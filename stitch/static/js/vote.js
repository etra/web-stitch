/**
 * Vote button handler for community pattern cards.
 * Handles upvote/downvote toggle with API calls.
 */
(function () {
    'use strict';

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.vote-btn');
        if (!btn) return;

        var controls = btn.closest('.vote-controls');
        var projectId = controls.dataset.projectId;
        var value = parseInt(btn.dataset.value, 10);
        var isActive = btn.classList.contains('active');

        // Toggle off if already active, otherwise cast vote
        var method = isActive ? 'DELETE' : 'POST';
        var url = '/api/projects/' + projectId + '/vote';
        var options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };

        if (!isActive) {
            options.body = JSON.stringify({ value: value });
        }

        fetch(url, options)
            .then(function (response) {
                if (response.status === 401) {
                    window.location.href = '/auth/login';
                    return null;
                }
                if (!response.ok) {
                    throw new Error('Vote failed');
                }
                return response.json();
            })
            .then(function (data) {
                if (!data) return;

                // Update score display
                var scoreEl = controls.querySelector('.vote-score');
                scoreEl.textContent = Math.max(data.vote_score, 0);

                // Update active states
                var upBtn = controls.querySelector('.vote-up');
                var downBtn = controls.querySelector('.vote-down');
                upBtn.classList.toggle('active', data.user_vote === 1);
                downBtn.classList.toggle('active', data.user_vote === -1);
            })
            .catch(function (err) {
                console.error('Vote error:', err);
            });
    });
})();
