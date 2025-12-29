// Manual Estimation - New Premium UI
// Handles form submission and results display with animations

const API_BASE_URL = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    initializeCoatsSlider();
});

/**
 * Initialize the manual estimation form
 */
function initializeForm() {
    const form = document.getElementById('manual-form');

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

/**
 * Initialize the coats slider
 */
function initializeCoatsSlider() {
    const slider = document.getElementById('num_coats');
    const display = document.getElementById('coats-display');

    if (slider && display) {
        slider.addEventListener('input', (e) => {
            display.textContent = e.target.value;

            // Add animation
            display.style.transform = 'scale(1.2)';
            setTimeout(() => {
                display.style.transform = 'scale(1)';
            }, 150);
        });
    }
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);

    // Build request payload
    const payload = {
        room: {
            length: parseFloat(formData.get('length')),
            width: parseFloat(formData.get('width')),
            height: parseFloat(formData.get('height')),
            num_doors: parseInt(formData.get('num_doors')),
            num_windows: parseInt(formData.get('num_windows'))
        },
        paint_type: formData.get('paint_type'),
        num_coats: parseInt(formData.get('num_coats')),
        include_ceiling: formData.get('include_ceiling') === 'on'
    };

    // Show loading
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/estimate/manual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const response_data = await response.json();
        console.log('📊 Manual estimate response:', response_data);
        console.log('📊 Response keys:', Object.keys(response_data));

        // Extract actual data from nested structure
        const data = response_data.data || response_data;
        console.log('📊 Actual data:', data);

        displayResults(data);
        showToast('success', 'Calculation Complete', 'Paint estimate generated successfully');

    } catch (error) {
        console.error('Error:', error);
        showToast('error', 'Calculation Failed', 'Please check your input and try again');
    } finally {
        showLoading(false);
    }
}

/**
 * Display results with animation
 */
function displayResults(data) {
    const container = document.getElementById('results-container');

    if (!container) return;

    // Build results HTML
    const html = `
        <div class="results-grid">
            <!-- Summary Card -->
            <div class="result-card">
                <h3 class="result-card__title">Surface Details</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Paintable Area</span>
                        <span class="result-item__value">${data.summary?.paintable_area_sqft?.toFixed(1) || 'N/A'} sq ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Paint Required</span>
                        <span class="result-item__value">${data.summary?.paint_required_liters?.toFixed(2) || 'N/A'} L</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Number of Coats</span>
                        <span class="result-item__value">${data.num_coats || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            <!-- Cost Breakdown Card -->
            <div class="result-card">
                <h3 class="result-card__title">Product Breakdown</h3>
                <div class="result-card__content">
                    ${generateProductBreakdown(data.product_breakdown)}
                </div>
            </div>
            
            <!-- Total Cost -->
            <div class="result-total">
                <div class="result-total__label">Total Estimated Cost</div>
                <div class="result-total__value animate-count">₹${animateNumber(data.cost_breakdown?.total_cost || 0)}</div>
            </div>
        </div>
        
        <div class="result-actions">
            <button class="btn btn--secondary" onclick="window.print()">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 7V3h10v4M5 14H3a1 1 0 01-1-1V9a1 1 0 011-1h14a1 1 0 011 1v4a1 1 0 01-1 1h-2M5 14v3h10v-3"/>
                </svg>
                Print Estimate
            </button>
            <button class="btn btn--primary" onclick="resetForm()">
                Calculate Again
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4v5h5M16 16v-5h-5M4 9a8 8 0 0112.9-3.1M16 11a8 8 0 01-12.9 3.1"/>
                </svg>
            </button>
        </div>
    `;

    container.innerHTML = html;
    container.style.display = 'block';

    // Scroll to results smoothly
    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);

    // Animate the total cost number
    setTimeout(() => {
        animateTotalCost(data.cost_breakdown?.total_cost || 0);
    }, 500);
}

/**
 * Generate product breakdown HTML
 */
