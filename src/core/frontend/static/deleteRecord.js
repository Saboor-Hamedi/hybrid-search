// 1. Set up the modal (same as before)
function deleteRecord(docId) {
  event.preventDefault();
  document.getElementById("delTargetId").textContent = docId;
  document.getElementById("quickDeleteForm").action =
    `/document/${docId}/delete_post`;
  document.getElementById("quickDeleteModal").style.display = "flex";
}

// 2. NEW: Intercept the form submission
document
  .getElementById("quickDeleteForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault(); // 🛑 This stops the page reload

    const submitBtn = this.querySelector('button[type="submit"]');
    const docId = document.getElementById("delTargetId").textContent;

    // Show loading on button
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm"></span> Deleting...';

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
