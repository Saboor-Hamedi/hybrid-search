// 1. Set up the modal
function deleteRecord(docId) {
  if (event) event.preventDefault();
  
  // Reset Modal text and icons
  const titleEl = document.getElementById('quickDeleteTitle');
  const msgEl = document.getElementById('quickDeleteMessage');
  const confirmBtn = document.getElementById('quickDeleteConfirmBtn');
  const iconEl = document.getElementById('quickDeleteIcon');
  const form = document.getElementById("quickDeleteForm");
  
  if (titleEl) titleEl.textContent = 'Delete Document?';
  if (iconEl) {
    iconEl.className = 'bi bi-exclamation-triangle';
    iconEl.style.display = 'inline-block';
  }
  if (msgEl) msgEl.innerHTML = `Are you sure you want to delete <strong>#<span id="delTargetId">${docId}</span></strong>?`;
  if (confirmBtn) {
    confirmBtn.textContent = 'Delete Permanent';
    confirmBtn.disabled = false;
  }
  
  // Clear any hijacks (like startNewSession's onsubmit)
  if (form) form.onsubmit = null;

  document.getElementById("delTargetId").textContent = docId;
  document.getElementById("quickDeleteForm").action = `/document/${docId}/delete_post`;
  document.getElementById("quickDeleteModal").style.display = "flex";
}

// 2. NEW: Intercept the form submission
document
  .getElementById("quickDeleteForm")
  .addEventListener("submit", async function (e) {
    // If it's a hijacked form for New Session, don't run this
    if (this.onsubmit) return;
    
    e.preventDefault(); 

    const submitBtn = document.getElementById('quickDeleteConfirmBtn');
    const docId = document.getElementById("delTargetId").textContent;

    // Show loading on button (Rotating Circle)
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Deleting...';

    try {
      const response = await fetch(this.action, {
        method: "POST",
        body: new FormData(this),
      });

      //  Success: Close modal and remove item from DOM
      document.getElementById("quickDeleteModal").style.display = "none";


      // check if the page is document page
      if (window.location.pathname.includes('document')) {
        const backQuery = encodeURIComponent(this.q.value || '');

        // Here we separate mode. 
        let backMode = this.mode.value || 'hybrid';
        let strategy = 'linear'; // this default 
        if(backMode.includes('-')){
            [backMode, strategy] = backMode.split('-');

        }

        // Here we build the full URL with search parameters 
        window.location.href = `/?query=${backQuery}&mode=${backMode}&fusion_strategy=${strategy}`;
        return;
      }

      // Find the item in the list and animate it out
      const items = document.querySelectorAll(".result-item");
      items.forEach((item) => {
        if (item.innerHTML.includes("#" + docId)) {
          item.style.opacity = "0";
          item.style.transform = "translateX(50px)";
          item.style.transition = "all 0.4s ease";
          setTimeout(() => item.remove(), 400); // Remove from HTML after animation
        }
      });
    } catch (err) {
      alert("Delete failed. Please try again.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Delete Permanent";
    }
  });
