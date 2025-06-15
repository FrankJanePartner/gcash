const balanceEl = document.getElementById('balance');
    let isVisible = false;
    const actualAmount = '₱ 0.00';

    function toggleBalance() {
      isVisible = !isVisible;
      balanceEl.textContent = isVisible ? actualAmount : '₱ ••••';
    }