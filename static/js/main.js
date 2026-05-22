// MentoriaConecta - main.js

// Auto-dismiss flash messages
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.style.opacity = '0', 4000);
  setTimeout(() => el.remove(), 4500);
  el.style.transition = 'opacity .5s';
});

// Marcar link ativo na sidebar
const currentPath = window.location.pathname;
document.querySelectorAll('.sidebar-nav a').forEach(link => {
  if (link.getAttribute('href') === currentPath) {
    link.classList.add('active');
  }
});
