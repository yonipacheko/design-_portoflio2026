(() => {
  'use strict';
  const key = 'portfolio-analytics-excluded';
  if (location.pathname.endsWith('/analytics-preferences.html')) return;
  if (location.hostname !== 'fernando-product-design-portfolio.vercel.app') return;
  try {
    if (localStorage.getItem(key) === '1') return;
  } catch (_) {
    // If the preference cannot be read, avoid tracking this browser.
    return;
  }
  window.va = window.va || function () {
    (window.vaq = window.vaq || []).push(arguments);
  };
  // Record page paths only: strip query strings and fragments.
  window.va('beforeSend', (event) => {
    const url = new URL(event.url);
    url.search = '';
    url.hash = '';
    event.url = url.href;
    return event;
  });
  const script = document.createElement('script');
  script.defer = true;
  script.src = '/_vercel/insights/script.js';
  document.head.appendChild(script);
})();
