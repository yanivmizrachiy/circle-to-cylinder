(() => {
  'use strict';

  const paper = document.getElementById('cone-reader-paper');
  const pages = Array.from(paper?.querySelectorAll(':scope > .a4-page') ?? []);
  const toolbar = document.getElementById('cone-reader-toolbar');
  const viewport = document.getElementById('cone-reader-viewport');
  const input = document.getElementById('cone-page');
  const previous = document.getElementById('cone-prev');
  const next = document.getElementById('cone-next');
  const total = document.getElementById('cone-total');
  const status = document.getElementById('cone-reader-status');
  const zoomIn = document.getElementById('cone-zoom-in');
  const zoomOut = document.getElementById('cone-zoom-out');
  const fit = document.getElementById('cone-fit');
  const printPage = document.getElementById('cone-print-page');
  const printAll = document.getElementById('cone-print-all');

  if (!pages.length || !toolbar || !viewport || !input) return;

  let active = 0;
  let zoom = 1;
  let resizeFrame = 0;
  let printing = false;
  const normalize = (value) => {
    const numeric = Number(value);
    const integer = Number.isFinite(numeric) ? Math.trunc(numeric) : 1;
    return Math.max(1, Math.min(pages.length, integer || 1));
  };

  function pageFromHash() {
    return normalize(new URLSearchParams(location.hash.slice(1)).get('page'));
  }

  function updateScale() {
    resizeFrame = 0;
    const visibleViewport = window.visualViewport;
    const height = visibleViewport?.height ?? window.innerHeight;
    const top = viewport.getBoundingClientRect().top;
    const availableHeight = Math.max(1, height - top);
    viewport.style.setProperty('--cone-viewport-height', `${availableHeight}px`);
    const css = getComputedStyle(viewport);
    const width = Math.max(1, viewport.clientWidth - parseFloat(css.paddingLeft) - parseFloat(css.paddingRight));
    const space = Math.max(1, viewport.clientHeight - parseFloat(css.paddingTop) - parseFloat(css.paddingBottom));
    const page = pages[active];
    const scale = Math.min(1, width / page.offsetWidth, space / page.offsetHeight) * zoom;
    viewport.style.setProperty('--cone-scale', String(scale));
    viewport.style.setProperty('--cone-scaled-width', `${page.offsetWidth * scale}px`);
    viewport.style.setProperty('--cone-scaled-height', `${page.offsetHeight * scale}px`);
    zoomOut.disabled = zoom <= 1;
    zoomIn.disabled = zoom >= 3;
  }

  function scheduleScale() {
    if (!resizeFrame) resizeFrame = requestAnimationFrame(updateScale);
  }

  function goToPage(value, { syncUrl = true } = {}) {
    const number = normalize(value);
    const index = number - 1;
    pages[active].classList.remove('is-current');
    pages[active].setAttribute('aria-hidden', 'true');
    pages[active].inert = true;
    active = index;
    pages[active].classList.add('is-current');
    pages[active].removeAttribute('aria-hidden');
    pages[active].inert = false;
    input.value = String(number);
    previous.disabled = active === 0;
    next.disabled = active === pages.length - 1;
    status.textContent = `עמוד ${number} מתוך ${pages.length} בחוברת החרוט`;
    if (syncUrl && location.hash !== `#page=${number}`) {
      history.replaceState(null, '', `#page=${number}`);
    }
    viewport.scrollTop = 0;
    viewport.scrollLeft = 0;
    scheduleScale();
  }

  function setZoom(value) {
    zoom = Math.max(1, Math.min(3, value));
    scheduleScale();
    if (zoom === 1) {
      viewport.scrollTop = 0;
      viewport.scrollLeft = 0;
    }
  }

  async function print(mode) {
    if (printing) return;
    printing = true;
    printPage.disabled = true;
    printAll.disabled = true;
    try {
      if (document.fonts?.ready) await document.fonts.ready;
      const images = mode === 'current' ? pages[active].querySelectorAll('img') : paper.querySelectorAll('img');
      await Promise.all(Array.from(images, (image) => image.decode?.().catch(() => {}) ?? Promise.resolve()));
      document.body.dataset.conePrint = mode;
      window.print();
    } finally {
      printing = false;
      printPage.disabled = false;
      printAll.disabled = false;
    }
  }

  pages.forEach((page) => { page.setAttribute('aria-hidden', 'true'); page.inert = true; });
  total.textContent = String(pages.length);
  input.max = String(pages.length);
  input.disabled = false;
  document.body.classList.add('cone-reader-enabled');
  toolbar.hidden = false;
  goToPage(pageFromHash());

  previous.addEventListener('click', () => goToPage(active));
  next.addEventListener('click', () => goToPage(active + 2));
  input.addEventListener('change', () => goToPage(input.value));
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') { event.preventDefault(); goToPage(input.value); input.blur(); }
  });
  zoomIn.addEventListener('click', () => setZoom(zoom + .25));
  zoomOut.addEventListener('click', () => setZoom(zoom - .25));
  fit.addEventListener('click', () => setZoom(1));
  printPage.addEventListener('click', () => { void print('current'); });
  printAll.addEventListener('click', () => { void print('all'); });
  window.addEventListener('afterprint', () => { delete document.body.dataset.conePrint; scheduleScale(); });
  window.addEventListener('hashchange', () => goToPage(pageFromHash()));
  window.addEventListener('resize', scheduleScale);
  window.visualViewport?.addEventListener('resize', scheduleScale);
  document.fonts?.ready.then(scheduleScale);
  if ('ResizeObserver' in window) new ResizeObserver(scheduleScale).observe(toolbar);
  window.addEventListener('keydown', (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input, textarea, select, [contenteditable]')) return;
    const destination = { ArrowLeft: active + 2, ArrowRight: active, Home: 1, End: pages.length }[event.key];
    if (destination !== undefined) { event.preventDefault(); goToPage(destination); }
  });

  let touchStart = null;
  viewport.addEventListener('pointerdown', (event) => {
    if (event.pointerType === 'touch' && event.isPrimary && zoom === 1) {
      touchStart = { x:event.clientX, y:event.clientY, time:performance.now(), id:event.pointerId };
    }
  });
  viewport.addEventListener('pointerup', (event) => {
    if (!touchStart || touchStart.id !== event.pointerId) return;
    const start = touchStart;
    touchStart = null;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (zoom === 1 && performance.now() - start.time < 800 && Math.abs(dx) > 70 && Math.abs(dy) < 40) {
      goToPage(dx > 0 ? active + 2 : active);
    }
  });
  viewport.addEventListener('pointercancel', () => { touchStart = null; });
})();
