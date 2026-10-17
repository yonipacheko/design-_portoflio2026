const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const animations = [...document.querySelectorAll('[data-animation]')].map((video) => {
  const button = video.parentElement.querySelector('.haki-animation-toggle');
  let inView = false;
  let userPaused = false;
  const load = () => {
    const source = video.querySelector('source');
    if (!source.hasAttribute('src')) {
      source.src = source.dataset.src;
      video.load();
    }
  };
  const play = () => {
    load();
    video.play().catch(() => { button.textContent = 'Play animation'; });
  };
  video.addEventListener('play', () => {
    button.textContent = 'Pause animation';
    button.setAttribute('aria-label', `Pause ${video.getAttribute('aria-label').toLowerCase()}`);
  });
  video.addEventListener('pause', () => {
    button.textContent = 'Play animation';
    button.setAttribute('aria-label', `Play ${video.getAttribute('aria-label').toLowerCase()}`);
  });
  button.addEventListener('click', () => {
    if (video.paused) {
      userPaused = false;
      play();
    } else {
      userPaused = true;
      video.pause();
    }
  });
  const sync = () => {
    if (inView && !document.hidden && !reducedMotion.matches && !userPaused) play();
    else video.pause();
  };
  return { video, sync, setInView: (value) => { inView = value; sync(); } };
});
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      animations.find(({ video }) => video === entry.target).setInView(entry.isIntersecting);
    });
  }, { threshold: 0.15 });
  animations.forEach(({ video }) => observer.observe(video));
}
// Unsupported browsers retain a poster and an explicit play button.
reducedMotion.addEventListener('change', () => animations.forEach(({ sync }) => sync()));
document.addEventListener('visibilitychange', () => animations.forEach(({ sync }) => sync()));
