// Get the necessary elements
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

// Function to send a message
function sendMessage(event) {
  event.preventDefault(); // Prevent the default form submission behavior

  const message = chatInput.value.trim(); // Get the user's message

  if (message) {
    // Display the user's message
    const userMessage = document.createElement('div');
    userMessage.textContent = message;
    chatMessages.appendChild(userMessage);

    // Clear the input field
    chatInput.value = '';

    // Here, you can call your LLM model and get the response
    // For example, you could make an AJAX request to a Django view that generates the response
    // and then update the chatMessages element with the response

    // For demonstration purposes, let's just display a simple response
    const response = 'This is a sample response from the LLM.';
    const botMessage = document.createElement('div');
    botMessage.textContent = response;
    chatMessages.appendChild(botMessage);
  }
}

// Attach the sendMessage function to the form's submit event
chatForm.addEventListener('submit', sendMessage);

console.log("create_chat.js loaded successfully.")