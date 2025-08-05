// AutoTestify Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading animation to buttons on form submit
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                submitBtn.disabled = true;
                
                // Re-enable button after 30 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 30000);
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('alert-dismissible')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        }, 5000);
    });

    // Add fade-in animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .feature-card').forEach(card => {
        observer.observe(card);
    });

    // Copy to clipboard functionality
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!', 'success');
        }).catch(() => {
            showToast('Failed to copy to clipboard', 'error');
        });
    }

    // Toast notification system
    function showToast(message, type = 'info') {
        const toastContainer = getOrCreateToastContainer();
        const toast = createToast(message, type);
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    function getOrCreateToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    function createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const iconMap = {
            success: 'fas fa-check-circle text-success',
            error: 'fas fa-exclamation-circle text-danger',
            warning: 'fas fa-exclamation-triangle text-warning',
            info: 'fas fa-info-circle text-info'
        };
        
        toast.innerHTML = `
            <div class="toast-header">
                <i class="${iconMap[type] || iconMap.info} me-2"></i>
                <strong class="me-auto">AutoTestify</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        return toast;
    }

    // Form validation enhancement
    document.querySelectorAll('input[type="url"]').forEach(input => {
        input.addEventListener('blur', function() {
            const url = this.value.trim();
            if (url && !isValidUrl(url)) {
                this.classList.add('is-invalid');
                showValidationMessage(this, 'Please enter a valid URL');
            } else {
                this.classList.remove('is-invalid');
                hideValidationMessage(this);
            }
        });
    });

    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            const email = this.value.trim();
            if (email && !isValidEmail(email)) {
                this.classList.add('is-invalid');
                showValidationMessage(this, 'Please enter a valid email address');
            } else {
                this.classList.remove('is-invalid');
                hideValidationMessage(this);
            }
        });
    });

    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function showValidationMessage(input, message) {
        hideValidationMessage(input);
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        input.parentNode.appendChild(feedback);
    }

    function hideValidationMessage(input) {
        const feedback = input.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    // Progress bar animation
    function animateProgressBar(progressBar, targetWidth, duration = 1000) {
        const startWidth = 0;
        const startTime = performance.now();
        
        function updateProgress(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentWidth = startWidth + (targetWidth - startWidth) * progress;
            
            progressBar.style.width = currentWidth + '%';
            progressBar.setAttribute('aria-valuenow', currentWidth);
            
            if (progress < 1) {
                requestAnimationFrame(updateProgress);
            }
        }
        
        requestAnimationFrame(updateProgress);
    }

    // Expose utility functions globally
    window.AutoTestify = {
        showToast,
        copyToClipboard,
        animateProgressBar,
        isValidUrl,
        isValidEmail
    };
});

// GitHub URL validation and parsing
function parseGitHubUrl(url) {
    const regex = /^https:\/\/github\.com\/([^\/]+)\/([^\/]+)\/?$/;
    const match = url.match(regex);
    
    if (match) {
        return {
            owner: match[1],
            repo: match[2],
            isValid: true
        };
    }
    
    return {
        isValid: false,
        error: 'Invalid GitHub repository URL format'
    };
}

// API URL validation
function validateApiUrl(url) {
    try {
        const parsedUrl = new URL(url);
        
        if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
            return {
                isValid: false,
                error: 'URL must use HTTP or HTTPS protocol'
            };
        }
        
        return {
            isValid: true,
            protocol: parsedUrl.protocol,
            hostname: parsedUrl.hostname,
            port: parsedUrl.port
        };
    } catch (error) {
        return {
            isValid: false,
            error: 'Invalid URL format'
        };
    }
}

// File size formatter
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Time formatter
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Local storage helpers
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
            return false;
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to read from localStorage:', error);
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
            return false;
        }
    }
};

// Export utilities
window.AutoTestifyUtils = {
    parseGitHubUrl,
    validateApiUrl,
    formatFileSize,
    formatTime,
    debounce,
    Storage
};