function createNewChat() {
    const chatHistoryList = document.querySelector('.chat-history-list');
    const newChatEntry = document.createElement('li');
    newChatEntry.classList.add('list-item-styles');
    const anchor = document.createElement('a');
    anchor.classList.add("group", "relative", "flex", "items-center", "gap-2.5", "rounded-sm", "px-4", "py-2", "font-medium", "text-bodydark1", "duration-300", "ease-in-out", "hover:bg-graydark", "dark:hover:bg-meta-4");
    newChatEntry.classList.add("cursor-pointer")
    anchor.innerHTML = "<svg class=\"fill-current\" fill=\"none\" height=\"18\" viewBox=\"0 0 18 18\" width=\"18\" xmlns=\"http://www.w3.org/2000/svg\">\n" +
        "                    <path d=\"M9 4.5C9.82843 4.5 10.5 3.82843 10.5 3C10.5 2.17157 9.82843 1.5 9 1.5C8.17157 1.5 7.5 2.17157 7.5 3C7.5 3.82843 8.17157 4.5 9 4.5Z\" fill=\"\"></path>\n" +
        "                    <path d=\"M13.5 9C13.5 12.5899 10.5899 15.5 7 15.5C3.41015 15.5 0.5 12.5899 0.5 9C0.5 5.41015 3.41015 2.5 7 2.5C10.5899 2.5 13.5 5.41015 13.5 9Z\" fill=\"\"></path>\n" +
        "                    <path d=\"M17.5 17.5L13.5 13.5\" stroke=\"\" stroke-linecap=\"round\" stroke-linejoin=\"round\"></path>\n" +
        "                </svg> New Chat"
    newChatEntry.appendChild(anchor);
    chatHistoryList.children.item(0).appendChild(newChatEntry);

    anchor.addEventListener('click', () => {
        fetch(chat_form_url)
            .then(response => response.text())
            .then(data => {
                const contentBlock = document.querySelector('#main');
                contentBlock.innerHTML = data;
                const chat_id = contentBlock.children.item(0).id;
                scrollToBottom();
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
                        userMessageContainer.classList.add('flex', 'flex-row', 'px-2', 'py-4', 'sm:px-4', 'chat-message');

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

                        // Add the animation class to the chat form
                        Form.classList.add('animate');

                        // Remove the animation class after the animation completes
                        setTimeout(() => {
                            Form.classList.remove('animate');
                        }, 500); // 500ms is the duration of the animation
                    }
                }

                // Handle the WebSocket response
                chatSocket.onmessage = function (e) {
                    const data = JSON.parse(e.data);
                    const chunk = data["message"];
                    // Create a new bot message container for each message received
                    const spacing = document.createElement('div');
                    spacing
                        .innerHTML = "<div class=\"mb-2 flex w-full flex-row justify-end gap-x-2 text-slate-500\">\n" +
                        "                <button class=\"hover:text-blue-600\" @click=\"copyToClipboard('" + chunk + "')\">\n" +
                        "                    <svg xmlns=\"http://www.w3.org/2000/svg\" class=\"h-5 w-5\" viewBox=\"0 0 24 24\" stroke-width=\"2\" stroke=\"currentColor\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\" data-darkreader-inline-stroke=\"\" style=\"--darkreader-inline-stroke: currentColor;\">\n" +
                        "                        <path stroke=\"none\" d=\"M0 0h24v24H0z\" fill=\"none\" data-darkreader-inline-stroke=\"\" style=\"--darkreader-inline-stroke: none;\"></path>\n" +
                        "                        <path d=\"M8 8m0 2a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2z\"></path>\n" +
                        "                        <path d=\"M16 8v-2a2 2 0 0 0 -2 -2h-8a2 2 0 0 0 -2 2v8a2 2 0 0 0 2 2h2\"></path>\n" +
                        "                    </svg>\n" +
                        "                </button>\n" +
                        "                <!-- Add other buttons here if needed -->\n" +
                        "            </div>";
                    const botMessageContainer = document.createElement('div');
                    botMessageContainer
                        .classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4', 'chat-message');

                    const botAvatar = document.createElement('img');
                    botAvatar
                        .classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
                    botAvatar
                        .src = bot_avatar_url;

                    const botMessageContent = document.createElement('div');
                    botMessageContent
                        .classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

                    const botMessage = document.createElement('p');
                    botMessage
                        .textContent = chunk;

                    botMessageContent
                        .appendChild(botMessage);
                    botMessageContainer
                        .appendChild(botAvatar);
                    botMessageContainer
                        .appendChild(botMessageContent);
                    chatMessages
                        .appendChild(spacing);
                    chatMessages
                        .appendChild(botMessageContainer);
                    scrollToBottom();
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
            scrollToBottom();
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
                    userMessageContainer.classList.add('flex', 'flex-row', 'px-2', 'py-4', 'sm:px-4', 'chat-message');

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

                    // Add the animation class to the chat form
                    Form.classList.add('animate');

                    // Remove the animation class after the animation completes
                    setTimeout(() => {
                        Form.classList.remove('animate');
                    }, 500); // 500ms is the duration of the animation
                }
            }

            // Handle the WebSocket response
            chatSocket.onmessage = function (e) {
                const data = JSON.parse(e.data);
                const chunk = data["message"];
                // Create a new bot message container for each message received
                const spacing = document.createElement('div');
                spacing
                    .innerHTML = "<div class=\"mb-2 flex w-full flex-row justify-end gap-x-2 text-slate-500\">\n" +
                    "                <button class=\"hover:text-blue-600\" @click=\"copyToClipboard('" + chunk + "')\">\n" +
                    "                    <svg xmlns=\"http://www.w3.org/2000/svg\" class=\"h-5 w-5\" viewBox=\"0 0 24 24\" stroke-width=\"2\" stroke=\"currentColor\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\" data-darkreader-inline-stroke=\"\" style=\"--darkreader-inline-stroke: currentColor;\">\n" +
                    "                        <path stroke=\"none\" d=\"M0 0h24v24H0z\" fill=\"none\" data-darkreader-inline-stroke=\"\" style=\"--darkreader-inline-stroke: none;\"></path>\n" +
                    "                        <path d=\"M8 8m0 2a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2z\"></path>\n" +
                    "                        <path d=\"M16 8v-2a2 2 0 0 0 -2 -2h-8a2 2 0 0 0 -2 2v8a2 2 0 0 0 2 2h2\"></path>\n" +
                    "                    </svg>\n" +
                    "                </button>\n" +
                    "                <!-- Add other buttons here if needed -->\n" +
                    "            </div>";
                const botMessageContainer = document.createElement('div');
                botMessageContainer
                    .classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4', 'chat-message');

                const botAvatar = document.createElement('img');
                botAvatar
                    .classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
                botAvatar
                    .src = bot_avatar_url;

                const botMessageContent = document.createElement('div');
                botMessageContent
                    .classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

                const botMessage = document.createElement('p');
                botMessage
                    .textContent = chunk;

                botMessageContent
                    .appendChild(botMessage);
                botMessageContainer
                    .appendChild(botAvatar);
                botMessageContainer
                    .appendChild(botMessageContent);
                chatMessages
                    .appendChild(spacing);
                chatMessages
                    .appendChild(botMessageContainer);
                scrollToBottom();
            };

            // Attach the sendMessage function to the form's submit event
            Form.addEventListener('submit', sendMessage);
        })
        .catch(error => console.error(error));
}

function copyToClipboard(data) {
    navigator.clipboard.writeText(data);
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}