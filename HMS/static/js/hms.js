function openCall() {
  document.getElementById('callModal').classList.add('show');
  showCallState('stateConnecting');
  setTimeout(() => {
    const m = document.getElementById('callModal');
    if (m && m.classList.contains('show')) showCallState('stateQueue');
  }, 2000);
}

function showCallState(id) {
  ['stateConnecting','stateQueue','stateConnected','stateCallback'].forEach(s => {
    const el = document.getElementById(s);
    if (el) el.style.display = 'none';
  });
  const t = document.getElementById(id);
  if (t) t.style.display = 'block';
}

function requestCallback() { showCallState('stateCallback'); }
function closeModal() { document.getElementById('callModal').classList.remove('show'); }

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => a.remove());
  }, 4000);
});