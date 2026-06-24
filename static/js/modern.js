// ===== MODAL MANAGEMENT =====
class ModalManager {
    constructor() {
        this.setupModals();
        this.setupAuthToggle();
    }

    setupModals() {
        const loginBtns = document.querySelectorAll('[data-auth-trigger="login"]');
        const registerBtns = document.querySelectorAll('[data-auth-trigger="register"]');
        const authModal = document.getElementById('authModal');
        const closeBtn = document.querySelector('.modal-close');

        loginBtns.forEach(loginBtn => {
            loginBtn.addEventListener('click', () => {
                this.showModal('login');
            });
        });

        registerBtns.forEach(registerBtn => {
            registerBtn.addEventListener('click', () => {
                this.showModal('register');
            });
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }

        if (authModal) {
            authModal.addEventListener('click', (e) => {
                if (e.target === authModal) {
                    this.closeModal();
                }
            });
        }

        // Setup form submissions
        this.setupFormSubmissions();

        // Setup password toggle
        this.setupPasswordToggle();
    }

    setupFormSubmissions() {
        const loginForm = document.getElementById('loginFormElement');
        const registerForm = document.getElementById('registerFormElement');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLoginSubmit(loginForm);
            });
        }

        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegisterSubmit(registerForm);
            });
        }
    }

    async handleLoginSubmit(form) {
        const formData = new FormData(form);
        const errorDiv = document.getElementById('loginError');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Logging in...';
        errorDiv.style.display = 'none';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const responsePath = new URL(response.url).pathname;
                if (response.redirected && responsePath !== '/users/login/') {
                    Toast.show('Login successful! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = response.url;
                    }, 1000);
                    return;
                }

                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const errors = doc.querySelectorAll('.errorlist li');
                let errorMsg = 'Login failed. Please check your credentials.';
                if (errors.length > 0) {
                    errorMsg = errors[0].textContent;
                }
                errorDiv.textContent = errorMsg;
                errorDiv.style.display = 'block';
            } else {
                errorDiv.textContent = 'Login failed. Please check your credentials.';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Error: ' + error.message;
            errorDiv.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Login';
        }
    }

    async handleRegisterSubmit(form) {
        const formData = new FormData(form);
        const errorDiv = document.getElementById('registerError');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating account...';
        errorDiv.style.display = 'none';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const responsePath = new URL(response.url).pathname;
                if (response.redirected && responsePath !== '/users/register/') {
                    Toast.show('Account created! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = response.url;
                    }, 1000);
                    return;
                }

                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const errors = doc.querySelectorAll('.errorlist li');
                let errorMsg = 'Registration failed. Please check your information.';
                if (errors.length > 0) {
                    errorMsg = Array.from(errors).map(e => e.textContent).join(', ');
                }
                errorDiv.textContent = errorMsg;
                errorDiv.style.display = 'block';
            } else {
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const errors = doc.querySelectorAll('.errorlist li');
                let errorMsg = 'Registration failed. Please check your information.';
                if (errors.length > 0) {
                    errorMsg = Array.from(errors).map(e => e.textContent).join(', ');
                }
                errorDiv.textContent = errorMsg;
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Error: ' + error.message;
            errorDiv.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Account';
        }
    }

    showModal(mode = 'login') {
        const modal = document.getElementById('authModal');
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        if (modal) {
            modal.classList.add('active');
            if (mode === 'login') {
                loginForm?.style.display = 'block';
                registerForm?.style.display = 'none';
            } else {
                loginForm?.style.display = 'none';
                registerForm?.style.display = 'block';
            }
        }
    }

    closeModal() {
        const modal = document.getElementById('authModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    setupAuthToggle() {
        const toggleToRegister = document.getElementById('toggleToRegister');
        const toggleToLogin = document.getElementById('toggleToLogin');

        if (toggleToRegister) {
            toggleToRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.showModal('register');
            });
        }

        if (toggleToLogin) {
            toggleToLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.showModal('login');
            });
        }
    }

    setupPasswordToggle() {
        const toggleBtns = document.querySelectorAll('.toggle-visibility');
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.previousElementSibling;
                const icon = this;

                if (input.type === 'password') {
                    input.type = 'text';
                    icon.textContent = '👁️‍🗨️';
                } else {
                    input.type = 'password';
                    icon.textContent = '👁️';
                }
            });
        });
    }
}

