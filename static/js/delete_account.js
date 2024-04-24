const deleteAccountUrl = '{% url "delete" %}';

function deleteAccount() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(deleteAccountUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({userId: '{{ request.user.id }}'})
    })
    .then(response => {
        if (response.ok) {
            console.log('Account deleted');
            window.location.href = '/logout/';
        } else {
            console.error('Failed to delete account');
        }
    })
    .catch(error => {
        console.error('Error deleting account:', error);
    });
}

document.addEventListener('alpine:init', () => {
    Alpine.data('modal', () => ({
        showModal: false,
        deleteAccount
    }));
});
