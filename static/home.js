let ongoingStream = null;
const responses = []; // Store responses here
let idCounter = 0; // Unique ID counter for bot messages

function createNewChat() {
    const chatHistoryList = document.querySelector('.chat-history-list');
    const newChatEntry = document.createElement('li');
    newChatEntry.classList.add('list-item-styles', 'cursor-pointer');

    const anchor = document.createElement('a');
    anchor.classList.add("group", "relative", "flex", "items-center", "gap-2.5", "rounded-sm", "px-4", "py-2", "font-medium", "text-bodydark1", "duration-300", "ease-in-out", "hover:bg-graydark", "dark:hover:bg-meta-4");
    anchor.innerHTML = `
            <svg class="fill-current" fill="none" height="18" viewBox="0 0 18 18" width="18" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 4.5C9.82843 4.5 10.5 3.82843 10.5 3C10.5 2.17157 9.82843 1.5 9 1.5C8.17157 1.5 7.5 2.17157 7.5 3C7.5 3.82843 8.17157 4.5 9 4.5Z" fill=""></path>
                <path d="M13.5 9C13.5 12.5899 10.5899 15.5 7 15.5C3.41015 15.5 0.5 12.5899 0.5 9C0.5 5.41015 3.41015 2.5 7 2.5C10.5899 2.5 13.5 5.41015 13.5 9Z" fill=""></path>
                <path d="M17.5 17.5L13.5 13.5" stroke="" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg> New Chat`;

    newChatEntry.appendChild(anchor);
    chatHistoryList.children.item(0).appendChild(newChatEntry);

    anchor.addEventListener('click', () => {
        fetch(chat_form_url)
            .then(response => response.text())
            .then(data => {
                const contentBlock = document.querySelector('#main');
                contentBlock.innerHTML = data;
                const chat_id = contentBlock.children.item(0).id;
                initializeChat(chat_id);
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
            initializeChat(chatId);
            setupInfiniteScroll(chatId);
        })
        .catch(error => console.error(error));
}

function initializeChat(chatId) {
    scrollToBottom();

    const Form = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    const chatSocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/chat/' + chatId + '/'
    );
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        const chunk = JSON.parse(data.message);
        if (data.sender === 'llm' && chunk.event === 'on_parser_stream') {
            updateBotMessage(chunk.data.chunk, ongoingStream.id);
        } else if (data.sender === 'llm' && chunk.event === 'on_parser_start') {
            ongoingStream = appendBotMessage();
        }
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket closed unexpectedly');
    };

    Form.addEventListener('submit', (event) => {
        event.preventDefault();

        const message = chatInput.value.trim();
        if (message) {
            appendUserMessage(message, chatMessages);
            chatInput.value = '';

            chatSocket.send(JSON.stringify({
                'message': message,
                'sender': 'user'
            }));

            Form.classList.add('animate');
            setTimeout(() => {
                Form.classList.remove('animate');
            }, 500);
        }
    });


}

