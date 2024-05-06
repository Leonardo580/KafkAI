function createNewChat() {
    const chatHistoryList = document.querySelector('.chat-history-list');
    const newChatEntry = document.createElement('li');
    newChatEntry.classList.add('list-item-styles');
    const anchor = document.createElement('a');
    anchor.classList.add("group", "relative", "flex", "items-center", "gap-2.5", "rounded-sm", "px-4", "py-2", "font-medium", "text-bodydark1", "duration-300", "ease-in-out", "hover:bg-graydark", "dark:hover:bg-meta-4");
    anchor.textContent = 'New Chat';
    newChatEntry.appendChild(anchor);
    chatHistoryList.appendChild(newChatEntry);

    anchor.addEventListener('click', () => {
        fetch(chat_form_url)
            .then(response => response.text())
            .then(data => {
                const contentBlock = document.querySelector('#main');
                contentBlock.innerHTML = data;
                const chat_id = contentBlock.children.item(0).id;

                // Get the necessary elements
                const Form = document.getElementById('chat-form');
                const chatInput = document.getElementById('chat-input');
                const chatMessages = document.getElementById('chat-messages');

                // Create a WebSocket connection
                const chatSocket = new WebSocket(
                    'ws://' + window.location.host +
                    '/ws/chat/' + chat_id + '/'
                );

                // Function to send a message
                function sendMessage(event) {
                    event.preventDefault(); // Prevent the default form submission behavior

                    const message = chatInput.value.trim(); // Get the user's message

                    if (message) {
                        // Create user message component
                        const userMessageContainer = document.createElement('div');
                        userMessageContainer.classList.add('flex', 'flex-row', 'px-2', 'py-4', 'sm:px-4');

                        const userAvatar = document.createElement('img');
                        userAvatar.classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
                        userAvatar.src = avatar_url;

                        const userMessageContent = document.createElement('div');
                        userMessageContent.classList.add('flex', 'max-w-3xl', 'items-center');

                        const userMessage = document.createElement('p');
                        userMessage.textContent = message;

                        userMessageContent.appendChild(userMessage);
                        userMessageContainer.appendChild(userAvatar);
                        userMessageContainer.appendChild(userMessageContent);
                        chatMessages.appendChild(userMessageContainer);

                        // Clear the input field
                        chatInput.value = '';

                        // Send the message to the server via WebSocket
                        chatSocket.send(JSON.stringify({
                            'message': message,
                            "sender": "user"
                        }));
                    }
                }

                // Handle the WebSocket response
                chatSocket.onmessage = function (e) {

                    const data = JSON.parse(e.data);

                    const chunk = data.chunk;

                    // Create a new bot message container for each message received
                    const botMessageContainer = document.createElement('div');
                    botMessageContainer.classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4');

                    const botAvatar = document.createElement('img');
                    botAvatar.classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
                    botAvatar.src = bot_avatar_url;

                    const botMessageContent = document.createElement('div');
                    botMessageContent.classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

                    const botMessage = document.createElement('p');
                    botMessage.textContent = chunk;

                    botMessageContent.appendChild(botMessage);
                    botMessageContainer.appendChild(botAvatar);
                    botMessageContainer.appendChild(botMessageContent);
                    chatMessages.appendChild(botMessageContainer);
                };

                // Attach the sendMessage function to the form's submit event
                Form.addEventListener('submit', sendMessage);
            })
            .catch(error => console.error(error));
    });
}

function chat_messages(chatId) {
    fetch(`/chat/api/${chatId}/`)
        .then(response => response.text())
        .then(data => {
            const contentBlock = document.querySelector('#main');
            contentBlock.innerHTML = data;

            // Get the necessary elements
            const Form = document.getElementById('chat-form');
            const chatInput = document.getElementById('chat-input');
            const chatMessages = document.getElementById('chat-messages');
            // Create a WebSocket connection
            const chatSocket = new WebSocket(
                'ws://' + window.location.host +
                '/ws/chat/' + chatId + '/'
            );

            // Function to send a message
            function sendMessage(event) {

                event.preventDefault(); // Prevent the default form submission behavior

                const message = chatInput.value.trim(); // Get the user's message

                if (message) {
                    // Create user message component
                    const userMessageContainer = document.createElement('div');
                    userMessageContainer.classList.add('flex', 'flex-row', 'px-2', 'py-4', 'sm:px-4');

                    const userAvatar = document.createElement('img');
                    userAvatar.classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
                    userAvatar.src = avatar_url;

                    const userMessageContent = document.createElement('div');
                    userMessageContent.classList.add('flex', 'max-w-3xl', 'items-center');

                    const userMessage = document.createElement('p');
                    userMessage.textContent = message;

                    userMessageContent.appendChild(userMessage);
                    userMessageContainer.appendChild(userAvatar);
                    userMessageContainer.appendChild(userMessageContent);
                    chatMessages.appendChild(userMessageContainer);

                    // Clear the input field
                    chatInput.value = '';

                    // Send the message to the server via WebSocket
                    chatSocket.send(JSON.stringify({
                        'message': message,
                        'sender': 'user'
                    }));
                }
            }

            // Handle the WebSocket response
            chatSocket.onmessage = function (e) {
                console.log(e);
                const data = JSON.parse(e.data);
                const chunk = data["message"];
                // Create a new bot message container for each message received
                const botMessageContainer = document.createElement('div');
                botMessageContainer.classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4');

                const botAvatar = document.createElement('img');
                botAvatar.classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
                botAvatar.src = bot_avatar_url;

                const botMessageContent = document.createElement('div');
                botMessageContent.classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

                const botMessage = document.createElement('p');
                botMessage.textContent = chunk;

                botMessageContent.appendChild(botMessage);
                botMessageContainer.appendChild(botAvatar);
                botMessageContainer.appendChild(botMessageContent);
                chatMessages.appendChild(botMessageContainer);

            };

            // Attach the sendMessage function to the form's submit event
            Form.addEventListener('submit', sendMessage);
        })
        .catch(error => console.error(error));
}