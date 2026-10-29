const names = { bench: 'סביבת עבודה', library: 'ספרייה פתוחה', arena: 'זירת תרגול' };
const query = new URLSearchParams(location.search);
let selected = Object.hasOwn(names, query.get('design')) ? query.get('design') : 'bench';
let device = query.get('device') === 'phone' ? 'phone' : 'desktop';
const frame = document.querySelector('#preview');
frame.addEventListener('load', () => {
  const previewDocument = frame.contentDocument;
  if (!previewDocument) return;
  const clearFocus = () => frame.removeAttribute('data-focus-inside');
  previewDocument.addEventListener('focusin', () => frame.setAttribute('data-focus-inside', 'true'));
  frame.contentWindow.addEventListener('blur', clearFocus);
});
document.addEventListener('focusin', () => {
  if (document.activeElement !== frame) frame.removeAttribute('data-focus-inside');
});
function render(replaceFrame = true) {
  document.querySelectorAll('[data-design]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.design === selected)));
  document.querySelectorAll('[data-device]').forEach(button => {
    if (button.tagName === 'BUTTON') button.setAttribute('aria-pressed', String(button.dataset.device === device));
  });
  document.querySelector('.frame-shell').dataset.device = device;
  document.querySelector('#current').textContent = names[selected];
  const next = `./${selected}/index.html`;
  if (replaceFrame && frame.getAttribute('src') !== next) frame.src = next;
  frame.title = `הצעת ${names[selected]}, ממשק הדגמה מקומי`;
  document.querySelector('#full-size').href = next;
  const url = new URL(location.href);
  url.search = new URLSearchParams({ design: selected, device }).toString();
  history.replaceState(null, '', url);
  document.querySelector('#share-status').textContent = '';
}
document.querySelectorAll('[data-design]').forEach(button => button.addEventListener('click', () => {
  if (selected === button.dataset.design) return;
  selected = button.dataset.design;
  render();
}));
document.querySelectorAll('button[data-device]').forEach(button => button.addEventListener('click', () => {
  device = button.dataset.device;
  render(false);
}));
document.querySelector('#share').addEventListener('click', async () => {
  const status = document.querySelector('#share-status');
  try { await navigator.clipboard.writeText(location.href); status.textContent = 'הקישור הועתק. אפשר לשלוח אותו לשקד.'; }
  catch { status.textContent = `אפשר להעתיק את הכתובת מסרגל הדפדפן: ${location.href}`; }
});
render();
