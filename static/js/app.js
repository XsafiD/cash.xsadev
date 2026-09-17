// Auto-hide flash message setelah 5 detik.
document.querySelectorAll('[data-alert]').forEach((el) => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s ease';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 5000);
});
