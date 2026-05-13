/** Mark Studio — Early appointment page detection
 *  Runs in head (via assets_frontend_minimal) to prevent white flash.
 *  Adds .mk-appointment-page to <html> before page renders.
 */
(function () {
    var path = window.location.pathname.replace(/^\/en/, '');
    if (path.indexOf('/appointment') === 0) {
        document.documentElement.classList.add('mk-appointment-page');
    }
})();
