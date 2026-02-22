// Document page JS: copy, edit, delete, and card hover behaviors
function copyContent(button) {
  const content = document.querySelector('.document-content').innerText;
  navigator.clipboard.writeText(content).then(() => {
    const originalHtml = button.innerHTML;
    button.innerHTML = '<i class="bi bi-check-lg"></i>';
    button.classList.remove('btn-outline-secondary');
    button.classList.add('btn-success');
    setTimeout(() => {
      button.innerHTML = originalHtml;
      button.classList.remove('btn-success');
      button.classList.add('btn-outline-secondary');
    }, 2000);
  }).catch(err => { alert('Failed to copy content'); });
}
function toggleEditMode(){ const editModal = new bootstrap.Modal(document.getElementById('editModal')); editModal.show(); }
function confirmDelete(){ const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal')); deleteModal.show(); }

document.addEventListener('DOMContentLoaded', function () {
  const cards = document.querySelectorAll('.col-md-6 .card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', function () {
      this.style.transform = 'translateY(-1px)';
      this.style.boxShadow = '0 2px 6px rgba(0,0,0,0.06)';
    });
    card.addEventListener('mouseleave', function () {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = '';
    });
  });
});
