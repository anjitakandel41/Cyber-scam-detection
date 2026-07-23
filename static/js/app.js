(function () {
    const modalHTML = `
    <div id="logoutConfirmModal" class="modal fade" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow-lg">
                <div class="modal-header border-bottom-0">
                    <div>
                        <h5 class="modal-title fw-bold">Confirm Logout</h5>
                        <p class="text-muted mb-0">You are about to sign out of Cyber Scam Detection.</p>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body pt-0">
                    <div class="alert alert-warning d-flex align-items-center mb-0" role="alert">
                        <i class="bi bi-exclamation-triangle-fill flex-shrink-0 me-2"></i>
                        <div>
                            Are you sure you want to logout? You will need to sign in again to access your dashboard.
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-top-0">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" id="logoutConfirmBtn"><i class="bi bi-box-arrow-right me-1"></i>Logout</button>
                </div>
            </div>
        </div>
    </div>
    `;

    let pendingLogoutForm = null;

    function createLogoutModal() {
        if (!document.getElementById('logoutConfirmModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }

    function showLogoutModal() {
        const modalEl = document.getElementById('logoutConfirmModal');
        if (!modalEl) return;

        if (window.bootstrap && typeof bootstrap.Modal === 'function') {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            return;
        }

        if (pendingLogoutForm) {
            pendingLogoutForm.submit();
        }
    }

    function initLogoutConfirmation() {
        createLogoutModal();

        const dashboardLogoutForm = document.getElementById('dashboardLogoutForm');
        if (dashboardLogoutForm) {
            dashboardLogoutForm.addEventListener('submit', (event) => {
                event.preventDefault();
                event.stopPropagation();
                pendingLogoutForm = dashboardLogoutForm;
                showLogoutModal();
            });
        }

        document.body.addEventListener('click', (event) => {
            const logoutButton = event.target.closest('.logout-link, button[data-logout]');
            if (!logoutButton) return;
            if (logoutButton.id === 'dashboardLogoutBtn') return;

            const form = logoutButton.closest('form[action*="logout"]');
            if (!form) return;

            event.preventDefault();
            event.stopPropagation();
            pendingLogoutForm = form;
            showLogoutModal();
        });

        const confirmBtn = document.getElementById('logoutConfirmBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                if (!pendingLogoutForm) return;
                pendingLogoutForm.submit();
            });
        }

        document.querySelectorAll('[data-year]').forEach((node) => {
            node.textContent = new Date().getFullYear();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLogoutConfirmation);
    } else {
        initLogoutConfirmation();
    }
})();
