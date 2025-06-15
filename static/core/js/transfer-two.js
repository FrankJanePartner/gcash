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