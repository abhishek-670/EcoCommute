(function () {
    'use strict';

    function classText(el) {
        if (!el) {
            return '';
        }
        if (typeof el.className === 'string') {
            return el.className;
        }
        return (el.getAttribute && el.getAttribute('class')) || '';
    }

    function hasToken(el, token) {
        return classText(el).indexOf(token) !== -1;
    }

    function isReducedMotion() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    function isButtonLikeAnchor(anchor) {
        var cls = classText(anchor);
        return cls.indexOf('btn') !== -1 || cls.indexOf('bg-') !== -1 || cls.indexOf('shadow') !== -1;
    }

    function applyPageEnter(reduceMotion) {
        var page = document.body;
        if (!page || !page.classList.contains('ui-page-enter')) {
            return;
        }

        if (reduceMotion) {
            page.classList.add('ui-page-loaded');
            return;
        }

        requestAnimationFrame(function () {
            page.classList.add('ui-page-loaded');
        });
    }

    function applyButtonHover() {
        var controls = document.querySelectorAll('button, input[type="submit"], input[type="button"], a, .btn');
        controls.forEach(function (el) {
            if (el.classList.contains('ui-btn-hover') || el.classList.contains('btn-hover')) {
                return;
            }
            if (hasToken(el, 'hover:-translate-y') || hasToken(el, 'hover:scale') || hasToken(el, 'btn-link')) {
                return;
            }
            if (el.tagName === 'A' && !isButtonLikeAnchor(el)) {
                return;
            }
            if (el.disabled || el.getAttribute('aria-disabled') === 'true') {
                return;
            }
            el.classList.add('ui-btn-hover');
        });
    }

    function applyCardHover() {
        var cards = document.querySelectorAll(
            '[data-animate-card], .card, .stat-card, .passenger-card, .bg-white.rounded-lg, .bg-white.rounded-xl, .bg-white.rounded-2xl'
        );

        cards.forEach(function (card) {
            if (card.classList.contains('ui-card-hover') || card.classList.contains('btn-hover')) {
                return;
            }
            if (card.closest('nav, table, thead, tbody, tr')) {
                return;
            }
            card.classList.add('ui-card-hover');
        });
    }

    function applyIconHover() {
        var icons = document.querySelectorAll('[data-animate-icon], a i, a svg, button i, button svg, .btn i, .btn svg');
        icons.forEach(function (icon) {
            if (icon.classList.contains('ui-icon-hover')) {
                return;
            }
            icon.classList.add('ui-icon-hover');
        });
    }

    function collectRevealTargets() {
        var targets = [];

        var explicitTargets = document.querySelectorAll('[data-animate-section], .ui-reveal');
        explicitTargets.forEach(function (el) {
            el.classList.add('ui-reveal');
            targets.push(el);
        });

        var hasCustomReveal = document.querySelector('.scroll-reveal') !== null;
        if (!hasCustomReveal) {
            var genericTargets = document.querySelectorAll(
                'section, .card, .stat-card, .passenger-card, .bg-white.rounded-lg, .bg-white.rounded-xl, .bg-white.rounded-2xl'
            );
            genericTargets.forEach(function (el) {
                if (el.classList.contains('scroll-reveal') || el.classList.contains('ui-reveal')) {
                    return;
                }
                el.classList.add('ui-reveal');
                targets.push(el);
            });
        }

        return targets;
    }

    function applyRevealObserver(reduceMotion) {
        var targets = collectRevealTargets();
        if (!targets.length) {
            return;
        }

        if (reduceMotion || !('IntersectionObserver' in window)) {
            targets.forEach(function (el) {
                el.classList.add('ui-revealed');
            });
            return;
        }

        var revealObserver = new IntersectionObserver(
            function (entries, observer) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) {
                        return;
                    }
                    entry.target.classList.add('ui-revealed');
                    observer.unobserve(entry.target);
                });
            },
            {
                threshold: 0.12,
                rootMargin: '0px 0px -8% 0px'
            }
        );

        targets.forEach(function (el) {
            revealObserver.observe(el);
        });
    }

    function applyFeatureLoad(reduceMotion) {
        var features = document.querySelectorAll('[data-animate-feature], #map, #routeMap, #heroMap, .hero-map-wrap, .feature-section');
        if (!features.length) {
            return;
        }

        features.forEach(function (el) {
            el.classList.add('ui-feature-load');
        });

        if (reduceMotion) {
            features.forEach(function (el) {
                el.classList.add('ui-feature-loaded');
            });
            return;
        }

        requestAnimationFrame(function () {
            features.forEach(function (el) {
                el.classList.add('ui-feature-loaded');
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var reduceMotion = isReducedMotion();
        applyPageEnter(reduceMotion);
        applyButtonHover();
        applyCardHover();
        applyIconHover();
        applyRevealObserver(reduceMotion);
        applyFeatureLoad(reduceMotion);
    });
})();