// ===== ACCORDION =====
class Accordion {
    constructor() {
        this.setupAccordions();
    }

    setupAccordions() {
        const headers = document.querySelectorAll('.accordion-header');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                this.toggleAccordion(header);
            });
        });
    }

    toggleAccordion(header) {
        const body = header.nextElementSibling;
        const isActive = header.classList.contains('active');

        // Close all other accordions
        document.querySelectorAll('.accordion-header').forEach(h => {
            if (h !== header && h.classList.contains('active')) {
                h.classList.remove('active');
                h.nextElementSibling.classList.remove('open');
            }
        });

        // Toggle current
        if (isActive) {
            header.classList.remove('active');
            body.classList.remove('open');
        } else {
            header.classList.add('active');
            body.classList.add('open');
        }
    }
}

// ===== SMOOTH SCROLLING =====
class SmoothScroll {
    constructor() {
        this.setupLinks();
    }

    setupLinks() {
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }
}

// ===== TOAST NOTIFICATIONS =====
class Toast {
    static show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// ===== DASHBOARD SIDEBAR =====
class DashboardSidebar {
    constructor() {
        this.setupSidebar();
    }

    setupSidebar() {
        const sidebarLinks = document.querySelectorAll('.sidebar-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                sidebarLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }
}

// ===== SCAN INPUT =====
class ScanInput {
    constructor() {
        this.setupScanInput();
    }

    setupScanInput() {
        const scanBtn = document.getElementById('scanBtn');
        const clearBtn = document.getElementById('clearBtn');
        const scanInput = document.getElementById('scanInput');

        if (scanBtn) {
            scanBtn.addEventListener('click', () => {
                this.performScan();
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (scanInput) {
                    scanInput.value = '';
                    scanInput.focus();
                }
                const result = document.getElementById('scanResult');
                if (result) {
                    result.style.display = 'none';
                }
            });
        }

        if (scanInput) {
            scanInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performScan();
                }
            });
        }
    }

    performScan() {
        const input = document.getElementById('scanInput');
        const result = document.getElementById('scanResult');

        if (!input || !input.value.trim()) {
            Toast.show('Please enter a URL or email', 'error');
            return;
        }

        const scanSection = document.querySelector('.scan-input-section');
        const scanUrl = scanSection?.dataset.scanUrl || '/scanner/url/';
        window.location.href = scanUrl;
    }

    showLoading() {
        const result = document.getElementById('scanResult');
        if (result) {
            result.innerHTML = '<div class="loader"></div>';
            result.style.display = 'block';
        }
    }

    showResult(risk, resultElement) {
        let status, color;

        if (risk < 30) {
            status = 'Safe';
            color = 'safe';
        } else if (risk < 70) {
            status = 'Suspicious';
            color = 'suspicious';
        } else {
            status = 'Dangerous';
            color = 'dangerous';
        }

        const html = `
            <div class="result-status ${color}">
                <strong>${status}</strong> - Risk Score: ${risk}%
            </div>
            <div class="risk-bar">
                <div class="risk-fill" style="width: ${risk}%"></div>
            </div>
            <p>${this.getRecommendation(risk)}</p>
        `;

        resultElement.innerHTML = html;
        resultElement.style.display = 'block';
        Toast.show(`Scan complete: ${status}`, 'info');
    }

    getRecommendation(risk) {
        if (risk < 30) return '✓ This appears to be safe. Proceed with caution.';
        if (risk < 70) return '⚠ Be cautious with this content. Verify before interacting.';
        return '✗ Avoid interaction with this content. Report if necessary.';
    }
}

// ===== NAVBAR ACTIVE STATE =====
class Navbar {
    constructor() {
        this.updateActiveLink();
        window.addEventListener('scroll', () => this.updateNavbarStyle());
    }

