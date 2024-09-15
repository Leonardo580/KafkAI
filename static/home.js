let ongoingStream = null;
let currentStepElement = null; // Element to hold the current step message
let currentPage = 1;
let current_chunks = ""
const responses = []; // Store responses here
let idCounter = 0; // Unique ID counter for bot messages
let isWebSocketConnected = true; // Flag to track WebSocket connection status
const marked = window.marked;
let confirmButton, cancelButton;

const user_message = {
    "__start__": "processing...",
    "retrieve": "retrieving...",
    "grade_documents": "grading...",
    "generate": "generating...",
    "search": "searching...",
}

function createChatWithPipeline(pipelineId) {
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

    chatHistoryList.children.item(0).insertAdjacentElement("afterend", newChatEntry);
    fetch(`${chat_form_url}?pipeline_id=${pipelineId}`)
        .then(response => response.text())
        .then(data => {
            const contentBlock = document.querySelector('#main');
            contentBlock.innerHTML = data;
            const chat_id = contentBlock.children.item(0).id;
            anchor.setAttribute('x-bind:class', `{ 'bg-blue-500 text-white': selectedChat === ${chat_id} }`);
            anchor.setAttribute('x-on:click.prevent', `selectedChat = ${chat_id}; chat_messages(${chat_id})`);
            initializeChat(chat_id);
            anchor.addEventListener('click', () => {
                initializeChat(chat_id);
            });
        })
        .catch(error => console.error(error));
}

function createNewChat() {
    const pipelineModal = document.getElementById('pipeline-modal');
    pipelineModal.classList.remove('hidden');

    // Only set up event listeners if they haven't been set up before
    if (!confirmButton) {
        confirmButton = document.getElementById('confirm-pipeline');
        confirmButton.addEventListener('click', handleConfirm);
    }
    if (!cancelButton) {
        cancelButton = document.getElementById('cancel-pipeline');
        cancelButton.addEventListener('click', handleCancel);
    }
}

function handleConfirm() {
    const pipelineModal = document.getElementById('pipeline-modal');
    const selectedPipelineId = document.getElementById('pipeline-select').value;

    if (!selectedPipelineId || selectedPipelineId === 'undefined') {
        alert('Please select a a chat');
        return;
    }

    pipelineModal.classList.add('hidden');
    createChatWithPipeline(selectedPipelineId);
}
function handleCancel() {
    const pipelineModal = document.getElementById('pipeline-modal');
    pipelineModal.classList.add('hidden');
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
    currentPage = 1;
    const form = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatSocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/chat/' + chatId + '/'
    );

    // WebSocket connection open
    chatSocket.onopen = function (e) {
        isWebSocketConnected = true;
        updateSubmitButtonState();
    };

    // WebSocket message handling
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === 'progress') {
            updateSystemMessage(user_message[data.message], chatMessages);
        } else if (data.sender === 'llm') {
            console.log(data);
            const chunk = data.message;
            if (data.event === 'on_chat_model_stream') {
                removeLoadingWidget();
                currentStepElement.remove();
                updateBotMessage(current_chunks, chunk, ongoingStream.id, chatMessages);
                current_chunks += chunk;
                idCounter++;
            } else if (data.event === 'on_chat_model_start') {
                current_chunks = "";
                ongoingStream = appendBotMessage("", idCounter, chatMessages);
                removeLoadingWidget();
                currentStepElement.remove();
            }
        }
    };

    // WebSocket close handling
    chatSocket.onclose = function (e) {
        console.error('Chat socket closed unexpectedly');
        isWebSocketConnected = false;
        updateSubmitButtonState();
        removeLoadingWidget();
    };

    // Form submission handling
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        handleFormSubmit();
    });

    // Chat input keydown handling
    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleFormSubmit();
        }
    });

    function handleFormSubmit() {
        if (!isWebSocketConnected) {
            alert("WebSocket connection is not open. Please try again later.");
            return;
        }

        const message = chatInput.value.trim();
        if (message) {
            appendUserMessage(message, chatMessages);
            chatInput.value = '';

            showLoadingWidget(chatMessages);

            chatSocket.send(JSON.stringify({
                'message': message,
                'sender': 'user'
            }));

            form.classList.add('animate');
            setTimeout(() => {
                form.classList.remove('animate');
            }, 500);
        }
    }
}

// Update the submit button state based on WebSocket connection status
function updateSubmitButtonState() {
    const submitButton = document.querySelector('#chat-form button[type="submit"]');
    if (isWebSocketConnected) {
        submitButton.removeAttribute('disabled');
    } else {
        submitButton.setAttribute('disabled', 'disabled');
    }
}



