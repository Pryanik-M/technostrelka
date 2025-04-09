from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from random import randint
from transformers import AutoModelForSeq2SeqLM, T5TokenizerFast, T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer
import torch
import os
import nltk
import re
from nltk.tokenize import word_tokenize
import number_converter


app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'hardsecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbase.db'
app.config['TEMPLATES_AUTO_RELOAD'] = True
db = SQLAlchemy(app)

IMAGES_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = IMAGES_FOLDER

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

CODE = 0
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(256))
    name = db.Column(db.String(100))


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    content = db.Column(db.Text)
    is_user = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    term = db.Column(db.String(100))  # Убираем unique=True
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    __table_args__ = (db.UniqueConstraint('user_id', 'term', name='unique_user_term'),)


with app.app_context():
    db.create_all()


def send_email(message, adress):
    sender = "gulovskiu@gmail.com"
    password = "nwjcfhzloyluetwv"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    try:
        server.login(sender, password)
        msg = MIMEText(message)
        msg["Subject"] = "Подтверждение почты"
        server.sendmail(sender, adress, msg.as_string())
        return "The message was sent successfully!"
    except Exception as _ex:
        return f"{_ex}\nCheck your login or password please!"


def correct_spelling(text, max_length=4000):
    MODEL_NAME = 'UrukHan/t5-russian-spell'
    tokenizer = T5TokenizerFast.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    task_prefix = "Spell correct: "
    input_sequences = [text] if type(text) is not list else text

    encoded = tokenizer(
        [task_prefix + sequence for sequence in input_sequences],
        padding="longest",
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    predicts = model.generate(**encoded.to(device), max_length=max_length)
    results = tokenizer.batch_decode(predicts, skip_special_tokens=True)
    return results[0] if isinstance(text, str) else results


def load_headliner():
    tokenizer = AutoTokenizer.from_pretrained("IlyaGusev/rut5_base_sum_gazeta", legacy=True)
    model = AutoModelForSeq2SeqLM.from_pretrained("IlyaGusev/rut5_base_sum_gazeta").to(device)
    return model, tokenizer


def generate_headline_fixed_length(text, model, tokenizer, target_words=8):
    input_ids = tokenizer(
        "Составь заголовок: " + text,
        return_tensors="pt",
        max_length=1000,
        truncation=True
    ).input_ids.to(device)

    output_ids = model.generate(
        input_ids=input_ids,
        max_length=30,
        min_length=10,
        num_beams=4,
        repetition_penalty=2.5,
        length_penalty=0.5,
        early_stopping=True
    )

    headline = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    words = word_tokenize(headline, language="russian")

    if len(words) > target_words:
        words = words[:target_words]
        while words and not words[-1].isalnum():
            words.pop()
    headline = ' '.join(words).rstrip('.,')

    return headline.strip().capitalize()


def load_paraphraser():
    MODEL_PATH = "cointegrated/rut5-base-paraphraser"
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    try:
        tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH, legacy=True)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH).to(DEVICE)
        return model, tokenizer
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        exit()


def paraphrase_text(text, model, tokenizer, max_length=4000):
    prompt = text
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=max_length,
        truncation=True,
        padding=True
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=max_length,
            num_beams=5,
            do_sample=True,
            temperature=1.5,
            top_k=50,
            top_p=0.95,
            early_stopping=True
        )

    decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return clean_paraphrase_output(decoded_output)


def clean_paraphrase_output(text):
    text = re.sub(r'^(перефразируй:|перефразируя:|подробнее:|дополнительно:)\s*', '', text, flags=re.IGNORECASE)
    return text.strip()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/new_password', methods=['GET', 'POST'])
def new_password():
    email = request.args.get('email')
    if request.method == 'POST':
        psw1 = request.form['psw1']
        psw2 = request.form['psw2']
        if not psw1 or not psw2:
            return render_template('new_password.html', err='Заполните все поля', psw1=psw1, psw2=psw2)
        if len(psw1) < 8:
            return render_template('new_password.html', err='Пароль слишком маленький', psw1=psw1, psw2=psw2)
        if psw1 != psw2:
            return render_template('new_password.html', err='Пароли различаются', psw1=psw1, psw2=psw2)
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(psw1)
            db.session.commit()
        return redirect(url_for('login'))
    return render_template('new_password.html', psw1='', psw2='')


