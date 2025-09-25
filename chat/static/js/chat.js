document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messagesContainer = document.getElementById('messages-container');
    let isSending = false;

    function sendMessage() {
        if (isSending) return;
        
        const message = messageInput.value.trim();
        if (message) {
            isSending = true;
            sendButton.disabled = true;
            
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    room_link: roomLink,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messageInput.value = '';
                } else {
                    console.error('Ошибка отправки:', data.error);
                    alert('Ошибка отправки сообщения: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Ошибка сети при отправке сообщения');
            })
            .finally(() => {
                isSending = false;
                sendButton.disabled = false;
            });
        }
    }

    function getNewMessages() {
        fetch(`/get_messages/${roomLink}?last_id=${lastMessageId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        addMessageToChat(msg);
                        lastMessageId = Math.max(lastMessageId, msg.id);
                    });
                    scrollToBottom();
                }
            })
            .catch(error => {
                console.error('Ошибка получения сообщений:', error);
            });
    }

    function addMessageToChat(message) {
        const existingMessage = document.querySelector(`.message[data-id="${message.id}"]`);
        if (existingMessage) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.setAttribute('data-id', message.id);
        
        const usernameSpan = document.createElement('span');
        usernameSpan.className = 'username';
        usernameSpan.textContent = message.username + ':';
        
        const textSpan = document.createElement('span');
        textSpan.className = 'text';
        textSpan.innerHTML = message.message;
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'timestamp';
        timeSpan.textContent = new Date(message.timestamp).toLocaleTimeString();
        
        messageDiv.appendChild(usernameSpan);
        messageDiv.appendChild(textSpan);
        messageDiv.appendChild(timeSpan);
        
        messagesContainer.appendChild(messageDiv);
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    setInterval(getNewMessages, 1000);
    scrollToBottom();
});