    updateActiveLink() {
        const currentPage = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-menu a');

        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPage.includes(href.replace(/^\//, ''))) {
                link.classList.add('active');
            }
        });
    }

    updateNavbarStyle() {
        const navbar = document.querySelector('.modern-navbar');
        if (navbar && window.scrollY > 20) {
            navbar.style.backgroundColor = 'rgba(7, 17, 31, 0.95)';
        } else if (navbar) {
            navbar.style.backgroundColor = 'rgba(7, 17, 31, 0.75)';
        }
    }
}

// ===== FORM VALIDATION =====
class FormValidator {
    constructor() {
        this.setupValidation();
    }

    setupValidation() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                if (this.validateLoginForm()) {
                    Toast.show('Login successful!', 'success');
                    setTimeout(() => {
                        new ModalManager().closeModal();
                    }, 500);
                }
            });
        }

        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                if (this.validateRegisterForm()) {
                    Toast.show('Account created successfully!', 'success');
                    setTimeout(() => {
                        new ModalManager().closeModal();
                    }, 500);
                }
            });
        }
    }

    validateLoginForm() {
        const email = document.querySelector('#loginForm input[type="email"]');
        const password = document.querySelector('#loginForm input[type="password"]');

        return this.validateEmail(email) && this.validatePassword(password);
    }

    validateRegisterForm() {
        const username = document.querySelector('#registerForm input[name="username"]');
        const email = document.querySelector('#registerForm input[type="email"]');
        const password = document.querySelector('#registerForm input[name="password"]');
        const confirmPassword = document.querySelector('#registerForm input[name="confirmPassword"]');

        return (
            this.validateUsername(username) &&
            this.validateEmail(email) &&
            this.validatePassword(password) &&
            this.validatePasswordMatch(password, confirmPassword)
        );
    }

    validateEmail(field) {
        const value = field?.value || '';
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!regex.test(value)) {
            this.showError(field, 'Invalid email');
            return false;
        }
        this.clearError(field);
        return true;
    }

    validatePassword(field) {
        const value = field?.value || '';
        if (value.length < 6) {
            this.showError(field, 'Password must be at least 6 characters');
            return false;
        }
        this.clearError(field);
        return true;
    }

    validateUsername(field) {
        const value = field?.value || '';
        if (value.length < 3) {
            this.showError(field, 'Username must be at least 3 characters');
            return false;
        }
        this.clearError(field);
        return true;
    }

    validatePasswordMatch(password, confirm) {
        if (password?.value !== confirm?.value) {
            this.showError(confirm, 'Passwords do not match');
            return false;
        }
        this.clearError(confirm);
        return true;
    }

    showError(field, message) {
        if (!field) return;
        field.style.borderColor = '#ef5b6b';
        let error = field.parentElement?.querySelector('.form-error');
        if (!error) {
            error = document.createElement('div');
            error.className = 'form-error';
            field.parentElement?.appendChild(error);
        }
        error.textContent = message;
    }

    clearError(field) {
        if (!field) return;
        field.style.borderColor = '#e1e8f2';
        const error = field.parentElement?.querySelector('.form-error');
        if (error) error.remove();
    }
}

// ===== PAGE SCROLL ANIMATIONS =====
class ScrollAnimations {
    constructor() {
        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        });

        document.querySelectorAll('.card').forEach(card => {
            observer.observe(card);
        });
    }
}

// ===== PROFILE FORM =====
class ProfileForm {
    constructor() {
        this.setupProfileForm();
    }

    setupProfileForm() {
        const form = document.getElementById('profileForm');
        if (!form) return;

        const editBtn = form.querySelector('.btn-save');
        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.preventDefault();
                Toast.show('Profile updated successfully!', 'success');
            });
        }
    }
}

// ===== INIT ON DOM READY =====
document.addEventListener('DOMContentLoaded', () => {
    new ModalManager();
    new Accordion();
    new SmoothScroll();
    new Navbar();
    new DashboardSidebar();
    new ScanInput();
    new ScrollAnimations();
    new ProfileForm();

    // Set current year in footer
    const yearElement = document.querySelector('[data-year]');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
});
