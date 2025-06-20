// Clipboard Code Start
 function copyToClipboard() {
      const text = document.getElementById("accountText").textContent;
      navigator.clipboard.writeText(text).then(() => {
        const msg = document.getElementById("copiedMsg");
        msg.classList.add("show");
        setTimeout(() => {
          msg.classList.remove("show");
        }, 2000); // hide after 2 seconds
      }).catch(err => {
        console.error("Failed to copy: ", err);
      });
    }
// Clipboard Code End