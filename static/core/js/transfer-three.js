function openModal() {
    // Immediately show the modal—no validation here
    document.getElementById('transactionModal').style.display = 'flex';
}

function confirmTransaction() {
    // Close the modal; actual backend call is up to your developer
    document.getElementById('transactionModal').style.display = 'none';
    // You could dispatch a custom event or call a stub function here instead
}

// Close modal on backdrop click
window.addEventListener('click', e => {
    const modal = document.getElementById('transactionModal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Disable send button and show loading state on form submit
document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.querySelector('.send-btn');
    const formElements = ['#Nickname', '#account-name', '#account-number', '#note'];

    sendBtn.addEventListener('click', async (event) => {
        event.preventDefault();

        // Disable button and show loading text
        sendBtn.disabled = true;
        const originalText = sendBtn.textContent;
        sendBtn.textContent = 'Sending...';

        // Collect form data
        const data = {
            nickname: document.querySelector('#Nickname').value.trim(),
            account_name: document.querySelector('#account-name').value.trim(),
            account_number: document.querySelector('#account-number').value.trim(),
            note: document.querySelector('#note').value.trim(),
        };

        try {
            const response = await fetch('/transferTwo/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.success) {
                // Show modal for entering verification code
                openModal();
            } else {
                alert(result.error || 'An error occurred.');
            }
        } catch (error) {
            alert('An error occurred: ' + error.message);
        } finally {
            // Re-enable button and restore text
            sendBtn.disabled = false;
            sendBtn.textContent = originalText;
        }
    });
});

// Helper function to get CSRF token cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}