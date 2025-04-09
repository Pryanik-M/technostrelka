document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');

    const container = document.getElementById('container');
    const showLoginBtn = document.getElementById('show-login-form');
    const showRegisterBtn = document.getElementById('show-register-form');
    const signUpForm = document.querySelector('.sign-up');
    const signInForm = document.querySelector('.sign-in');

    // Функция для обновления состояния контейнера
    function updateContainerState(activeForm) {
        if (activeForm === 'login') {
            container.classList.add('right-panel');
            signUpForm.classList.remove('active');
            signInForm.classList.add('active');
        } else {
            container.classList.remove('right-panel');
            signInForm.classList.remove('active');
            signUpForm.classList.add('active');
        }
    }

    // Инициализация состояния из серверной переменной
    const hidden_active_form = document.getElementById('hidden_active_form');
    const activeForm = hidden_active_form.value || 'register'; // Значение по умолчанию
    updateContainerState(activeForm);

    if (showLoginBtn) {
        showLoginBtn.addEventListener('click', function(e) {
            e.preventDefault();

            // Проверяем заполнение полей в форме регистрации
            const registerName = document.getElementById('register-name');
            const registerEmail = document.getElementById('register-email');
            const registerPassword = document.getElementById('register-password');
            const registerConfirm = document.getElementById('register-confirm');
            let isRegisterFormFilled = false;

            if (registerName && registerName.value.trim() !== '') isRegisterFormFilled = true;
            if (registerEmail && registerEmail.value.trim() !== '') isRegisterFormFilled = true;
            if (registerPassword && registerPassword.value.trim() !== '') isRegisterFormFilled = true;
            if (registerConfirm && registerConfirm.value.trim() !== '') isRegisterFormFilled = true;
            
            if (isRegisterFormFilled) {
                if (!confirm('Вы заполнили поля формы регистрации. Переключиться на вход? Все введенные данные будут потеряны.')) {
                    return;
                }
            }
            
            console.log('Switch to login');
            updateContainerState('login');
        });
    }

    if (showRegisterBtn) {
        showRegisterBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Проверяем заполнение полей в форме входа
            const loginEmail = document.getElementById('login-email');
            const loginPassword = document.getElementById('login-password');
            let isLoginFormFilled = false;

            if (loginEmail && loginEmail.value.trim() !== '') isLoginFormFilled = true;
            if (loginPassword && loginPassword.value.trim() !== '') isLoginFormFilled = true;
            
            if (isLoginFormFilled) {
                if (!confirm('Вы заполнили поля формы входа. Переключиться на регистрацию? Все введенные данные будут потеряны.')) {
                    return;
                }
            }
            
            console.log('Switch to register');
            updateContainerState('register');
        });
    }

    // Обработка ошибок ввода
    document.querySelectorAll('input').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('input-error');
            const errorElement = this.closest('form').querySelector('.error-message');
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        });
    });
});