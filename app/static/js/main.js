document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl =>
        new bootstrap.Tooltip(tooltipTriggerEl)
    );

    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl =>
        new bootstrap.Popover(popoverTriggerEl)
    );

    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
                e.preventDefault();
            }
        });
    });

    const textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('data-max-length');
        const counter = document.createElement('div');
        counter.className = 'form-text text-end';
        textarea.parentNode.appendChild(counter);

        function updateCounter() {
            const length = textarea.value.length;
            counter.textContent = `${length}/${maxLength} символов`;

            if (length > maxLength * 0.9) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }

            if (length > maxLength) {
                counter.classList.add('text-danger');
                textarea.classList.add('is-invalid');
            } else {
                counter.classList.remove('text-danger');
                textarea.classList.remove('is-invalid');
            }
        }

        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });

    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Отправка...';
                submitButton.disabled = true;
            }
        });
    });

    const tagInput = document.getElementById('tags');
    if (tagInput) {
        tagInput.addEventListener('input', function() {
            const tags = this.value.split(',').map(tag => tag.trim()).filter(tag => tag);
            if (tags.length > 5) {
                this.value = tags.slice(0, 5).join(', ');
                this.classList.add('is-invalid');

                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = 'Максимум 5 тегов';
                this.parentNode.appendChild(feedback);
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }

    const shareButtons = document.querySelectorAll('.share-article');
    shareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="bi bi-check"></i> Скопировано!';
                this.classList.add('btn-success');

                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-success');
                }, 2000);
            });
        });
    });

    const likeButtons = document.querySelectorAll('.like-article');
    likeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.getAttribute('data-article-id');
            const likeCount = this.querySelector('.like-count');

            fetch(`/api/articles/${articleId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                likeCount.textContent = data.likes;
                this.classList.toggle('btn-outline-danger');
                this.classList.toggle('btn-danger');
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-bs-theme', currentTheme);

        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            this.innerHTML = newTheme === 'light'
                ? '<i class="bi bi-moon"></i>'
                : '<i class="bi bi-sun"></i>';
        });
    }
});

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;

    notification.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function checkAuth() {
    const protectedLinks = document.querySelectorAll('[data-require-auth]');
    protectedLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!document.querySelector('[data-user-authenticated]')) {
                e.preventDefault();
                showNotification('Для этого действия необходимо авторизоваться', 'warning');

                localStorage.setItem('redirect_after_login', this.href);

                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', checkAuth);

function togglePasswordVisibility(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId || inputId + 'Btn');

    if (!input || !button) return;

    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        if (icon) icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        if (icon) icon.className = 'bi bi-eye';
    }
}

function validateUsername(username) {
    const pattern = /^[a-zA-Z0-9_]{3,50}$/;
    return pattern.test(username);
}

function validateEmail(email) {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(email);
}

function showProfileMessage(message, type = 'success') {
    const oldAlerts = document.querySelectorAll('.profile-alert');
    oldAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show profile-alert`;
    alertDiv.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px;';

    const iconClass = type === 'success' ? 'bi-check-circle' :
                     type === 'danger' ? 'bi-exclamation-triangle' : 'bi-info-circle';

    alertDiv.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function initProfileModal() {
    const modal = document.getElementById('editProfileModal');
    if (!modal) return;

    const usernameInput = document.getElementById('editUsername');
    const warningAlert = document.getElementById('usernameChangeWarning');
    const form = document.getElementById('editProfileForm');
    const toggleCurrentBtn = document.getElementById('toggleCurrentPasswordBtn');
    const toggleNewBtn = document.getElementById('toggleNewPasswordBtn');

    if (warningAlert) {
        warningAlert.style.display = 'none';
    }

    if (toggleCurrentBtn) {
        toggleCurrentBtn.addEventListener('click', () =>
            togglePasswordVisibility('currentPassword', 'toggleCurrentPasswordBtn'));
    }

    if (toggleNewBtn) {
        toggleNewBtn.addEventListener('click', () =>
            togglePasswordVisibility('newPassword', 'toggleNewPasswordBtn'));
    }

    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            const isValid = validateUsername(this.value.trim());
            const isChanged = this.value.trim() !== this.defaultValue;

            if (warningAlert) {
                warningAlert.style.display = isChanged ? 'block' : 'none';
            }

            if (this.value.trim() === '') {
                this.classList.remove('is-valid', 'is-invalid');
            } else if (isValid) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });

        usernameInput.addEventListener('blur', function() {
            const value = this.value.trim();
            if (value && !validateUsername(value)) {
                showProfileMessage(
                    'Имя пользователя должно содержать только латинские буквы, цифры и подчеркивание (3-50 символов)',
                    'warning'
                );
            }
        });
    }

    if (form) {
        form.addEventListener('submit', function(event) {
            const username = usernameInput ? usernameInput.value.trim() : '';
            const emailInput = document.getElementById('editEmail');
            const email = emailInput ? emailInput.value.trim() : '';
            const currentPassword = document.getElementById('currentPassword')?.value.trim() || '';
            const newPassword = document.getElementById('newPassword')?.value.trim() || '';

            let isValid = true;
            let errorMessage = '';

            if (username && !validateUsername(username)) {
                isValid = false;
                errorMessage = 'Некорректное имя пользователя. Используйте только латинские буквы, цифры и подчеркивание (3-50 символов).';
            }

            if (email && !validateEmail(email)) {
                isValid = false;
                errorMessage = 'Некорректный email адрес.';
            }

            if (!currentPassword) {
                isValid = false;
                errorMessage = 'Введите текущий пароль для подтверждения.';
            }

            if (newPassword && newPassword.length < 6) {
                isValid = false;
                errorMessage = 'Новый пароль должен содержать минимум 6 символов.';
            }

            if (username && username !== usernameInput?.defaultValue) {
                if (!confirm('При изменении имени пользователя вам потребуется войти в систему заново. Продолжить?')) {
                    isValid = false;
                }
            }

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
                showProfileMessage(errorMessage, 'danger');
                return false;
            }

            const submitBtn = document.getElementById('saveChangesBtn');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Сохранение...';
                submitBtn.disabled = true;

                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }

            return true;
        });
    }

    modal.addEventListener('hidden.bs.modal', function() {
        if (usernameInput) {
            usernameInput.value = usernameInput.defaultValue;
            usernameInput.classList.remove('is-valid', 'is-invalid');
        }

        if (warningAlert) {
            warningAlert.style.display = 'none';
        }

        const currentPassword = document.getElementById('currentPassword');
        const newPassword = document.getElementById('newPassword');

        if (currentPassword) currentPassword.value = '';
        if (newPassword) newPassword.value = '';

        const submitBtn = document.getElementById('saveChangesBtn');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="bi bi-check-lg"></i> Сохранить изменения';
            submitBtn.disabled = false;
        }
    });
}


document.addEventListener('DOMContentLoaded', function() {
    initProfileModal();

    checkAuth();

    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    const error = urlParams.get('error');

    if (message) {
        showProfileMessage(decodeURIComponent(message), 'success');
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }

    if (error) {
        showProfileMessage(decodeURIComponent(error), 'danger');
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }

    if (error && document.getElementById('editProfileModal')) {
        const modal = new bootstrap.Modal(document.getElementById('editProfileModal'));
        modal.show();
    }
});

window.togglePasswordVisibility = togglePasswordVisibility;
window.showProfileMessage = showProfileMessage;