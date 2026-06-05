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
 *  Odoo's .o_cc1 color class sets background-color:#fff via compiled SCSS.
 *  CSS !important cannot reliably override it (specificity issue in bundled assets).
 *  This script forces transparent background on chatter OWL components.
 */
(function () {
    function fixChatterBg() {
        var chatter = document.querySelector('.o_portal_chatter') || document.querySelector('#discussion');
        if (!chatter) return;
        var els = chatter.querySelectorAll('.o_cc, .o_cc1, .o_cc2, .o_cc3, .o_cc4, .o_cc5');
        for (var i = 0; i < els.length; i++) {
            els[i].style.setProperty('background-color', 'transparent', 'important');
            els[i].style.setProperty('background', 'transparent', 'important');
            els[i].style.setProperty('color', 'rgba(255,255,255,0.7)', 'important');
        }
    }

    // Run on load and observe for OWL lazy rendering
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixChatterBg);
    } else {
        fixChatterBg();
    }

    // MutationObserver for OWL component rendering
    var observer = new MutationObserver(function () { fixChatterBg(); });
    var target = document.querySelector('#chatterRoot') || document.querySelector('.o_portal_chatter');
    if (target) {
        observer.observe(target, { childList: true, subtree: true });
    } else {
        // Wait for DOM then observe
        document.addEventListener('DOMContentLoaded', function () {
            var t = document.querySelector('#chatterRoot') || document.querySelector('.o_portal_chatter');
            if (t) observer.observe(t, { childList: true, subtree: true });
        });
    }
})();
