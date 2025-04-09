from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime
from random import randint

app = Flask(__name__, static_folder='static')

app.config['SECRET_KEY'] = 'hardsecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbase.db'
db = SQLAlchemy(app)

IMAGES_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = IMAGES_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

CODE = 0


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(256))  # Увеличиваем длину для хранения хэша
    name = db.Column(db.String(100))

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    content = db.Column(db.Text)
    is_user = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    term = db.Column(db.String(100), unique=True)  # Уникальные термины
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


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
    else:
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
            message = (f'''Здравствуйте!
            Вы получили это письмо, потому что мы получили запрос на подтверждения почты для вашей учетной записи.
            Специальный код: {CODE}
            Если вы не запрашивали код, никаких дальнейших действий не требуется.

            С Уважением,
            команда "Вот они слева направо".''')
            send_email(message=message, adress=email)
            return render_template('check_email.html', flag=True, err="Код отправлен", email=email)
        else:
            if int(unic_code) == CODE:
                if reset == 0:
                    CODE = 0
                    session['email'] = email
                    new_user = User(
                        name=name,
                        email=email,
                        password=generate_password_hash(password)
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user)
                    return redirect(url_for('index'))
                elif reset == 1:
                    return redirect(url_for('new_password', email=email))
    else:
        return render_template('check_email.html', flag=False, err="", email=email)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
                return render_template('entrance.html',
                                       register_errors=errors,
                                       name=name,
                                       email=email,
                                       password=password,
                                       confirm_password=confirm_password,
                                       active_form='register')  # Остаёмся на регистрации
            return redirect(url_for('send', name=name, email=email, password=password, reset=0))
        elif form_type == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            user = User.query.filter_by(email=email).first()
            if not check_password_hash(user.password, password):
                return render_template('entrance.html',
                                       login_errors=["Неверный email или пароль"],
                                       login_email=email,
                                       login_password=password,
                                       active_form='login')  # Добавлено active_form='login'
            elif not user:
                return render_template('entrance.html',
                                       login_errors=["Неверный email или пароль"],
                                       login_email=email,
                                       login_password=password,
                                       active_form='login')  # Добавлено active_form='login'
            login_user(user, remember=remember)
            return redirect(url_for('index'))
    return render_template('entrance.html', active_form='register')  # По умолчанию регистрация


@app.route('/main', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        chat_id = request.form.get('chat_id')

        # Проверяем, есть ли загруженный файл
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

        # Сохраняем сообщение пользователя
        user_message = Message(
            chat_id=int(chat_id),
            content=message_content,
            is_user=True,
            timestamp=datetime.datetime.utcnow()
        )
        db.session.add(user_message)

        # Добавляем термины из сообщения пользователя
        words = [word for word in message_content.split() if len(word) > 3]
        for word in words:
            if not Term.query.filter_by(user_id=current_user.id, term=word).first():
                new_term = Term(user_id=current_user.id, term=word)
                db.session.add(new_term)

        # Автоматический ответ ИИ
        ai_message = Message(
            chat_id=int(chat_id),
            content="Это автоматический ответ ИИ. Здесь будет реальный ответ от вашего ИИ.",
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

    return render_template('index.html',
                           chats=user_chats,
                           messages=messages,
                           current_chat_id=chat_id)

@app.route('/favorite/<int:message_id>', methods=['POST'])
@login_required
def add_to_favorite(message_id):
    message = Message.query.get_or_404(message_id)
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

    # Удаляем все сообщения чата
    Message.query.filter_by(chat_id=chat_id).delete()
    # Удаляем сам чат
    db.session.delete(chat)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/profile')
def profile():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_messages = [Message.query.get(fav.message_id) for fav in favorites]
    terms = Term.query.filter_by(user_id=current_user.id).order_by(Term.created_at.desc()).all()
    return render_template('profile.html',
                         name=current_user.name,
                         email=current_user.email,
                         image='static/image/profile_rev.png',
                         favorite_messages=favorite_messages,
                         terms=terms)

@app.route('/edit_name', methods=['POST'])
@login_required
def edit_name():
    new_name = request.form.get('new_name')
    if not new_name:
        return redirect(url_for('profile'))  # Можно добавить сообщение об ошибке
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