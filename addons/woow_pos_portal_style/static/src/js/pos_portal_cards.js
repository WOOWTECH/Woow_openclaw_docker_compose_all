/**
 * Woow POS Portal Style
 * Replaces POS and Kitchen Display icons with unique flat-style SVGs
 * and adds descriptive text under each card title.
 *
 * Works on both portal (/my) and backend pages via MutationObserver.
 */
(function () {
    'use strict';

    var CARD_CONFIG = {
        pos: {
            match: function (text) {
                return text.includes('銷售點') && !text.includes('廚房');
            },
            iconUrl: '/woow_pos_portal_style/static/src/img/icon_pos.svg',
            description: '管理您的門市銷售與收款',
            cssClass: 'wpu-card-pos'
        },
        kitchen: {
            match: function (text) {
                return text.includes('廚房顯示') || text.includes('廚房螢幕');
            },
            iconUrl: '/woow_pos_portal_style/static/src/img/icon_kitchen.svg',
            description: '即時追蹤備餐與出餐進度',
            cssClass: 'wpu-card-kitchen'
        }
    };

    // Selectors that may contain module card titles
    var TITLE_SELECTORS = 'h3, h4, h5, .card-title, strong, .o_kanban_record_title, .fw-bold';
    // Selectors for card containers
    var CARD_SELECTORS = '.o_portal_index_card, .wpu-module-card, .o_kanban_record, .list-group-item, [class*="card"]';

    /**
     * Walk up from a title element to find the closest card container.
     */
    function findCardContainer(titleEl) {
        var el = titleEl.parentElement;
        while (el && el !== document.body) {
            if (el.matches && el.matches(CARD_SELECTORS)) return el;
            // Also match <a> or <div> that wraps a card row
            if (el.matches && el.matches('a, div.row, div.d-flex, div.list-group-item, tr')) return el;
            el = el.parentElement;
        }
        return titleEl.parentElement;
    }

    /**
     * Apply icon replacement and description to a card.
     */
    function applyCustomization(card, config) {
        if (card.dataset.wpuPosStyled) return;
        card.dataset.wpuPosStyled = '1';
        card.classList.add('wpu-customized-card', config.cssClass);

        // Replace icon image
        var img = card.querySelector('img');
        if (img) {
            img.src = config.iconUrl;
            img.alt = config.description;
            img.classList.add('wpu-custom-icon', 'wpu-icon-' + config.cssClass.replace('wpu-card-', ''));
        }

        // Find and update the subtitle / description element
        var candidates = card.querySelectorAll('p, small, span, .text-muted');
        var updated = false;
        for (var i = 0; i < candidates.length; i++) {
            var el = candidates[i];
            var elText = el.textContent.trim();
            // Replace "餐廳" or empty subtitle with the description
            if (elText === '餐廳' || elText === '' || elText === '餐飲') {
                el.textContent = config.description;
                el.classList.add('wpu-card-description');
                updated = true;
                break;
            }
        }

        // If no subtitle was found/updated, insert one after the title
        if (!updated) {
            var titleEl = card.querySelector(TITLE_SELECTORS);
            if (titleEl) {
                var desc = document.createElement('p');
                desc.className = 'wpu-card-description mb-0';
                desc.textContent = config.description;
                titleEl.parentNode.insertBefore(desc, titleEl.nextSibling);
            }
        }
    }

    /**
     * Scan the page for POS / Kitchen Display cards and customize them.
     */
    function scanAndCustomize() {
        var allTitles = document.querySelectorAll(TITLE_SELECTORS);
        for (var i = 0; i < allTitles.length; i++) {
            var titleEl = allTitles[i];
            var text = titleEl.textContent.trim();

            for (var key in CARD_CONFIG) {
                if (CARD_CONFIG[key].match(text)) {
                    var card = findCardContainer(titleEl);
                    if (card && !card.dataset.wpuPosStyled) {
                        applyCustomization(card, CARD_CONFIG[key]);
                    }
                }
            }
        }
    }

    // --- Execution ---

    // Initial scan
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scanAndCustomize);
    } else {
        scanAndCustomize();
    }

    // Watch for dynamically rendered content (OWL/SPA)
    var debounceTimer;
    var observer = new MutationObserver(function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(scanAndCustomize, 300);
    });

    function startObserver() {
        var target = document.body || document.documentElement;
        if (target) {
            observer.observe(target, { childList: true, subtree: true });
        }
    }

    if (document.body) {
        startObserver();
    } else {
        document.addEventListener('DOMContentLoaded', startObserver);
    }
})();
