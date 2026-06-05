/** Mark Studio — Smooth scroll for anchor navigation
 *  Handles Odoo's /en prefix rewriting and deferred asset loading
 */
(function () {
    function scrollToHash(hash) {
        var el = document.querySelector(hash);
        if (!el) return false;
        var top = el.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({ top: top, behavior: 'smooth' });
        return true;
    }

    // On page load: scroll to hash if present (retry for Odoo lazy rendering)
    function onReady() {
        if (!window.location.hash) return;
        var hash = window.location.hash;
        var attempts = 0;
        var timer = setInterval(function () {
            if (scrollToHash(hash) || ++attempts > 10) clearInterval(timer);
        }, 200);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onReady);
    } else {
        onReady();
    }

    // Intercept anchor clicks before Odoo's router
    document.addEventListener('click', function (e) {
        var link = e.target.closest('a');
        if (!link) return;
        var href = link.getAttribute('href');
        if (!href) return;
        var m = href.match(/#([a-zA-Z][\w-]*)/);
        if (!m) return;
        var hash = '#' + m[1];
        var el = document.querySelector(hash);
        if (!el) return;
        e.preventDefault();
        e.stopPropagation();
        scrollToHash(hash);
        history.pushState(null, null, hash);
    }, true);
})();

/** Mark Studio — Appointment page class injection
 *  Adds .mk-appointment-page to body on /appointment/* URLs
 *  so Retrodandy CSS overrides can target the page.
 */
(function () {
    var path = window.location.pathname.replace(/^\/en/, '');
    if (path.indexOf('/appointment') === 0) {
        document.body.classList.add('mk-appointment-page');
    }
})();

/** Mark Studio — Enhance appointment detail card
 *  Restructures /appointment/N page to match homepage booking card layout.
 */
(function () {
    var path = window.location.pathname.replace(/^\/en/, '');
    // Only on /appointment/N (not /appointment, /appointment/N/schedule, /appointment/N/book)
    if (!/^\/appointment\/\d+$/.test(path)) return;

    function enhance() {
        var card = document.querySelector('.card.shadow');
        if (!card) return;
        var body = card.querySelector('.card-body');
        if (!body) return;

        // Add mk-appt-detail class for CSS targeting
        card.classList.add('mk-appt-detail');

        // Create image div
        var imgDiv = document.createElement('div');
        imgDiv.className = 'mk-appt-detail-img';
        card.insertBefore(imgDiv, body);

        // Replace badge text and add meta info
        var badgeContainer = body.querySelector('.mb-3');
        if (badgeContainer) {
            badgeContainer.innerHTML =
                '<span class="mk-appt-meta"><i class="fa fa-clock-o"></i> 60 分鐘</span>' +
                '<span class="mk-appt-meta"><i class="fa fa-user"></i> 馬克</span>' +
                '<span class="mk-appt-meta"><i class="fa fa-tag"></i> 免費體驗</span>';
            badgeContainer.className = 'mk-appt-meta-row';
        }

        // Add description before button
        var btn = body.querySelector('.btn');
        if (btn) {
            var desc = document.createElement('p');
            desc.className = 'mk-appt-desc';
            desc.textContent = '由專業教練馬克提供一對一按摩伸展服務，針對您的身體狀況量身打造最適合的療程。';
            btn.parentNode.insertBefore(desc, btn);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enhance);
    } else {
        enhance();
    }
})();

/** Mark Studio — Portal chatter dark theme enforcement
 *  Odoo 18 OWL Chatter renders inside Shadow DOM (#chatterRoot).
 *  External CSS cannot penetrate Shadow DOM boundaries.
 *  This script injects a <style> tag directly into the Shadow DOM
 *  when it's created, applying the dark theme from inside.
 */
(function () {
    var DARK_CSS = [
        '.o-mail-Chatter, .o-portal-Chatter, .o-mail-Chatter-top { background: transparent !important; }',
        '.o-mail-Composer-bg, .o-mail-Composer-actions { background: rgba(255,255,255,0.05) !important; }',
        '.o-mail-Composer-input, textarea.o-mail-Composer-bg { background: rgba(255,255,255,0.05) !important; color: #fff !important; }',
        '.o-mail-Composer-input::placeholder { color: rgba(255,255,255,0.3) !important; }',
        '.o-mail-Composer-fake { background: rgba(255,255,255,0.05) !important; }',
        '.o-mail-Composer-send { background: transparent !important; color: #fff !important; border: 2px solid #fff !important; border-radius: 0 !important; }',
        '.o-mail-Composer-send:hover { background: #fff !important; color: #000 !important; }',
        '.o-mail-PickerContent { background: #1a1a1a !important; }',
        '.o-mail-Composer .btn:not(.o-mail-Composer-send) { color: rgba(255,255,255,0.5) !important; }',
        '.o-mail-Chatter p, .o-mail-Chatter span, .o-mail-Chatter div { color: rgba(255,255,255,0.7) !important; }',
        '.o-mail-Thread { background: transparent !important; }',
        '.o-mail-Message { border-color: rgba(255,255,255,0.1) !important; }',
        '.shadow-sm { box-shadow: none !important; }',
        '.text-body { color: rgba(255,255,255,0.7) !important; }',
        '.text-muted { color: rgba(255,255,255,0.4) !important; }',
        '.border-secondary { border-color: rgba(255,255,255,0.25) !important; }',
        '.o_cc, .o_cc1, .o_cc2, .o_cc3, .o_cc4, .o_cc5 { background: transparent !important; color: rgba(255,255,255,0.7) !important; }'
    ].join('\n');

    function injectDarkTheme(shadowRoot) {
        if (shadowRoot.querySelector('#mk-dark-chatter')) return;
        var style = document.createElement('style');
        style.id = 'mk-dark-chatter';
        style.textContent = DARK_CSS;
        shadowRoot.appendChild(style);
    }

    // Poll for Shadow DOM — re-query element each cycle to avoid stale refs
    var pollInterval = setInterval(function () {
        var root = document.querySelector('#chatterRoot');
        if (!root) return;
        if (!root.shadowRoot) return;
        injectDarkTheme(root.shadowRoot);
        // Keep observing for re-renders
        try {
            var innerObserver = new MutationObserver(function () {
                injectDarkTheme(root.shadowRoot);
            });
            innerObserver.observe(root.shadowRoot, { childList: true, subtree: true });
        } catch (e) {}
        clearInterval(pollInterval);
    }, 300);

    // Stop after 60 seconds
    setTimeout(function () { clearInterval(pollInterval); }, 60000);
})();
