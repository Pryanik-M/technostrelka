// Добавление кнопок под сообщения ассистента
document.querySelectorAll('.assistant-message').forEach(message => {
    const messageId = message.dataset.messageId;
    const likeContainer = document.querySelector(`#like-container-${messageId}`); // Ищем вне сообщения

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

    // Обработчики для кнопок
    const likeBtn = likeContainer.querySelector('.like-btn');
    const refreshBtn = likeContainer.querySelector('.refresh-btn');
    const copyBtn = likeContainer.querySelector('.copy-btn');

    likeBtn.addEventListener('click', function() {
        const messageId = this.dataset.messageId;
        fetch(`/favorite/${messageId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
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
        // Здесь можно добавить логику перегенерации ответа
        alert(`Перегенерация сообщения ${messageId}`);
    });

    copyBtn.addEventListener('click', function() {
        const messageContent = message.previousElementSibling.querySelector('.message-content').textContent; // Ищем контент в предыдущем элементе
        navigator.clipboard.writeText(messageContent).then(() => {
            alert('Сообщение скопировано!');
        });
    });
});