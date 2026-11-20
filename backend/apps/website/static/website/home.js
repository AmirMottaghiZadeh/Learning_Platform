(() => {
  const story = document.querySelector('.home-story');
  if (!story) return;

  const card = story.querySelector('.home-reference-card');
  const tabList = card.querySelector('.home-reference-tabs');
  const tabs = [...tabList.querySelectorAll('[role="tab"]')];
  const referenceLinks = [...card.querySelectorAll('[data-home-zoom]')];
  const dialog = document.querySelector('.home-screen-preview');

  card.addEventListener('click', event => {
    const link = event.target.closest('[data-home-zoom]');
    if (!link || !dialog.showModal || isModifiedClick(event)) return;

    event.preventDefault();
    dialog.querySelector('h2').textContent = link.dataset.previewTitle;
    const image = dialog.querySelector('img');
    image.src = link.href;
    image.alt = link.dataset.previewAlt;
    dialog.showModal();
  });

  const header = document.getElementById('hdr');
  const stage = story.querySelector('.home-stage');
  const scenes = [...story.querySelectorAll('.home-scene')];
  const art = story.querySelector('.home-art');
  const device = art.querySelector('.home-device-seat');
  const deviceBody = device.querySelector('.home-device-body');
  const shadow = device.querySelector('.home-device-shadow');
  const rim = device.querySelector('.home-frame-highlight');
  const screens = [...device.querySelectorAll('[data-screen]')];
  const sideImages = [...art.querySelectorAll('.home-side-device img')];
  const controls = story.querySelector('.home-scene-controls');
  const copy = story.querySelector('.home-story-copy');
  const steps = [...controls.querySelectorAll('nav a')];
  const next = controls.querySelector('.home-scene-next');
  const nextTargets = ['library', 'references', document.getElementById('stats') ? 'stats' : 'features'];
  const nextLabels = ['دارونامه را ببینید', 'منابع بالینی را ببینید', 'ادامهٔ صفحه'];
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = matchMedia('(max-width: 720px)');
  const curve = 'cubic-bezier(.2,.8,.2,1)';

  let entrance = [];
  let frame = 0;
  let previousTime = 0;
  let renderedProgress = 0;
  let activeScene = -1;
  let start = 0;
  let travel = 1;
  let artWidth = 0;

  const clamp = value => Math.max(0, Math.min(1, value));
  const mix = (from, to, amount) => from + (to - from) * amount;
  const ease = (from, to, value) => {
    const t = clamp((value - from) / (to - from));
    return t * t * (3 - 2 * t);
  };

  function isModifiedClick(event) {
    return event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey;
  }

  function move(element, x, y, angle = 0, scale = 1) {
    element.style.transform = `translate3d(${x}px,${y}px,0) rotate(${angle}deg) scale(${scale})`;
  }

  function measure() {
    story.style.setProperty('--story-top', `${header.offsetHeight}px`);
    start = scrollY + story.getBoundingClientRect().top - header.offsetHeight;
    travel = Math.max(1, story.offsetHeight - stage.offsetHeight);
    artWidth = art.clientWidth;
  }

  function updateScene(index) {
    if (index === activeScene) return;
    activeScene = index;
    stage.dataset.scene = scenes[index].dataset.homeScene;
    copy.scrollTop = 0;

    const focusedScene = document.activeElement?.closest('.home-scene');
    if (focusedScene && focusedScene !== scenes[index]) steps[index].focus({preventScroll: true});
    scenes.forEach((scene, i) => {
      const current = index === i;
      scene.inert = !current;
      if (current) {
        scene.removeAttribute('aria-hidden');
        steps[i].setAttribute('aria-current', 'step');
      } else {
        scene.setAttribute('aria-hidden', 'true');
        steps[i].removeAttribute('aria-current');
      }
    });
    next.hash = nextTargets[index];
    next.querySelector('span').textContent = nextLabels[index];
  }

  function render(value) {
    const library = ease(.14, .43, value);
    const references = ease(.56, .86, value);
    const fan = ease(.62, .94, value);
    const selected = tabs.findIndex(tab => tab.getAttribute('aria-selected') === 'true');
    const selectedReference = tabs[selected].dataset.reference;

    if (value > .045) {
      for (const animation of entrance) {
        if (animation.playState === 'running') animation.finish();
      }
    }

    updateScene(value > .67 ? 2 : value > .27 ? 1 : 0);
    stage.toggleAttribute('data-reference-resting', references > .995);
    const still = reducedMotion.matches;
    move(device, (still ? 0 : mobile.matches ? 4 : 12) * library * (1 - references), still ? 0 : -6 * library + 4 * references,
      still ? 0 : -5 * (1 - library) - references, still ? 1 : 1 - .06 * library - .025 * references);

    screens.forEach(screen => {
      const key = screen.dataset.screen;
      const layer = key === 'home' ? 1 : key === 'library' ? library : key === selectedReference ? references : 0;
      screen.style.opacity = layer;
      move(screen, 0, still ? 0 : key === 'home' ? -12 * library : (1 - layer) * 24);
    });

    const adjacentLinks = referenceLinks.filter((link, index) => index !== selected);
    sideImages.forEach((image, index) => {
      if (fan > 0 && image.src !== adjacentLinks[index].href) image.src = adjacentLinks[index].href;
      const frame = image.parentElement;
      const direction = index ? -1 : 1;
      frame.style.opacity = fan;
      const spread = still ? 1 : fan;
      move(frame, direction * artWidth * (mobile.matches ? .265 : .245) * spread, 18 * spread,
        direction * 11 * spread, .84 + .14 * spread);
    });

    const entering = [1, ease(.24, .44, value), ease(.65, .86, value)];
    const leaving = [ease(.12, .28, value), ease(.56, .72, value), 0];
    scenes.forEach((scene, index) => {
      scene.style.opacity = entering[index] * (1 - leaving[index]);
      move(scene, 0, still ? 0 : 22 * (1 - entering[index]) - 18 * leaving[index]);
    });
  }

  function scrollProgress() {
    return clamp((scrollY - start) / travel);
  }

  function animate(now) {
    frame = 0;
    const target = scrollProgress();
    const delta = Math.max(1, Math.min(40, now - (previousTime || now - 16)));
    renderedProgress = Math.abs(renderedProgress - target) < .001
      ? target
      : mix(renderedProgress, target, 1 - Math.exp(-delta / 53));
    render(renderedProgress);
    previousTime = renderedProgress === target ? 0 : now;
    if (previousTime) schedule();
  }

  function schedule() {
    if (!frame) frame = requestAnimationFrame(animate);
  }

  function playEntrance() {
    if (!deviceBody.animate || (location.hash && location.hash !== '#overview') || scrollProgress() > .015) return;
    if (reducedMotion.matches) {
      entrance = [deviceBody.animate([{opacity: .5}, {opacity: 1}], {duration: 180, easing: curve})];
      return;
    }
    const distance = mobile.matches ? '-44svh' : '-65svh';
    const duration = 860;
    entrance = [
      deviceBody.animate([
        {transform: `translate3d(32px,${distance},0) rotate(-8deg) scale(.96)`, offset: 0, easing: 'cubic-bezier(.44,.05,.74,.58)'},
        {transform: 'translate3d(0,2px,0) rotate(.5deg)', offset: .78, easing: curve},
        {transform: 'none', offset: 1},
      ], duration),
      shadow.animate([
        {opacity: 0, transform: 'translate(40px,38px) scale(1.14)'},
        {opacity: .3, transform: 'translate(15px,14px) scale(1.06)', offset: .61},
        {opacity: 1, transform: 'none'},
      ], {duration, easing: curve}),
      rim.animate([{opacity: 0}, {opacity: .67, offset: .4}, {opacity: 0}], {duration: 430, delay: 470, easing: curve}),
      scenes[0].querySelector('.home-overview-copy').animate([
        {opacity: .22, transform: 'translateY(12px)'},
        {opacity: 1, transform: 'none'},
      ], {duration: 480, easing: curve}),
    ];
  }

  function refresh() {
    measure();
    schedule();
  }

  story.classList.add('home-motion-ready');
  document.documentElement.classList.add('home-motion');
  controls.hidden = false;
  measure();
  renderedProgress = scrollProgress();
  render(renderedProgress);
  playEntrance();

  new MutationObserver(schedule).observe(tabList, {attributes: true, subtree: true, attributeFilter: ['aria-selected']});
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', refresh, {passive: true});
  reducedMotion.addEventListener('change', () => {
    entrance.forEach(animation => animation.cancel());
    schedule();
  });
  document.fonts?.ready.then(refresh);
})();