function setupInfiniteScroll(chatId) {

    const chatMessages = document.getElementById('chat-messages');

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
    botMessageContainer.classList.add('message');
    botMessageContainer.dataset.content = message;

    // Copy button container
    const copyButtonContainer = document.createElement('div');
    copyButtonContainer.classList.add('mb-2', 'flex', 'w-full', 'flex-row', 'justify-end', 'gap-x-2', 'text-slate-500');

    // Copy button
    const copyButton = document.createElement('button');
    copyButton.classList.add('hover:text-blue-600');
    copyButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
            <path d="M8 8m0 2a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2z"></path>
            <path d="M16 8v-2a2 2 0 0 0 -2 -2h-8a2 2 0 0 0 -2 2v8a2 2 0 0 0 2 2h2"></path>
        </svg>
    `;
    copyButton.addEventListener('click', function (e) {
        e.preventDefault();
        navigator.clipboard.writeText(message);
    });

    copyButtonContainer.appendChild(copyButton);
    botMessageContainer.appendChild(copyButtonContainer);

    // Message content container
    const messageContentContainer = document.createElement('div');
    messageContentContainer.classList.add('mb-4', 'flex', 'rounded-xl', 'bg-slate-50', 'px-2', 'py-6', 'dark:bg-slate-900', 'sm:px-4');

    // Bot avatar
    const botAvatar = document.createElement('img');
    botAvatar.classList.add('mr-2', 'flex-shrink-0', 'h-8', 'w-8', 'rounded-full', 'sm:mr-4');
    botAvatar.src = bot_avatar_url;

    // Bot message content
    const botMessageContent = document.createElement('div');
    botMessageContent.classList.add('flex', 'max-w-3xl', 'items-center', 'rounded-xl');

    const botMessage = document.createElement('p');
    botMessage.classList.add('bot-message-text');
    botMessage.innerHTML = marked.parse(message);

    botMessageContent.appendChild(botMessage);
    messageContentContainer.appendChild(botAvatar);
    messageContentContainer.appendChild(botMessageContent);
    botMessageContainer.appendChild(messageContentContainer);

    chatMessages.appendChild(botMessageContainer);
    scrollToBottom();

    return {id: botMessageId};
}

function updateSystemMessage(message, chatMessages) {
    if (!currentStepElement) {
        currentStepElement = document.createElement('div');
        currentStepElement.classList.add('mb-4', 'flex', 'justify-center', 'px-2', 'py-6', 'text-gray-500', 'text-sm', 'chat-message');

        const systemMessage = document.createElement('p');
        systemMessage.textContent = message;
        currentStepElement.appendChild(systemMessage);

        chatMessages.appendChild(currentStepElement);
        scrollToBottom();
    } else {
        const systemMessage = currentStepElement.querySelector('p');
        systemMessage.textContent = message;
    }
}

function removeSystemMessage() {
    if (currentStepElement) {
        currentStepElement.remove();
        currentStepElement = null;
    }
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

function updateBotMessage(current_chucks, chunk, botMessageId) {
    const botMessageContainer = document.getElementById(botMessageId);
    const botMessageText = botMessageContainer.querySelector('.bot-message-text');

    if (botMessageText) {
        // Combine the current innerHTML with the new chunk
        const updatedContent = current_chucks + chunk;


        botMessageText.innerHTML = marked.parse(updatedContent);
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

let chat_page = 2;
let hasMoreChats = true;

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
            if (!data.next) {
                hasMoreChats = false;
                document.getElementById('load-more-button').disabled = true;
            }
        })
        .catch(error => {
            console.error('Error loading more chats:', error);
        });
}

function showLoadingWidget(chatMessages) {
    const loadingWidget = document.createElement('div');
    loadingWidget.id = 'loading-widget';
    loadingWidget.classList.add('flex', 'items-center', 'justify-center', 'p-4');
    loadingWidget.innerHTML = `
        <div role="status">
            <svg aria-hidden="true" class="w-8 h-8 mr-2 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
                <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
            </svg>
            <span class="sr-only">Loading...</span>
        </div>
    `;
    chatMessages.appendChild(loadingWidget);
    scrollToBottom();
}

function removeLoadingWidget() {
    const loadingWidget = document.getElementById('loading-widget');
    if (loadingWidget) {
        loadingWidget.remove();
    }
}

// const myCustomAdapter = {
//     streamText: (message, observer) => {
//         const socket = new WebSocket('https://pynlux.api.nlkit.com/pirate-speak');
//
//         // We register listeners for the WebSocket events here
//         // and call the observer methods accordingly
//         socket.onmessage = (event) => observer.next(event.data);
//         socket.onclose = () => observer.complete();
//         socket.onerror = (error) => void
//
//         // This is where we send the user message to the API
//         socket.send(message);
//     }
// }
//
// import {createAiChat} from '@nlux/core';
//
// const aiChat = createAiChat().withAdapter(myCustomAdapter);
// const root = document.getElementById('chat-element');
//
// aiChat.mount(root);