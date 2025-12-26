// ============================================
// JSW Paint Estimator - Enhanced Application
// ============================================

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global State
const state = {
    currentTab: 'manual',
    loading: false
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCoatSliders();
    initUploadDragDrop();
    initToastSystem();
    addPageAnimations();
    console.log('✨ JSW Paint Estimator initialized with premium features');
});

// Tab Management
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `${tabName}-tab`);
    });

    state.currentTab = tabName;

    // Smooth scroll to content
    setTimeout(() => {
        document.querySelector('.tab-pane.active')?.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest'
        });
    }, 100);
}

// Coat Sliders
function initCoatSliders() {
    // Manual estimation slider
    const manualSlider = document.getElementById('num_coats');
    const manualValue = document.getElementById('coats-value');

    if (manualSlider && manualValue) {
        manualSlider.addEventListener('input', (e) => {
            manualValue.textContent = e.target.value;
            animateNumberChange(manualValue);
        });
    }

    // CV estimation slider
    const cvSlider = document.getElementById('cv_num_coats');
    const cvValue = document.getElementById('cv-coats-value');

    if (cvSlider && cvValue) {
        cvSlider.addEventListener('input', (e) => {
            cvValue.textContent = e.target.value;
            animateNumberChange(cvValue);
        });
    }

    // Floor plan slider
    const floorplanSlider = document.getElementById('floorplan_num_coats');
    const floorplanValue = document.getElementById('floorplan-coats-value');

    if (floorplanSlider && floorplanValue) {
        floorplanSlider.addEventListener('input', (e) => {
            floorplanValue.textContent = e.target.value;
            animateNumberChange(floorplanValue);
        });
    }
}

// Animated number change
function animateNumberChange(element) {
    element.style.transform = 'scale(1.3)';
    element.style.color = 'var(--primary-start)';
    setTimeout(() => {
        element.style.transform = 'scale(1)';
        element.style.color = '';
    }, 200);
}

// Upload Drag & Drop Enhancement
function initUploadDragDrop() {
    const uploadArea = document.getElementById('upload-area');
    if (!uploadArea) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('drag-over');
        }, false);
    });
}

// Toast Notification System
function initToastSystem() {
    // Create toast container if it doesn't exist
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
    }
}

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const colors = {
        success: 'linear-gradient(135deg, #06D6A0 0%, #00B894 100%)',
        error: 'linear-gradient(135deg, #FF6B6B 0%, #EE5A6F 100%)',
        warning: 'linear-gradient(135deg, #FFD166 0%, #FFA500 100%)',
        info: 'linear-gradient(135deg, #4E54C8 0%, #8F94FB 100%)'
    };

    toast.style.cssText = `
        background: ${colors[type] || colors.info};
        color: white;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        display: flex;
        align-items: center;
        gap: 1rem;
        font-weight: 600;
        font-size: 1rem;
        pointer-events: all;
        cursor: pointer;
        animation: slideInRight 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        max-width: 400px;
        backdrop-filter: blur(10px);
    `;

    toast.innerHTML = `
        <span style="font-size: 1.5rem;">${icons[type] || icons.info}</span>
        <span style="flex: 1;">${message}</span>
        <span style="font-size: 1.2rem; opacity: 0.8;">×</span>
    `;

    // Add keyframes for animation
    if (!document.getElementById('toast-keyframes')) {
        const style = document.createElement('style');
        style.id = 'toast-keyframes';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(100px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            @keyframes slideOutRight {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(100px);
                }
            }
        `;
        document.head.appendChild(style);
    }

    container.appendChild(toast);

    // Auto remove
    const timeout = setTimeout(() => removeToast(toast), duration);

    // Click to dismiss
    toast.addEventListener('click', () => {
        clearTimeout(timeout);
        removeToast(toast);
    });
}

function removeToast(toast) {
    toast.style.animation = 'slideOutRight 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
    setTimeout(() => {
        toast.remove();
    }, 300);
}

// Page Load Animations
function addPageAnimations() {
    // Observe elements for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe cards and results
    document.querySelectorAll('.card, .result-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Animated Counter for Results
function animateCounter(element, start, end, duration = 1500, suffix = '') {
    if (!element) return;

    const startTime = performance.now();
    const range = end - start;

    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (easeOutCubic)
        const easeProgress = 1 - Math.pow(1 - progress, 3);

        const current = start + (range * easeProgress);

        if (suffix === '₹') {
            element.textContent = formatCurrency(current);
        } else {
            element.textContent = formatNumber(current) + (suffix ? ' ' + suffix : '');
        }

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }

    requestAnimationFrame(updateCounter);
}

// Smooth Scroll to Results
function scrollToResults(resultsId) {
    const resultsSection = document.getElementById(resultsId);
    if (resultsSection) {
        setTimeout(() => {
            resultsSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 300);
    }
}

// Loading Overlay
function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const text = overlay.querySelector('.loading-text');
    if (text) text.textContent = message;
    overlay.style.display = 'flex';
    state.loading = true;
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'none';
    state.loading = false;
}

// Utility Functions
function formatCurrency(amount) {
    return `₹${amount.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

function formatNumber(num, decimals = 2) {
    return num.toLocaleString('en-IN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function showError(message) {
    showToast(message, 'error', 5000);
    hideLoading();
}

function showSuccess(message) {
    showToast(message, 'success', 4000);
}

function showWarning(message) {
    showToast(message, 'warning', 4000);
}

function showInfo(message) {
    showToast(message, 'info', 3000);
}

// API Helper
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                ...options.headers,
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.detail || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Export for use in other modules
window.App = {
    state,
    showLoading,
    hideLoading,
    formatCurrency,
    formatNumber,
    showError,
    showSuccess,
    showWarning,
    showInfo,
    showToast,
    apiCall,
    animateCounter,
    scrollToResults,
    API_BASE_URL
};
