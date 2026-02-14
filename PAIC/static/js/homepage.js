// Homepage interactivity: fetch recent documents and render preview
document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/documents')
    .then(r => r.json())
    .then(docs => {
      const grid = document.querySelector('.preview-grid');
      if (!grid) return;
      grid.innerHTML = ''; // replace static cards
      const recent = docs.slice(0, 4);
      if (recent.length === 0) {
        grid.innerHTML = '<div class="card"><h3>No documents yet</h3><p>Generate a business plan to see it here.</p></div>';
        return;
      }
      recent.forEach(doc => {
        const el = document.createElement('div');
        el.className = 'card';
        el.innerHTML = `<h3>${doc.title}</h3><p>${(doc.snapshot['Business Description']||'')}</p><small style="color:var(--muted)">Created: ${new Date(doc.created_at).toLocaleString()}</small>`;
        el.onclick = () => window.location.href = '/library';
        grid.appendChild(el);
      });
    })
    .catch(() => {
      // leave static content if API fails
    });
});
