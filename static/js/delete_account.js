document.addEventListener('DOMContentLoaded', function() {
            const deleteAccountBtn = document.getElementById('deleteAccountBtn');
            const confirmDeleteModal = document.getElementById('popup-modal');
            const confirmDelete = document.getElementById('confirmDelete');
            const cancelDelete = document.getElementById('cancelDelete');

            deleteAccountBtn.addEventListener('click', () => {
          const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
          console.log(deleteAccountUrl);
          fetch(deleteAccountUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({userId: currentUserId})
          })
              .then(response => {
                if (response.ok) {
                  // Account deleted successfully
                  console.log('Account deleted');
                  // Perform any additional actions, such as redirecting to a logout page
                  window.location.href = '/logout/';
                } else {
                  // Handle account deletion error
                  console.error('Failed to delete account');
                }
              })
              .catch(error => {
                console.error('Error deleting account:', error);
              });

      });
    });