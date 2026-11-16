(() => {
  'use strict';
  const key = 'portfolio-analytics-excluded';
  const status = document.getElementById('status');
  function update() {
    const excluded = localStorage.getItem(key) === '1';
    status.textContent = excluded ? 'Your visits are excluded on this browser.' : 'Your visits are currently counted on this browser.';
    document.getElementById('exclude').disabled = excluded;
    document.getElementById('include').disabled = !excluded;
  }
  function save(excluded) {
    try {
      if (excluded) localStorage.setItem(key, '1');
      else localStorage.removeItem(key);
      update();
    } catch (_) {
      status.textContent = 'This browser blocked saving the preference. Allow site storage and try again.';
    }
  }
  document.getElementById('exclude').addEventListener('click', () => save(true));
  document.getElementById('include').addEventListener('click', () => save(false));
  try { update(); } catch (_) { status.textContent = 'Browser storage is unavailable; analytics will stay off.'; }
})();