function generateProductBreakdown(productBreakdown) {
    if (!productBreakdown) {
        return '<div class="result-item"><span class="result-item__label">No products</span></div>';
    }

    const items = [];

    // Handle both array and object structures
    // Check for primer (singular)
    const primer = productBreakdown.primer;
    if (primer) {
        if (Array.isArray(primer)) {
            primer.forEach(item => {
                items.push(`
                    <div class="result-item">
                        <span class="result-item__label">${item.product_name || 'Primer'}</span>
                        <span class="result-item__value">${item.quantity?.toFixed(2) || '0'} ${item.unit || 'L'}</span>
                    </div>
                `);
            });
        } else if (primer.product_name) {
            // Single object
            items.push(`
                <div class="result-item">
                    <span class="result-item__label">${primer.product_name || 'Primer'}</span>
                    <span class="result-item__value">${primer.quantity?.toFixed(2) || '0'} ${primer.unit || 'L'}</span>
                </div>
            `);
        }
    }

    // Check for paints
    const paints = productBreakdown.paints;
    if (paints) {
        if (Array.isArray(paints)) {
            paints.forEach(item => {
                items.push(`
                    <div class="result-item">
                        <span class="result-item__label">${item.product_name || 'Paint'}</span>
                        <span class="result-item__value">${item.quantity?.toFixed(2) || '0'} ${item.unit || 'L'}</span>
                    </div>
                `);
            });
        } else if (paints.product_name) {
            // Single object
            items.push(`
                <div class="result-item">
                    <span class="result-item__label">${paints.product_name || 'Paint'}</span>
                    <span class="result-item__value">${paints.quantity?.toFixed(2) || '0'} ${paints.unit || 'L'}</span>
                </div>
            `);
        }
    }

    // Check for putty
    const putty = productBreakdown.putty;
    if (putty) {
        if (Array.isArray(putty)) {
            putty.forEach(item => {
                items.push(`
                    <div class="result-item">
                        <span class="result-item__label">${item.product_name || 'Putty'}</span>
                        <span class="result-item__value">${item.quantity?.toFixed(2) || '0'} ${item.unit || 'kg'}</span>
                    </div>
                `);
            });
        } else if (putty.product_name) {
            // Single object
            items.push(`
                <div class="result-item">
                    <span class="result-item__label">${putty.product_name || 'Putty'}</span>
                    <span class="result-item__value">${putty.quantity?.toFixed(2) || '0'} ${putty.unit || 'kg'}</span>
                </div>
            `);
        }
    }

    return items.length > 0 ? items.join('') : '<div class="result-item"><span class="result-item__label">No products</span></div>';
}

/**
 * Animate number counting
 */
function animateNumber(target) {
    return target.toFixed(0);
}

/**
 * Animate total cost with counting effect
 */
function animateTotalCost(target) {
    const element = document.querySelector('.result-total__value');
    if (!element) return;

    const duration = 1000; // 1 second
    const steps = 50;
    const increment = target / steps;
    const stepDuration = duration / steps;

    let current = 0;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = `₹${target.toFixed(0)}`;
            clearInterval(timer);
        } else {
            element.textContent = `₹${Math.floor(current)}`;
        }
    }, stepDuration);
}

/**
 * Reset form to initial state
 */
function resetForm() {
    const form = document.getElementById('manual-form');
    const resultsContainer = document.getElementById('results-container');

    if (form) {
        form.reset();
        document.getElementById('coats-display').textContent = '2';
    }

    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Show/hide loading overlay
 */
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

/**
 * Show toast notification
 */
function showToast(type, title, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `
        <div class="toast__icon">
            ${getToastIcon(type)}
        </div>
        <div class="toast__content">
            <div class="toast__title">${title}</div>
            <div class="toast__message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('toast--show');
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('toast--show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Get toast icon SVG based on type
 */
function getToastIcon(type) {
    const icons = {
        success: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 13l4 4L19 7"/></svg>',
        error: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 18L18 6M6 6l12 12"/></svg>',
        warning: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        info: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };
    return icons[type] || icons.info;
}
