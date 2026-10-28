const siteHeader = document.querySelector('.site-header');
const menuButton = document.querySelector('.menu-toggle');
function closeMenu(returnFocus = false) {
  if (!siteHeader || !menuButton) return;
  siteHeader.classList.remove('menu-open');
  menuButton.setAttribute('aria-expanded', 'false');
  if (returnFocus) menuButton.focus();
}
menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  siteHeader.classList.toggle('menu-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && siteHeader?.classList.contains('menu-open')) closeMenu(true);
});
document.addEventListener('click', event => {
  if (siteHeader && !siteHeader.contains(event.target)) closeMenu();
});
document.querySelectorAll('.primary-nav a').forEach(link => link.addEventListener('click', () => closeMenu()));
window.matchMedia('(min-width: 761px)').addEventListener('change', event => { if (event.matches) closeMenu(); });
const activePage = (window.location.pathname.split('/').pop() || 'index').replace(/\.html$/, '');
document.querySelectorAll('.primary-nav a').forEach(link => {
  if (link.getAttribute('href')?.replace(/\.html$/, '') === activePage) link.setAttribute('aria-current', 'page');
});
const projectKey = new URLSearchParams(window.location.search).get('id') || 'mw3';
if (document.body.hasAttribute('data-project-page')) {
  const active = ['mw3', 'pirates-moon', 'mw4'].includes(projectKey) ? projectKey : 'missing';
  document.querySelectorAll('[data-project]').forEach(section => { section.hidden = section.dataset.project !== active; });
  const titles = {mw3:'MW3', 'pirates-moon':'MW3: Pirate’s Moon', mw4:'MW4', missing:'Project not found'};
  document.title = `Core Critical — ${titles[active]}`;
}
