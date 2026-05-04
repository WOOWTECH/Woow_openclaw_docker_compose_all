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