function setupInfiniteScroll(chatId) {
    const chatMessages = document.getElementById('chat-messages');
    let currentPage = 1;
    let loading = false;

    chatMessages.addEventListener('scroll', () => {
        if (chatMessages.scrollTop === 0 && !loading) {
            loadMoreMessages(chatId);
        }
    });

    function loadMoreMessages(chatId) {
        loading = true;
        const previousScrollHeight = chatMessages.scrollHeight;

        fetch(`/chat/api/messages/${chatId}/get?page=${currentPage}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.results && data.results.length > 0) {
                    const messages = data.results.reverse();
                    messages.forEach(message => {
                        if (message.sender === 'user') {
                            prependUserMessage(message.content, chatMessages);
                        } else {
                            const botMessageId = `bot-message-${idCounter++}`;
                            prependBotMessage(message.content, botMessageId, chatMessages);
                        }
                    });

                    // Adjust the scroll position after prepending messages
                    const newScrollHeight = chatMessages.scrollHeight;
                    chatMessages.scrollTop = newScrollHeight - previousScrollHeight + 50; // Adjust by 50 pixels

                    loading = false;
                    currentPage++;
                }
            })
            .catch(error => {
                console.error('Error loading more messages:', error);
                loading = false;
                // Handle error here, such as displaying a message to the user or retrying the request
            });
    }
}


function appendUserMessage(message, chatMessages) {
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
    scrollToBottom();
}

function appendBotMessage(message, botMessageId, chatMessages) {
    const botMessageContainer = document.createElement('div');
    botMessageContainer.id = botMessageId;
    botMessageContainer.classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4', 'chat-message');

    const botAvatar = document.createElement('img');
    botAvatar.classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
    botAvatar.src = bot_avatar_url;

    const botMessageContent = document.createElement('div');
    botMessageContent.classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

    const botMessage = document.createElement('p');
    botMessage.classList.add('bot-message-text');
    botMessage.textContent = message;

    botMessageContent.appendChild(botMessage);
    botMessageContainer.appendChild(botAvatar);
    botMessageContainer.appendChild(botMessageContent);
    chatMessages.appendChild(botMessageContainer);
    scrollToBottom();

    return {id: botMessageId};
}

function prependUserMessage(message, chatMessages) {
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

    // Prepend the message container to the chatMessages
    chatMessages.insertBefore(userMessageContainer, chatMessages.firstChild);
}

function prependBotMessage(message, botMessageId, chatMessages) {
    const botMessageContainer = document.createElement('div');
    botMessageContainer.id = botMessageId;
    botMessageContainer.classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4', 'chat-message');

    const botAvatar = document.createElement('img');
    botAvatar.classList.add('mr-2', 'flex', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
    botAvatar.src = bot_avatar_url;

    const botMessageContent = document.createElement('div');
    botMessageContent.classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

    const botMessage = document.createElement('p');
    botMessage.classList.add('bot-message-text');
    botMessage.textContent = message;

    botMessageContent.appendChild(botMessage);
    botMessageContainer.appendChild(botAvatar);
    botMessageContainer.appendChild(botMessageContent);

    // Prepend the message container to the chatMessages
    chatMessages.insertBefore(botMessageContainer, chatMessages.firstChild);

    return {id: botMessageId};
}

function updateBotMessage(chunk, botMessageId) {
    const botMessageContainer = document.getElementById(botMessageId);
    const botMessageText = botMessageContainer.querySelector('.bot-message-text');

    if (botMessageText) {
        botMessageText.innerHTML += chunk;
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

let chat_page=1
function loadMoreChats() {


    const url = `${api_chat_pagination}?page=${chat_page++}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const chatHistoryList = document.querySelector('.chat-history-list');
            data.results.forEach(chat => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <a href="#" @click.prevent="selectedChat = ${chat.id}; chat_messages(${chat.id})"
                       :class="{ 'bg-blue-500 text-white': selectedChat === ${chat.id} }"
                       class="group relative flex items-center gap-2.5 rounded-sm px-4 py-2 font-medium text-bodydark1 duration-300 ease-in-out hover:bg-graydark dark:hover:bg-meta-4">
                        <svg class="fill-current" fill="none" height="18" viewBox="0 0 18 18" width="18" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 4.5C9.82843 4.5 10.5 3.82843 10.5 3C10.5 2.17157 9.82843 1.5 9 1.5C8.17157 1.5 7.5 2.17157 7.5 3C7.5 3.82843 8.17157 4.5 9 4.5Z" fill=""/>
                            <path d="M13.5 9C13.5 12.5899 10.5899 15.5 7 15.5C3.41015 15.5 0.5 12.5899 0.5 9C0.5 5.41015 3.41015 2.5 7 2.5C10.5899 2.5 13.5 5.41015 13.5 9Z" fill=""/>
                            <path d="M17.5 17.5L13.5 13.5" stroke="" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        chat_#${chat.id}
                    </a>
                `;
                chatHistoryList.insertBefore(li, chatHistoryList.lastElementChild);
            });
            this.page++;
        })
        .catch(error => console.error('Error loading more chats:', error));
}
