// Library interactivity: search, sort, delete

document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('searchInput');
  if (search) {
    search.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      document.querySelectorAll('.document-card').forEach(card => {
        card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
});

function deleteDoc(id, el){
  if(!confirm('Delete this document?')) return;
  // Try API delete, if not available just remove from DOM
  fetch(`/api/documents/${id}`, { method: 'DELETE' })
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        el.closest('.document-card').remove();
      } else {
        // fallback
        el.closest('.document-card').remove();
      }
    })
    .catch(() => {
      el.closest('.document-card').remove();
    });
}
