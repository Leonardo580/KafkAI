    function createNewChat() {

    // Fetch the chat form template
    fetch(chat_form_url)
        .then(response => response.text())
        .then(data => {
            console.log(data);
            const contentBlock = document.querySelector('#main');
            contentBlock.innerHTML = data;
            // Add event listener for form submission or other chat functionality
        })
        .catch(error => console.error(error));
}

