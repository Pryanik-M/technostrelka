document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chatContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const helpBtn = document.querySelector('.help-input-btn');
    const helpModal = document.getElementById('helpModal');
    const closeHelpBtn = document.getElementById('closeHelpBtn');
    const attachBtn = document.querySelector('.attach-btn');
    const fileInput = document.getElementById('fileInput');

    // Автоматическое увеличение высоты textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Отправка сообщения по Enter
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Обработчик клика по кнопке отправки
    sendBtn.addEventListener('click', sendMessage);

    function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        const chatId = document.querySelector('input[name="chat_id"]').value;

        fetch('/main', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `chat_id=${encodeURIComponent(chatId)}&message=${encodeURIComponent(messageText)}`
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        })
        .catch(error => console.error('Error:', error));

        userInput.value = '';
        userInput.style.height = 'auto';
    }

    // Добавление кнопок под сообщения ассистента
    document.querySelectorAll('.assistant-message').forEach(message => {
        const messageId = message.dataset.messageId;
        const likeContainer = document.getElementById(`like-container-${messageId}`);

        likeContainer.innerHTML = `
            <button class="like-btn" data-message-id="${messageId}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M7 22H4C3.46957 22 2.96086 21.7893 2.58579 21.4142C2.21071 21.0391 2 20.5304 2 20V13C2 12.4696 2.21071 11.9609 2.58579 11.5858C2.96086 11.2107 3.46957 11 4 11H7M14 9V5C14 4.20435 13.6839 3.44129 13.1213 2.87868C12.5587 2.31607 11.7956 2 11 2L7 11V22H18.28C18.7623 22.0055 19.2304 21.8364 19.5979 21.524C19.9654 21.2116 20.2077 20.7769 20.28 20.3L21.66 11.3C21.7035 11.0134 21.6842 10.7207 21.6033 10.4423C21.5225 10.1638 21.3821 9.90629 21.1919 9.68751C21.0016 9.46873 20.7661 9.29393 20.5016 9.17522C20.2371 9.0565 19.9499 8.99672 19.66 9H14Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <button class="refresh-btn" data-message-id="${messageId}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 8C18.5347 5.61082 16.1375 4 13.5 4C9.08172 4 5.5 7.58172 5.5 12C5.5 16.4183 9.08172 20 13.5 20C17.2279 20 20.3797 17.4507 21.0018 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M18 9L21 6L23 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <button class="copy-btn" data-message-id="${messageId}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 4V16C8 17.1046 8.89543 18 10 18H18C19.1046 18 20 17.1046 20 16V7.5C20 6.67157 19.3284 6 18.5 6H16C14.8954 6 14 5.10457 14 4V4C14 2.89543 13.1046 2 12 2H6C4.89543 2 4 2.89543 4 4V14C4 15.1046 4.89543 16 6 16H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `;

        const likeBtn = likeContainer.querySelector('.like-btn');
        const refreshBtn = likeContainer.querySelector('.refresh-btn');
        const copyBtn = likeContainer.querySelector('.copy-btn');

        likeBtn.addEventListener('click', function() {
            const messageId = this.dataset.messageId;
            fetch(`/favorite/${messageId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.classList.toggle('active', data.action === 'added');
                }
            })
            .catch(error => console.error('Error:', error));
        });

        refreshBtn.addEventListener('click', function() {
            const messageId = this.dataset.messageId;
            alert(`Перегенерация сообщения ${messageId}`);
        });

        copyBtn.addEventListener('click', function() {
            const messageContent = message.querySelector('.message-content').textContent;
            navigator.clipboard.writeText(messageContent).then(() => {
                alert('Сообщение скопировано!');
            });
        });
    });

    // Обработка клика по элементу чата
    document.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', function(e) {
            if (e.target.classList.contains('edit-chat-btn') ||
                e.target.classList.contains('delete-chat-btn') ||
                e.target.tagName === 'SVG' ||
                e.target.tagName === 'PATH') {
                return;
            }
            const chatId = this.dataset.chatId;
            window.location.href = `/main?chat_id=${chatId}`;
        });
    });

    // Обработка редактирования чата
    document.querySelectorAll('.edit-chat-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            const currentTitle = this.parentElement.querySelector('.chat-title').textContent;
            const newTitle = prompt('Введите новое название чата:', currentTitle);

            if (newTitle && newTitle !== currentTitle) {
                fetch(`/edit_chat/${chatId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `title=${encodeURIComponent(newTitle)}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.parentElement.querySelector('.chat-title').textContent = data.chat_title;
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Обработка удаления чата
    document.querySelectorAll('.delete-chat-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            if (confirm('Вы уверены, что хотите удалить этот чат?')) {
                fetch(`/delete_chat/${chatId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.parentElement.remove();
                        if (window.location.search.includes(`chat_id=${chatId}`)) {
                            window.location.href = '/main';
                        }
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Показать модальное окно "Новый чат"
    document.querySelector('.new-chat-btn').addEventListener('click', function() {
        document.getElementById('newChatModal').style.display = 'flex';
    });

    // Закрыть модальное окно "Новый чат" при клике на "Отмена"
    document.getElementById('cancelChatBtn').addEventListener('click', function() {
        document.getElementById('newChatModal').style.display = 'none';
        document.getElementById('newChatTitle').value = '';
    });

    // Создать новый чат
    document.getElementById('createChatBtn').addEventListener('click', function() {
        const title = document.getElementById('newChatTitle').value;

        fetch('/new_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'title=' + encodeURIComponent(title)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const historyList = document.querySelector('.history-list');
                const newItem = document.createElement('li');
                newItem.className = 'history-item';
                newItem.dataset.chatId = data.chat_id;
                newItem.innerHTML = `
                    <span class="chat-title">${data.chat_title}</span>
                    <button class="edit-chat-btn" data-chat-id="${data.chat_id}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    </button>
                    <button class="delete-chat-btn" data-chat-id="${data.chat_id}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                    </button>
                `;
                historyList.insertBefore(newItem, historyList.firstChild);
                document.getElementById('newChatModal').style.display = 'none';
                document.getElementById('newChatTitle').value = '';
                window.location.href = '/main?chat_id=' + data.chat_id;
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Закрытие модального окна "Новый чат" при клике вне его
    document.getElementById('newChatModal').addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
            document.getElementById('newChatTitle').value = '';
        }
    });

    // Открытие модального окна "Помощь"
    helpBtn.addEventListener('click', function() {
        helpModal.style.display = 'flex';
    });

    // Закрытие модального окна "Помощь" кнопкой
    closeHelpBtn.addEventListener('click', function() {
        helpModal.style.display = 'none';
    });

    // Закрытие модального окна "Помощь" при клике вне его
    helpModal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
        }
    });

    // Обработка выбора файла
    attachBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file && file.name.endsWith('.txt')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                userInput.value = e.target.result;
            };
            reader.readAsText(file);
        }
    });
});