@app.route('/send', methods=['GET', 'POST'])
def send():
    email = request.args.get('email')
    name = request.args.get('name')
    password = request.args.get('password')
    reset = int(request.args.get('reset'))
    if request.method == 'POST':
        global CODE
        email = request.form['mail']
        unic_code = request.form['unik_cod']
        if email == '':
            return render_template('check_email.html', flag=False, err="Введите почту")
        if unic_code == '':
            CODE = randint(1000, 9999)
            message = f'''Здравствуйте!
            Вы получили это письмо, потому что мы получили запрос на подтверждения почты для вашей учетной записи.
            Специальный код: {CODE}
            Если вы не запрашивали код, никаких дальнейших действий не требуется.

            С Уважением,
            команда "Вот они слева направо".'''
            send_email(message=message, adress=email)
            return render_template('check_email.html', flag=True, err="Код отправлен", email=email)
        else:
            if int(unic_code) == CODE:
                if reset == 0:
                    CODE = 0
                    session['email'] = email
                    new_user = User(name=name, email=email, password=generate_password_hash(password))
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user)
                    return redirect(url_for('index'))
                elif reset == 1:
                    return redirect(url_for('new_password', email=email))
    return render_template('check_email.html', flag=False, err="", email=email)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'register':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            errors = []
            if not all([name, email, password, confirm_password]):
                errors.append("Все поля обязательны для заполнения")
            elif len(password) < 8:
                errors.append("Пароль должен содержать минимум 8 символов")
            elif password != confirm_password:
                errors.append("Пароли не совпадают")
            elif not email or '@' not in email:
                errors.append("Введите корректный email")
            elif User.query.filter_by(email=email).first():
                errors.append("Пользователь с таким email уже существует")
            if errors:
                return render_template('entrance.html', register_errors=errors, name=name,
                                       email=email, password=password, confirm_password=confirm_password,
                                       active_form='register')
            return redirect(url_for('send', name=name, email=email, password=password, reset=0))
        elif form_type == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            user = User.query.filter_by(email=email).first()
            if not check_password_hash(user.password, password):
                return render_template('entrance.html', login_errors=["Неверный email или пароль"],
                                       login_email=email,
                                       login_password=password,
                                       active_form='login')
            elif not user:
                return render_template('entrance.html', login_errors=["Неверный email или пароль"],
                                       login_email=email,
                                       login_password=password,
                                       active_form='login')
            login_user(user, remember=remember)
            return redirect(url_for('index'))
    return render_template('entrance.html', active_form='register')


@app.route('/main', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        chat_id = request.form.get('chat_id')

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and file.filename.endswith('.txt'):
                message_content = file.read().decode('utf-8').strip()
            else:
                message_content = request.form['message'].strip()
        else:
            message_content = request.form['message'].strip()

        if not message_content:
            return redirect(url_for('index', chat_id=chat_id))

        if chat_id == 'new':
            new_chat = Chat(user_id=current_user.id, title=f"Чат {datetime.datetime.now().strftime('%d.%m %H:%M')}")
            db.session.add(new_chat)
            db.session.commit()
            chat_id = new_chat.id

        user_message = Message(
            chat_id=int(chat_id),
            content=message_content,
            is_user=True,
            timestamp=datetime.datetime.utcnow()
        )
        db.session.add(user_message)

        waiting_message = Message(
            chat_id=int(chat_id),
            content="Ожидайте...",
            is_user=False,
            timestamp=datetime.datetime.utcnow()
        )
        db.session.add(waiting_message)
        db.session.commit()

        words = [word for word in message_content.split() if len(word) > 3]
        for word in words:
            if not Term.query.filter_by(user_id=current_user.id, term=word).first():
                new_term = Term(user_id=current_user.id, term=word)
                db.session.add(new_term)

        corrected_text = correct_spelling(message_content)
        paraphraser_model, paraphraser_tokenizer = load_paraphraser()
        paraphrased_text = paraphrase_text(corrected_text, paraphraser_model, paraphraser_tokenizer)
        model, tokenizer = load_headliner()
        headline = generate_headline_fixed_length(corrected_text, model, tokenizer, target_words=10)
        text = number_converter.replace_numbers_with_digits(paraphrased_text)[0]

        db.session.delete(waiting_message)

        ai_response = f'{headline}\n\n{text}'
        ai_message = Message(
            chat_id=int(chat_id),
            content=ai_response,
            is_user=False,
            timestamp=datetime.datetime.utcnow()
        )
        db.session.add(ai_message)
        db.session.commit()

        return redirect(url_for('index', chat_id=chat_id))

    chat_id = request.args.get('chat_id')
    user_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()

    if not chat_id and user_chats:
        chat_id = user_chats[0].id

    messages = []
    if chat_id:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()

    return render_template('index.html', chats=user_chats, messages=messages, current_chat_id=chat_id)


@app.route('/favorite/<int:message_id>', methods=['POST'])
@login_required
def add_to_favorite(message_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, message_id=message_id).first()
    if not favorite:
        new_favorite = Favorite(
            user_id=current_user.id,
            message_id=message_id
        )
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'added'})
    else:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})


@app.route('/new_chat', methods=['GET', 'POST'])
@login_required
def new_chat():
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            title = f"Чат {datetime.datetime.now().strftime('%d.%m %H:%M')}"
        new_chat = Chat(
            user_id=current_user.id,
            title=title
        )
        db.session.add(new_chat)
        db.session.commit()

        return jsonify({
            'success': True,
            'chat_id': new_chat.id,
            'chat_title': new_chat.title
        })

    return render_template('index.html')


@app.route('/edit_chat/<int:chat_id>', methods=['POST'])
@login_required
def edit_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    new_title = request.form.get('title')
    if new_title:
        chat.title = new_title
        db.session.commit()
        return jsonify({'success': True, 'chat_title': chat.title})
    return jsonify({'success': False, 'error': 'No title provided'}), 400


@app.route('/delete_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    Message.query.filter_by(chat_id=chat_id).delete()
    db.session.delete(chat)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/profile')
def profile():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_messages = [Message.query.get(fav.message_id) for fav in favorites]
    terms = Term.query.filter_by(user_id=current_user.id).order_by(Term.created_at.desc()).all()
    return render_template('profile.html', name=current_user.name, email=current_user.email,
                           image='static/image/profile_rev.png', favorite_messages=favorite_messages, terms=terms)


@app.route('/edit_name', methods=['POST'])
@login_required
def edit_name():
    new_name = request.form.get('new_name')
    if not new_name:
        return redirect(url_for('profile'))
    current_user.name = new_name
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/remove_favorite/<int:message_id>', methods=['POST'])
@login_required
def remove_favorite(message_id):
    favorite = Favorite.query.filter_by(user_id=current_user.id, message_id=message_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)