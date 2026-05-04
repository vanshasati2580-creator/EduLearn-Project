
document.addEventListener('DOMContentLoaded',() => {
  // --- lightweight analytics emitter ---
  const analytics = {
    emit: (event, payload={}) => {
      try{
        if(Array.isArray(window.dataLayer)){
          window.dataLayer.push({ event, ...payload });
        } else {
          // fallback for local/dev without a tag manager
          console.log('[analytics]', event, payload);
        }
      }catch(e){ /* ignore */ }
    }
  };
  const getCourseId = () => {
    const m = (window.location.pathname || '').match(/\/course\/(\d+)/);
    return m ? parseInt(m[1], 10) : null;
  };
  const getArea = (el) => {
    if(!el) return 'unknown';
    if(el.closest('.js-sticky-cta')) return 'sticky';
    if(el.closest('.course-hero')) return 'hero';
    if(el.closest('.col-lg-4')) return 'sidebar';
    return 'unknown';
  };
  const getVariant = () => {
    let v = localStorage.getItem('cta_variant');
    if(!v){ v = Math.random() < 0.5 ? 'A' : 'B'; localStorage.setItem('cta_variant', v); }
    return v;
  };
  // Intersection-driven reveal
  const els = document.querySelectorAll('.fade-up, .pop-card, .slide-in-left, .slide-in-right, .zoom-in');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if(e.isIntersecting){
        e.target.style.animationPlayState = 'running';
        e.target.classList.add('revealed');
        obs.unobserve(e.target);
      }
    });
  },{threshold:.12});
  els.forEach(el => {
    el.style.animationPlayState = 'paused';
    obs.observe(el);
  });

  // Button ripple effect + shine enhancement
  // Applies to any .btn (opt-out with .no-ripple). Uses CSS animation 'ripple'.
  const enableRipple = () => {
    // Delegate to the document to cover dynamically added buttons
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn');
      if(!btn || btn.classList.contains('no-ripple')) return;
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 1.25;
      const x = (e.clientX ?? (rect.left + rect.width/2)) - rect.left - size/2;
      const y = (e.clientY ?? (rect.top + rect.height/2)) - rect.top - size/2;
      const rip = document.createElement('span');
      rip.className = 'ripple';
      rip.style.width = rip.style.height = size + 'px';
      rip.style.left = x + 'px';
      rip.style.top = y + 'px';
      btn.appendChild(rip);
      rip.addEventListener('animationend', () => rip.remove());
    }, { passive: true });
  };
  enableRipple();
  // NOTE: previous 'btn-shine' sweep effect disabled to avoid conflict with spotlight overlay
  // If needed for specific buttons, add 'btn-shine' class manually in templates.

  // Spotlight hover tracking for buttons (SpotlightCard-like)
  // Updates CSS variables --spx/--spy so CSS can render a radial highlight that follows the pointer
  (function(){
    const prefersReducedMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    const setSpot = (btn, x, y) => {
      if(!btn) return;
      btn.style.setProperty('--spx', x);
      btn.style.setProperty('--spy', y);
    };
    const updateFromEvent = (e) => {
      if(prefersReducedMotion) return;
      const btn = e.target && e.target.closest && e.target.closest('.btn');
      if(!btn || btn.classList.contains('no-spotlight')) return;
      const r = btn.getBoundingClientRect();
      const x = (e.clientX - r.left) + 'px';
      const y = (e.clientY - r.top) + 'px';
      setSpot(btn, x, y);
    };
    document.addEventListener('pointermove', updateFromEvent, { passive: true });
    document.addEventListener('pointerdown', updateFromEvent, { passive: true });
    // Reset when pointer leaves a button
    document.addEventListener('pointerout', (e) => {
      const btn = e.target && e.target.closest && e.target.closest('.btn');
      if(!btn) return;
      const nextBtn = e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('.btn');
      if(nextBtn === btn) return; // still within same button
      setSpot(btn, '-999px', '-999px');
    }, { passive: true });
    // Keyboard accessibility: center the spotlight on focus
    document.addEventListener('focusin', (e) => {
      const btn = e.target && e.target.closest && e.target.closest('.btn');
      if(!btn || btn.classList.contains('no-spotlight')) return;
      setSpot(btn, '50%', '50%');
    });
    document.addEventListener('focusout', (e) => {
      const btn = e.target && e.target.closest && e.target.closest('.btn');
      if(!btn) return;
      setSpot(btn, '-999px', '-999px');
    });
  })();

  // Scroll progress bar
  (function(){
    const bar = document.createElement('div');
    bar.className = 'scroll-progress';
    document.body.appendChild(bar);
    let ticking = false;
    const update = () => {
      const h = document.documentElement;
      const max = Math.max(0, h.scrollHeight - window.innerHeight);
      const y = window.scrollY || h.scrollTop || 0;
      const p = max > 0 ? y / max : 0;
      bar.style.transform = `scaleX(${Math.min(1, Math.max(0, p))})`;
      ticking = false;
    };
    const onScroll = () => {
      if(!ticking){ requestAnimationFrame(update); ticking = true; }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', update);
    update();
  })();

  // Animate dashboard progress bars
  document.querySelectorAll('.progress').forEach(p => {
    const pct = parseInt(p.getAttribute('data-target') || '0', 10);
    const bar = p.querySelector('.progress-bar');
    setTimeout(()=>{ if(bar) bar.style.width = pct + '%'; }, 200);
    const pctEl = p.parentElement.querySelector('.pct');
    if(pctEl){
      let cur=0;
      const step = () => {
        if(cur >= pct) return;
        cur += 2;
        pctEl.textContent = Math.min(cur, pct);
        requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }
  });

  // Quiz progress bar reacts to selections
  const steps = document.querySelectorAll('#quiz-form .step');
  const seen = new Set();
  steps.forEach(s => {
    s.addEventListener('change', e => {
      const name = e.target.name;
      seen.add(name);
      const pct = Math.round((seen.size / (new Set([...steps].map(x=>x.name)).size)) * 100);
      const bar = document.querySelector('.progress-bar');
      if(bar) bar.style.width = pct + '%';
    });
  });

  // Password visibility toggle
  document.querySelectorAll('.toggle-password').forEach(btn => {
    const targetSel = btn.getAttribute('data-target');
    const input = targetSel ? document.querySelector(targetSel) : null;
    if(input && input.id){ btn.setAttribute('aria-controls', input.id); }
    btn.setAttribute('aria-pressed', 'false');
    btn.setAttribute('aria-label', 'Show password');
    btn.addEventListener('click', () => {
      const sel = btn.getAttribute('data-target');
      const field = sel ? document.querySelector(sel) : null;
      if(!field) return;
      const type = field.getAttribute('type') === 'password' ? 'text' : 'password';
      field.setAttribute('type', type);
      const showing = type === 'text';
      btn.textContent = showing ? 'Hide' : 'Show';
      btn.setAttribute('aria-pressed', showing ? 'true' : 'false');
      btn.setAttribute('aria-label', showing ? 'Hide password' : 'Show password');
      analytics.emit('login_toggle_password', { showing });
    });
  });

  // Theme toggle (dark <-> light) with persistence
  const applyTheme = (theme) => {
    if(theme === 'light'){
      document.body.setAttribute('data-theme','light');
    } else {
      document.body.removeAttribute('data-theme');
    }
    document.querySelectorAll('.theme-toggle').forEach(b=>{
      const isLight = document.body.getAttribute('data-theme') === 'light';
      b.textContent = isLight ? '🌙' : '☀️';
      b.classList.toggle('btn-outline-light', !isLight);
      b.classList.toggle('btn-outline-dark', isLight);
      b.setAttribute('aria-label', isLight ? 'Switch to dark mode' : 'Switch to light mode');
    });
  };
  const storedTheme = localStorage.getItem('theme');
  const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  applyTheme(storedTheme || (prefersLight ? 'light' : 'dark'));
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const next = document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', next);
      applyTheme(next);
    });
  });

  // Floating header on scroll
  const header = document.querySelector('.navbar.nav-glass');
  if(header){
    const threshold = 24;
    let ticking = false;
    const applyHeader = () => {
      const shouldFloat = window.scrollY > threshold;
      header.classList.toggle('is-floating', shouldFloat);
      ticking = false;
    };
    window.addEventListener('scroll', () => {
      if(!ticking){
        requestAnimationFrame(applyHeader);
        ticking = true;
      }
    }, { passive: true });
    applyHeader();
  }

  // Checkout input formatting
  const onlyDigits = (v) => (v || '').replace(/\D+/g, '');
  const ccNumber = document.querySelector('.cc-number');
  if(ccNumber){
    ccNumber.addEventListener('input', (e) => {
      let v = onlyDigits(e.target.value).slice(0, 19);
      // group as 4-4-4-4-3
      const groups = [];
      while(v.length){ groups.push(v.slice(0,4)); v = v.slice(4); }
      e.target.value = groups.join(' ');
    });
  }
  const ccExp = document.querySelector('.cc-exp');
  if(ccExp){
    ccExp.addEventListener('input', (e) => {
      let v = onlyDigits(e.target.value).slice(0,4);
      if(v.length >= 3){ v = v.slice(0,2) + '/' + v.slice(2); }
      e.target.value = v;
    });
  }
  const ccCvv = document.querySelector('.cc-cvv');
  if(ccCvv){
    ccCvv.addEventListener('input', (e) => {
      e.target.value = onlyDigits(e.target.value).slice(0,4);
    });
  }

  // Sticky CTA visibility on course pages
  const hero = document.getElementById('course-hero');
  const sticky = document.querySelector('.js-sticky-cta');
  if(hero && sticky){
    // assign A/B variant
    const variant = getVariant();
    sticky.setAttribute('data-variant', variant);
    analytics.emit('sticky_cta_assign', { courseId: getCourseId(), variant });

    const onObserve = (entries) => {
      entries.forEach(entry => {
        const show = !entry.isIntersecting;
        sticky.classList.toggle('show', show);
        sticky.setAttribute('aria-hidden', show ? 'false' : 'true');
        if(typeof onObserve._lastShow === 'undefined' || onObserve._lastShow !== show){
          onObserve._lastShow = show;
          analytics.emit('sticky_cta_visibility', { courseId: getCourseId(), variant, show });
        }
      });
    };
    const stObs = new IntersectionObserver(onObserve, { root: null, threshold: 0, rootMargin: '-64px 0px 0px 0px' });
    stObs.observe(hero);
    // Prevent content overlap: pad bottom equal to CTA height
    const setPad = () => { document.body.style.paddingBottom = `${sticky.offsetHeight}px`; };
    setPad();
    window.addEventListener('resize', setPad);
  }

  // Share button handler
  document.querySelectorAll('.js-share').forEach(btn => {
    btn.addEventListener('click', async () => {
      const url = btn.getAttribute('data-url') || window.location.href;
      const title = document.title;
      if(navigator.share){
        try{ await navigator.share({ title, url }); }catch(err){ /* user canceled */ }
        analytics.emit('share_used', { method: 'webshare', courseId: getCourseId(), area: getArea(btn) });
      } else if(navigator.clipboard && window.isSecureContext){
        try{
          await navigator.clipboard.writeText(url);
          const prev = btn.textContent;
          btn.textContent = 'Copied!';
          setTimeout(()=>{ btn.textContent = prev; }, 1000);
          analytics.emit('share_used', { method: 'clipboard', courseId: getCourseId(), area: getArea(btn) });
        }catch(err){ /* ignore */ }
      } else {
        window.prompt('Copy this link:', url);
        analytics.emit('share_used', { method: 'prompt', courseId: getCourseId(), area: getArea(btn) });
      }
    });
  });

  // Coupon Apply handlers
  const attachCoupon = (btn) => {
    const base = btn.getAttribute('data-checkout-base') || '';
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const group = btn.closest('.input-group');
      let input = group ? group.querySelector('input') : document.querySelector('.coupon-input');
      const code = (input && input.value || '').trim();
      const target = code ? `${base}?code=${encodeURIComponent(code)}` : base;
      analytics.emit('coupon_apply', { courseId: getCourseId(), area: getArea(btn), hasCode: !!code });
      if(target){ window.location.href = target; }
    });
  };
  document.querySelectorAll('.js-apply-coupon').forEach(attachCoupon);
  // Enter key support for coupon inputs
  document.querySelectorAll('.coupon-input, .input-group input[aria-label="Coupon code"]').forEach(inp => {
    inp.addEventListener('keydown', (e) => {
      if(e.key === 'Enter'){
        e.preventDefault();
        const btn = inp.closest('.input-group')?.querySelector('.js-apply-coupon');
        if(btn) btn.click();
      }
    });
  });

  // Reviews rating bars animation
  document.querySelectorAll('.rating-bar').forEach(wrapper => {
    const pct = parseInt(wrapper.getAttribute('data-pct') || '0', 10);
    const fill = wrapper.querySelector('.progress-animated');
    if(fill){ setTimeout(() => { fill.style.width = pct + '%'; }, 200); }
  });

  // Fix Unsplash page links used as <img src> by rewriting to direct CDN with fallbacks
  // Example broken: https://unsplash.com/photos/...-JKUTrJ4vK00
  // Prefer: https://images.unsplash.com/photo-JKUTrJ4vK00?q=80&w=<w>&h=<h>&fit=crop&auto=format
  // Fallback: https://source.unsplash.com/JKUTrJ4vK00/<w>x<h>; then a placeholder
  (function(){
    const pickSize = (img) => {
      if(img.closest('.course-hero') || img.closest('.hero-card')) return [1200, 675];
      if(img.closest('.ratio-16x9')) return [800, 450];
      if(img.closest('.ratio-4x3')) return [800, 600];
      if(img.closest('.ratio-1x1')) return [800, 800];
      return [800, 450];
    };
    const buildImagesUnsplash = (id, w, h) => `https://images.unsplash.com/photo-${id}?q=80&w=${w}&h=${h}&fit=crop&auto=format`;
    const buildSourceUnsplash = (id, w, h) => `https://source.unsplash.com/${id}/${w}x${h}`;
    const debug = localStorage.getItem('img_fix_debug') === '1';
    const log = (...a) => { if(debug) try{ console.debug('[unsplash-fix]', ...a); }catch(e){} };
    const isUnsplashPage = (u) => {
      const host = (u.hostname || '').toLowerCase();
      // Only treat unsplash.com/www.unsplash.com "page" hosts as rewritable sources.
      return host === 'unsplash.com' || host === 'www.unsplash.com';
    };
    const extractId = (u) => {
      const parts = (u.pathname || '').split('/').filter(Boolean);
      // Handle /photos/<slug-or-id> and /photos/<slug-or-id>/download
      let slug = parts[parts.length - 1] || '';
      if(['download','likes','comments'].includes((slug || '').toLowerCase())){
        slug = parts[parts.length - 2] || '';
      }
      const cand = (slug.split('-').pop() || '').replace(/[^A-Za-z0-9_-]/g,'');
      return cand && cand.length >= 8 ? cand : null;
    };
    const trySet = (img, url) => { if(img.getAttribute('src') !== url) img.setAttribute('src', url); };
    document.querySelectorAll('img').forEach(img => {
      const src = img.getAttribute('src') || '';
      if(!src) return;
      let u;
      try{ u = new URL(src, window.location.href); }catch(e){ return; }
      if(!isUnsplashPage(u)) return;
      const id = extractId(u);
      if(!id) return;
      const [w,h] = pickSize(img);
      const primary = buildImagesUnsplash(id, w, h);
      const secondary = buildSourceUnsplash(id, w, h);
      log('rewrite', { src, id, w, h, primary, secondary });
      const onErr = () => {
        // If primary fails, try secondary once; then placeholder
        if(!img.dataset.triedSecondary){
          img.dataset.triedSecondary = '1';
          log('error', { step: 'primary_failed', current: img.getAttribute('src'), next: secondary });
          trySet(img, secondary);
        } else if(!img.dataset.triedPlaceholder){
          img.dataset.triedPlaceholder = '1';
          const ph = `https://placehold.co/${w}x${h}?text=Image+Unavailable`;
          log('error', { step: 'secondary_failed', current: img.getAttribute('src'), next: ph });
          trySet(img, ph);
        }
      };
      img.addEventListener('error', onErr);
      trySet(img, primary);
      img.setAttribute('data-src-fixed', 'unsplash');
    });
  })();

  // ---------------- Login page enhancements ----------------
  // Scope strictly to the login page to avoid affecting the register page
  const authForm = document.querySelector('.auth-section form');
  const isLoginPage = !!document.getElementById('login-password') || /\/login(?:\/)?$/i.test(window.location.pathname);
  const loginForm = isLoginPage ? authForm : null;
  if(loginForm){
    analytics.emit('login_view', {});
    const authCard = loginForm.closest('.auth-card') || loginForm;
    const emailInput = loginForm.querySelector('input[type="email"]');
    const pwInput = loginForm.querySelector('input[type="password"], input#login-password');

    // Caps Lock hint for password
    if(pwInput){
      const group = pwInput.closest('.input-group');
      if(group){
        const hint = document.createElement('div');
        hint.className = 'form-text caps-hint d-none';
        hint.setAttribute('role','status');
        hint.setAttribute('aria-live','polite');
        hint.setAttribute('aria-hidden','true');
        hint.textContent = 'Caps Lock is ON';
        group.parentElement.insertBefore(hint, group.nextSibling);
        let lastOn = false;
        const setCaps = (on) => {
          if(on === lastOn) return;
          lastOn = on;
          hint.classList.toggle('d-none', !on);
          hint.setAttribute('aria-hidden', on ? 'false' : 'true');
          analytics.emit('login_capslock', { on });
        };
        const updateFromEvent = (e) => {
          const on = e.getModifierState && e.getModifierState('CapsLock');
          if(typeof on === 'boolean') setCaps(on);
        };
        pwInput.addEventListener('keydown', updateFromEvent);
        pwInput.addEventListener('keyup', updateFromEvent);
        pwInput.addEventListener('focus', (e)=> updateFromEvent(e));
        pwInput.addEventListener('blur', () => setCaps(false));
      }
    }

    // Demo autofill pills disabled per request

    // Submit loading state + prevent double submit
    const submitBtn = loginForm.querySelector('button[type="submit"], .btn.btn-primary');
    let submitted = false;
    if(submitBtn){
      loginForm.addEventListener('submit', (e)=>{
        if(submitted){ e.preventDefault(); return; }
        submitted = true;
        submitBtn.classList.add('is-loading');
        submitBtn.setAttribute('aria-busy','true');
        submitBtn.disabled = true;
        const hasEmail = !!(emailInput && emailInput.value.trim());
        const domain = (emailInput?.value.split('@')[1] || '').toLowerCase() || null;
        const hasPassword = !!(pwInput && pwInput.value);
        analytics.emit('login_submit', { hasEmail, emailDomain: domain || null, hasPassword });
      });
    }

    // Forgot password analytics
    const forgot = Array.from(loginForm.querySelectorAll('a')).find(a => (a.textContent || '').trim().toLowerCase().includes('forgot'));
    if(forgot){
      forgot.addEventListener('click', ()=> analytics.emit('login_forgot_password', {}));
    }

    // Error shake on invalid login (via toast)
    const dangerToast = document.querySelector('.toast.show.text-bg-danger .toast-body');
    if(dangerToast && /Invalid credentials/i.test(dangerToast.textContent || '')){
      analytics.emit('login_error', { reason: 'invalid_credentials' });
      if(authCard){
        authCard.classList.add('shake');
        authCard.addEventListener('animationend', ()=> authCard.classList.remove('shake'), { once:true });
      }
      if(pwInput){ pwInput.setAttribute('aria-invalid','true'); }
    }
  }

  // CTA clicks (buy now) to checkout
  const variantFor = () => (document.querySelector('.js-sticky-cta')?.getAttribute('data-variant') || null);
  document.querySelectorAll('a[href*="/checkout/"]').forEach(a => {
    a.addEventListener('click', () => {
      analytics.emit('cta_click', { courseId: getCourseId(), area: getArea(a), variant: variantFor() });
    });
  });

  // Add to cart clicks
  document.querySelectorAll('form[action*="/cart/add/"]').forEach(f => {
    f.addEventListener('submit', () => {
      analytics.emit('add_to_cart', { courseId: getCourseId(), area: getArea(f), variant: variantFor() });
    });
  });

  // Wishlist toggle
  document.querySelectorAll('form[action*="/favorite/"]').forEach(f => {
    f.addEventListener('submit', () => {
      analytics.emit('wishlist_toggle', { courseId: getCourseId(), area: getArea(f) });
    });
  });
  
  // ---------------- Homepage analytics & UX ----------------
  // Ensure hero has data-hero attribute so styles/effects apply without template edits
  const heroHeader = document.querySelector('header.hero');
  if(heroHeader && !heroHeader.hasAttribute('data-hero')){
    heroHeader.setAttribute('data-hero','');
  }
  const heroEl = document.querySelector('header.hero[data-hero]');
  const isHome = !!heroEl;
  if(isHome){
    // A/B assign for hero layout (no UI change yet; for analytics only)
    let hv = localStorage.getItem('hero_variant');
    if(!hv){ hv = Math.random() < 0.5 ? 'A' : 'B'; localStorage.setItem('hero_variant', hv); }
    heroEl.setAttribute('data-variant', hv);
    analytics.emit('hero_assign', { variant: hv });

    // Parallax for hero content (respects reduced motion)
    const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const leftCol = heroEl.querySelector('.js-hero-left');
    const rightCol = heroEl.querySelector('.js-hero-right');
    if(!reduceMotion && (leftCol || rightCol)){
      let ticking = false;
      const applyParallax = () => {
        const rect = heroEl.getBoundingClientRect();
        // t: 0 when hero is below viewport, 1 when fully in view
        const viewH = window.innerHeight || document.documentElement.clientHeight;
        const tRaw = 1 - Math.max(0, rect.top) / (viewH + rect.height);
        const t = Math.min(1, Math.max(0, tRaw));
        const leftY = -10 * t;   // move up
        const rightY = 10 * t;   // move down
        if(leftCol){ leftCol.style.transform = `translateY(${leftY}px)`; }
        if(rightCol){ rightCol.style.transform = `translateY(${rightY}px)`; }
        ticking = false;
      };
      const onScroll = () => {
        if(!ticking){ requestAnimationFrame(applyParallax); ticking = true; }
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', applyParallax);
      applyParallax();
    }

    // Section impressions
    const sections = ['continue','trending','categories','new','instructors','testimonials','newsletter','faq']
      .map(id => document.getElementById(id))
      .filter(Boolean);
    const secObs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if(e.isIntersecting && !e.target.dataset.seen){
          e.target.dataset.seen = '1';
          analytics.emit('section_view', { id: e.target.id });
          secObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.2 });
    sections.forEach(s => secObs.observe(s));

    // Search submit (hero + navbar)
    document.querySelectorAll('form[action*="/search"]').forEach(form => {
      form.addEventListener('submit', () => {
        const q = (new FormData(form).get('q') || '').toString();
        const area = form.closest('header.hero') ? 'hero' : form.closest('.navbar') ? 'navbar' : 'content';
        analytics.emit('search_submit', { area, hasQuery: !!q, qLen: q.length });
      });
    });

    // Popular query chips
    document.querySelectorAll('.js-popular-query').forEach(a => {
      a.addEventListener('click', () => {
        const term = a.getAttribute('data-q') || a.textContent.trim();
        analytics.emit('popular_query_click', { term, area: 'hero' });
      });
    });

    // Category chips
    document.querySelectorAll('.js-category').forEach(a => {
      a.addEventListener('click', () => {
        const cat = a.getAttribute('data-cat') || a.textContent.trim();
        analytics.emit('category_click', { category: cat });
      });
    });

    // Course card title clicks
    document.querySelectorAll('.js-course-link').forEach(a => {
      a.addEventListener('click', () => {
        const href = a.getAttribute('href') || '';
        const m = href.match(/\/course\/(\d+)/);
        const cid = m ? parseInt(m[1], 10) : null;
        const sec = a.closest('#trending') ? 'trending' : a.closest('#new') ? 'new' : 'unknown';
        analytics.emit('course_card_click', { courseId: cid, section: sec });
      });
    });

    // Hero CTAs
    document.querySelectorAll('.js-hero-cta').forEach(a => {
      a.addEventListener('click', () => {
        const label = a.textContent.trim();
        analytics.emit('hero_cta_click', { variant: hv, label });
      });
    });

    // Magnetic hover effect disabled to keep hero buttons/static controls stationary

    // Newsletter mock submit
    const nlForm = document.querySelector('.js-newsletter');
    if(nlForm){
      nlForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = (new FormData(nlForm).get('email') || '').toString();
        const domain = (email.split('@')[1] || '').toLowerCase();
        analytics.emit('newsletter_subscribe', { emailDomain: domain || null });
        const ok = document.querySelector('.js-newsletter-success');
        if(ok){ ok.classList.remove('d-none'); setTimeout(()=> ok.classList.add('d-none'), 2500); }
        nlForm.reset();
      });
    }
  }
});