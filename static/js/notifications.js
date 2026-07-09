/*
 * Shared notification bell widget - included on every dashboard.
 * Requires the markup from templates/partials/notification_bell.html
 * (ids: notificationCount, notificationDropdown, notificationList).
 * Exposes toggleNotifications/markRead/markAllRead globally since the
 * partial's markup calls them via inline onclick="" attributes.
 */
(function () {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    }

    function renderList(notifications) {
        const list = document.getElementById('notificationList');
        if (!list) return;
        if (!notifications.length) {
            list.innerHTML = '<div class="text-center text-muted p-4">No new notifications</div>';
            return;
        }
        list.innerHTML = notifications.map(function (n) {
            return '<div class="notification-item unread" onclick="markRead(' + n.id + ')">' +
                '<div><strong>' + escapeHtml(n.title) + '</strong></div>' +
                '<div>' + escapeHtml(n.message) + '</div>' +
                '<div class="time">' + escapeHtml(n.created_at) + '</div>' +
                '</div>';
        }).join('');
    }

    function refreshNotifications() {
        fetch('/notification/notifications/', { credentials: 'same-origin' })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                const countEl = document.getElementById('notificationCount');
                if (countEl) countEl.textContent = data.count;
                renderList(data.notifications || []);
            })
            .catch(function (err) { console.error('Failed to load notifications:', err); });
    }

    function toggleNotifications() {
        const dropdown = document.getElementById('notificationDropdown');
        if (!dropdown) return;
        const opening = dropdown.style.display !== 'block';
        dropdown.style.display = opening ? 'block' : 'none';
        if (opening) refreshNotifications();
    }

    function markRead(id) {
        fetch('/notification/' + id + '/read/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        })
            .then(function (res) { if (!res.ok) throw new Error('request failed'); return res.json(); })
            .then(refreshNotifications)
            .catch(function () { alert('Unable to mark notification as read.'); });
    }

    function markAllRead() {
        fetch('/notification/read-all/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        })
            .then(function (res) { if (!res.ok) throw new Error('request failed'); return res.json(); })
            .then(refreshNotifications)
            .catch(function () { alert('Unable to mark notifications as read.'); });
    }

    function init() {
        // Nothing to do if this page didn't include the bell partial.
        if (!document.getElementById('notificationCount')) return;

        refreshNotifications(); // fetch immediately - was previously only fetched on click or after a 30s wait
        setInterval(refreshNotifications, 30000);

        // Refresh when the tab regains focus or is restored from the
        // back/forward cache (neither fires DOMContentLoaded again).
        document.addEventListener('visibilitychange', function () {
            if (document.visibilityState === 'visible') refreshNotifications();
        });
        window.addEventListener('pageshow', function () { refreshNotifications(); });

        // Close the dropdown on an outside click (single delegated listener,
        // instead of reloading notifications on every click anywhere on the page).
        document.addEventListener('click', function (event) {
            const badge = event.target.closest ? event.target.closest('.notification-badge') : null;
            if (!badge) {
                const dropdown = document.getElementById('notificationDropdown');
                if (dropdown) dropdown.style.display = 'none';
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.toggleNotifications = toggleNotifications;
    window.markRead = markRead;
    window.markAllRead = markAllRead;
})();
