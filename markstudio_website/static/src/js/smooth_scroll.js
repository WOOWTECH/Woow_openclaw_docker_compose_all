/** Mark Studio — Smooth scroll for anchor navigation
 *  Handles /#section links from Odoo navbar which may intercept default behavior
 */
document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
        var link = e.target.closest('a[href*="/#"]');
        if (!link) return;

        var href = link.getAttribute('href');
        var hash = href.indexOf('#') !== -1 ? href.substring(href.indexOf('#')) : null;
        if (!hash) return;

        var target = document.querySelector(hash);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
            if (history.pushState) {
                history.pushState(null, null, hash);
            }
        }
    });
});
