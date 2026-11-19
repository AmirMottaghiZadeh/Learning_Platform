(() => {
    const story = document.querySelector('.home-story');
    if (!story) return;

    const stage = story.querySelector('.home-stage');
    const scenes = [...stage.querySelectorAll('.home-scene')];
    const copies = scenes.map(scene => scene.querySelector('.home-scene-copy'));
    const controls = stage.querySelector('.home-scene-controls');
    const tabs = [...controls.querySelectorAll('nav a')];
    const next = controls.querySelector('.home-scene-next');
    const libraryField = stage.querySelector('.home-field-library');
    const referenceField = stage.querySelector('.home-field-references');
    const gallery = stage.querySelector('.home-reference-gallery');
    const [uptodate, lexicomp, conditions] = gallery.querySelectorAll('a');
    const dialog = document.querySelector('.home-screen-preview');

    gallery.addEventListener('click', event => {
        const frame = event.target.closest('a');
        if (!frame || !dialog.showModal || event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;

        event.preventDefault();
        const image = dialog.querySelector('img');
        image.src = frame.href;
        image.alt = frame.querySelector('img').alt;
        dialog.querySelector('h2').textContent = frame.querySelector('span').textContent;
        dialog.showModal();
    });

    if (story.dataset.motion !== 'on' || !window.matchMedia || !window.CSS?.supports('position', 'sticky')) return;

    const mobileScreen = matchMedia('(max-width: 720px)');
    const shortScreen = matchMedia('(max-width: 365px), (max-width: 720px) and (max-height: 690px)');
    const supportsInert = 'inert' in HTMLElement.prototype;
    const hero = scenes[0];
    const artwork = document.createElement('div');
    artwork.className = 'home-shared';
    artwork.setAttribute('aria-hidden', 'true');
    artwork.setAttribute('inert', '');
    const device = hero.querySelector('.hero-dev').cloneNode(true);
    const screen = device.querySelector('.ip-screen');
    const libraryImage = stage.querySelector('.home-library-phone img').cloneNode(true);
    libraryImage.className = 'shot home-phone-library';
    libraryImage.removeAttribute('loading');
    const homeImages = [...screen.querySelectorAll('.shot')];
    const accessories = [...device.querySelectorAll('.plate, .sticker, .ip-status, .ip-island, .ip-home')];
    const header = document.getElementById('hdr');
    let dimensions;
    let frame = 0;
    let progress = 0;
    let lastFrame = 0;
    let active = -1;

    screen.append(libraryImage);
    artwork.append(device);

    const clamp = value => Math.max(0, Math.min(1, value));
    const mix = (from, to, amount) => from + (to - from) * amount;
    const smooth = (from, to, value) => {
        const t = clamp((value - from) / (to - from));
        return t * t * (3 - 2 * t);
    };
    const translate = (x, y) => `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
    const opacity = (element, value) => { element.style.opacity = value.toFixed(4); };

    function measure() {
        const top = header.offsetHeight;
        story.style.setProperty('--story-top', `${top}px`);
        const { width, height } = stage.getBoundingClientRect();
        const mobile = mobileScreen.matches;
        const small = shortScreen.matches;
        const phoneHeight = mobile
            ? Math.min(425, height * (small ? .43 : .53), width * 1.02)
            : Math.min(575, height * .72, width * .54);
        const phoneWidth = phoneHeight * 415 / 874;
        const heroHeight = mobile ? phoneHeight : Math.min(716, height * .84, width * .53);
        const galleryGap = parseFloat(getComputedStyle(gallery).columnGap);
        const gallerySpace = mobile ? width - 58 : Math.min(width * .45, 598);
        const referenceWidth = Math.min((gallerySpace - 2 * galleryGap) / 3, phoneWidth * .81, 190);
        const referenceHeight = (referenceWidth - 10) * 852 / 393 + 10;
        const galleryWidth = 3 * referenceWidth + 2 * galleryGap;
        const referenceX = width * (mobile ? .5 : .278);
        const referenceY = height * (mobile ? (small ? .62 : .635) : .48);
        dimensions = {
            width, height, mobile, small, phoneWidth, phoneHeight, heroHeight,
            referenceWidth, referenceX, referenceY,
            start: scrollY + story.getBoundingClientRect().top - top,
            travel: Math.max(1, story.offsetHeight - stage.offsetHeight),
        };

        artwork.style.setProperty('--w', `${phoneWidth}px`);
        gallery.style.width = `${galleryWidth}px`;
        // The gallery is positioned relative to its full-width animated section.
        gallery.style.transform = translate(referenceX - galleryWidth / 2, referenceY - referenceHeight / 2);
    }

    function setSceneHidden(scene, hidden) {
        scene.toggleAttribute('inert', hidden);
        if (hidden) scene.setAttribute('aria-hidden', 'true');
        else scene.removeAttribute('aria-hidden');
        if (!supportsInert) {
            scene.querySelectorAll('a[href]').forEach(link => {
                if (hidden) link.tabIndex = -1;
                else link.removeAttribute('tabindex');
            });
        }
    }

    function updateScene(index) {
        if (index === active) return;
        active = index;
        stage.dataset.scene = scenes[index].id;
        const previous = document.activeElement?.closest('.home-scene');
        if (previous && previous !== scenes[index]) tabs[index].focus({ preventScroll: true });

        scenes.forEach((scene, position) => {
            setSceneHidden(scene, position !== index);
            if (position === index) tabs[position].setAttribute('aria-current', 'step');
            else tabs[position].removeAttribute('aria-current');
        });

        const targets = ['library', 'references', document.getElementById('stats') ? 'stats' : 'features'];
        next.href = `#${targets[index]}`;
        next.firstElementChild.textContent = ['اسکرول برای کشف', 'دیدن منابع بالینی', 'ادامهٔ صفحه'][index];
    }

    function render(value) {
        if (value > .065) story.classList.remove('is-entering');
        const { width, height, mobile, small, phoneWidth, phoneHeight, heroHeight, referenceWidth, referenceX, referenceY } = dimensions;
        const open = smooth(.065, .455, value);
        const handoff = smooth(.54, .74, value);
        const heroX = Math.min(width * .5 - 20, Math.max(width * .32, width * .5 - 300));
        const x = mix(mobile ? width * .5 : mix(heroX, width * .28, open), referenceX, handoff);
        const heroCenter = mobile ? (small ? .625 : .59) : .47;
        const libraryCenter = mobile ? (small ? .62 : .60) : .475;
        const y = mix(height * mix(heroCenter, libraryCenter, open), referenceY, handoff);
        const scale = mix(mix(heroHeight / phoneHeight, .97, open), referenceWidth / phoneWidth, handoff);
        artwork.style.transform = `${translate(x - phoneWidth / 2, y - phoneHeight / 2)} rotate(${mix(-2, 0, open)}deg) scale(${scale})`;

        const libraryProgress = smooth(.155, .405, value);
        const center = smooth(.68, .82, value);
        const leftPhone = smooth(.61, .87, value);
        const rightPhone = smooth(.655, .91, value);

        opacity(libraryField, smooth(.145, .39, value));
        opacity(referenceField, smooth(.56, .87, value));
        opacity(libraryImage, libraryProgress);
        libraryImage.style.transform = translate(0, 32 * (1 - libraryProgress));
        homeImages.forEach(image => { image.style.transform = translate(0, -25 * libraryProgress); });
        const detail = 1 - smooth(.08, .28, value);
        accessories.forEach(accessory => opacity(accessory, detail));
        opacity(artwork, 1 - center);
        artwork.style.visibility = center === 1 ? 'hidden' : 'visible';

        // The same central phone resolves into Lexicomp while the side phones fan out.
        gallery.style.visibility = leftPhone > 0 ? 'visible' : 'hidden';
        opacity(uptodate, leftPhone);
        uptodate.style.transform = translate(57 * (1 - leftPhone), 24 * (1 - leftPhone));
        opacity(lexicomp, center);
        opacity(conditions, rightPhone);
        conditions.style.transform = translate(-57 * (1 - rightPhone), 24 * (1 - rightPhone));

        const entering = [1, smooth(.265, .475, value), smooth(.66, .88, value)];
        const leaving = [smooth(.12, .295, value), smooth(.58, .76, value), 0];
        copies.forEach((copy, index) => {
            opacity(copy, entering[index] * (1 - leaving[index]));
            copy.style.transform = translate(0, 33 * (1 - entering[index]) - 28 * leaving[index]);
        });

        updateScene(value > .71 ? 2 : value > .305 ? 1 : 0);
    }

    function scrollProgress() {
        return clamp((scrollY - dimensions.start) / dimensions.travel);
    }

    function animateScroll(now) {
        frame = 0;
        const target = scrollProgress();
        const amount = 1 - Math.exp(-Math.max(1, now - (lastFrame || now - 16)) / 30);
        progress = Math.abs(progress - target) < .0006 ? target : mix(progress, target, amount);
        lastFrame = progress === target ? 0 : now;
        render(progress);
        if (lastFrame) frame = requestAnimationFrame(animateScroll);
    }

    function syncScroll() {
        if (!frame) frame = requestAnimationFrame(animateScroll);
    }

    function jump(hash, behavior) {
        const index = scenes.findIndex(scene => `#${scene.id}` === hash);
        if (index < 0) return false;
        const positions = [0, .47, .96];
        scrollTo({ top: Math.max(0, dimensions.start + dimensions.travel * positions[index]), behavior });
        return true;
    }

    function playEntrance() {
        artwork.style.setProperty('--home-entrance-y', `-${dimensions.height * 1.3}px`);
        story.classList.add('is-entering');
    }

    controls.addEventListener('click', event => {
        const link = event.target.closest('a');
        if (!link || event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        if (!jump(link.hash, 'smooth')) return;
        event.preventDefault();
        history.replaceState(history.state, '', link.hash);
    });
    addEventListener('scroll', syncScroll, { passive: true });
    addEventListener('resize', () => {
        measure();
        render(progress);
        syncScroll();
    }, { passive: true });
    addEventListener('hashchange', () => jump(location.hash, 'instant'));

    document.documentElement.classList.add('home-motion');
    story.classList.add('is-animated');
    controls.hidden = false;
    stage.append(artwork);
    measure();
    progress = scrollProgress();
    render(progress);
    (document.fonts?.ready || Promise.resolve()).then(() => {
        measure();
        jump(location.hash, 'instant');
        progress = scrollProgress();
        render(progress);
        if ((!location.hash || location.hash === '#overview') && progress === 0) playEntrance();
    });
})();
