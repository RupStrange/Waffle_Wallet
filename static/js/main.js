// main.js — students will add JavaScript here as features are built

// --------------------------------------------------------------------------
// Signed-in app shell: sliding sidebar and dashboard tabs.
//
// Everything here operates on markup already in the DOM, so it needs no
// backend. Each block guards on its own container and no-ops elsewhere.
// --------------------------------------------------------------------------
(function () {
    "use strict";

    var app = document.querySelector(".ww-app");
    if (!app) {
        return; // not a signed-in page
    }

    // ---- Sliding sidebar -------------------------------------------------

    var toggle = document.getElementById("ww-sidebar-toggle");
    var sidebar = document.getElementById("ww-sidebar");
    var overlay = document.getElementById("ww-sidebar-overlay");
    var closeBtn = document.getElementById("ww-sidebar-close");

    if (toggle && sidebar) {
        var openNav = function () {
            app.classList.add("is-nav-open");
            toggle.setAttribute("aria-expanded", "true");
            toggle.setAttribute("aria-label", "Close menu");
            if (overlay) {
                overlay.hidden = false;
            }
            // Move focus into the drawer so keyboard users land inside it.
            var first = sidebar.querySelector(".ww-sidebar-link");
            if (first) {
                first.focus();
            }
        };

        var closeNav = function (returnFocus) {
            app.classList.remove("is-nav-open");
            toggle.setAttribute("aria-expanded", "false");
            toggle.setAttribute("aria-label", "Open menu");
            if (overlay) {
                overlay.hidden = true;
            }
            if (returnFocus) {
                toggle.focus();
            }
        };

        toggle.addEventListener("click", function () {
            if (app.classList.contains("is-nav-open")) {
                closeNav(true);
            } else {
                openNav();
            }
        });

        if (closeBtn) {
            closeBtn.addEventListener("click", function () {
                closeNav(true);
            });
        }

        if (overlay) {
            overlay.addEventListener("click", function () {
                closeNav(true);
            });
        }

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && app.classList.contains("is-nav-open")) {
                closeNav(true);
            }
        });
    }

    // ---- Dashboard tabs --------------------------------------------------

    var tabs = Array.prototype.slice.call(app.querySelectorAll('[role="tab"]'));

    if (tabs.length) {
        var selectTab = function (tab, focusIt) {
            tabs.forEach(function (t) {
                var selected = t === tab;
                t.setAttribute("aria-selected", selected ? "true" : "false");
                t.classList.toggle("is-active", selected);
                // Roving tabindex: only the active tab is reachable by Tab.
                t.tabIndex = selected ? 0 : -1;

                var panel = document.getElementById(t.getAttribute("aria-controls"));
                if (panel) {
                    panel.hidden = !selected;
                }
            });
            if (focusIt) {
                tab.focus();
            }
        };

        tabs.forEach(function (tab, i) {
            tab.addEventListener("click", function () {
                selectTab(tab, false);
            });

            tab.addEventListener("keydown", function (e) {
                var next = null;
                switch (e.key) {
                    case "ArrowRight":
                        next = tabs[(i + 1) % tabs.length];
                        break;
                    case "ArrowLeft":
                        next = tabs[(i - 1 + tabs.length) % tabs.length];
                        break;
                    case "Home":
                        next = tabs[0];
                        break;
                    case "End":
                        next = tabs[tabs.length - 1];
                        break;
                    default:
                        return;
                }
                e.preventDefault();
                selectTab(next, true);
            });
        });
    }

    // ---- Expense filtering and sorting -----------------------------------
    //
    // Operates on the static rows via their data-category / data-date /
    // data-amount attributes. A later step replaces this with server-side
    // query params and keeps the JS only as a progressive enhancement.

    var list = app.querySelector(".ww-txns");
    var countEl = app.querySelector(".ww-pf-result-count");
    var emptyEl = app.querySelector(".ww-pf-empty");
    var qEl = document.getElementById("pf-f-q");
    var catEl = document.getElementById("pf-f-cat");
    var fromEl = document.getElementById("pf-f-from");
    var toEl = document.getElementById("pf-f-to");
    var sortEl = document.getElementById("pf-f-sort");
    var resetEl = app.querySelector(".ww-pf-filter-reset");

    if (list) {
        var rows = Array.prototype.slice.call(list.querySelectorAll(".ww-txn"));
        var total = rows.length;

        var apply = function () {
            var term = qEl ? qEl.value.trim().toLowerCase() : "";
            var category = catEl ? catEl.value : "";
            var from = fromEl ? fromEl.value : "";
            var to = toEl ? toEl.value : "";
            var shown = 0;

            rows.forEach(function (row) {
                var rowCat = row.getAttribute("data-category");
                var rowDate = row.getAttribute("data-date");
                var nameEl = row.querySelector(".ww-txn-name");
                var name = nameEl ? nameEl.textContent.toLowerCase() : "";

                // ISO dates compare correctly as strings, so no Date parsing.
                var visible =
                    (!term || name.indexOf(term) !== -1) &&
                    (!category || rowCat === category) &&
                    (!from || rowDate >= from) &&
                    (!to || rowDate <= to);

                row.hidden = !visible;
                if (visible) {
                    shown += 1;
                }
            });

            if (countEl) {
                countEl.textContent =
                    "Showing " + shown + " of " + total + " expense" + (total === 1 ? "" : "s");
            }
            if (emptyEl) {
                emptyEl.hidden = shown !== 0;
            }
        };

        var sort = function () {
            var mode = sortEl ? sortEl.value : "date-desc";

            var ordered = rows.slice().sort(function (a, b) {
                switch (mode) {
                    case "date-asc":
                        return a.getAttribute("data-date") > b.getAttribute("data-date") ? 1 : -1;
                    case "amt-desc":
                        return Number(b.getAttribute("data-amount")) - Number(a.getAttribute("data-amount"));
                    case "amt-asc":
                        return Number(a.getAttribute("data-amount")) - Number(b.getAttribute("data-amount"));
                    default: // date-desc
                        return a.getAttribute("data-date") < b.getAttribute("data-date") ? 1 : -1;
                }
            });

            ordered.forEach(function (row) {
                list.appendChild(row);
            });
        };

        [catEl, fromEl, toEl].forEach(function (el) {
            if (el) {
                el.addEventListener("change", apply);
            }
        });

        if (qEl) {
            qEl.addEventListener("input", apply);
        }

        if (sortEl) {
            sortEl.addEventListener("change", sort);
        }

        if (resetEl) {
            resetEl.addEventListener("click", function () {
                if (qEl) { qEl.value = ""; }
                if (catEl) { catEl.value = ""; }
                if (fromEl) { fromEl.value = ""; }
                if (toEl) { toEl.value = ""; }
                if (sortEl) { sortEl.value = "date-desc"; }
                sort();
                apply();
            });
        }
    }

    // ---- Time travel: quick date chips -----------------------------------

    var dateEl = document.getElementById("pf-date");
    var chips = Array.prototype.slice.call(app.querySelectorAll(".ww-pf-daychip"));

    // The page is static, so "today" is the fixed date the dummy data is
    // anchored to rather than the real clock. A later step reads this from
    // the server-rendered value instead.
    var anchor = dateEl && dateEl.getAttribute("max");

    var isoDaysAgo = function (days) {
        var d = new Date(anchor + "T00:00:00");
        d.setDate(d.getDate() - days);
        return d.toISOString().slice(0, 10);
    };

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
            if (!dateEl) {
                return;
            }

            if (chip.hasAttribute("data-pick")) {
                // showPicker() is not in every browser — fall back to focus.
                if (typeof dateEl.showPicker === "function") {
                    dateEl.showPicker();
                } else {
                    dateEl.focus();
                }
                return; // leave the active chip where it was
            }

            if (anchor) {
                dateEl.value = isoDaysAgo(Number(chip.getAttribute("data-days")));
            }

            chips.forEach(function (c) {
                c.classList.toggle("is-active", c === chip);
            });
        });
    });

    // A manual edit means none of the preset chips apply any more.
    if (dateEl) {
        dateEl.addEventListener("change", function () {
            chips.forEach(function (c) {
                if (c.hasAttribute("data-pick")) {
                    return;
                }
                c.classList.toggle(
                    "is-active",
                    Boolean(anchor) && dateEl.value === isoDaysAgo(Number(c.getAttribute("data-days")))
                );
            });
        });
    }
})();
