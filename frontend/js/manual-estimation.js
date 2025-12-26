// ============================================
// Manual Estimation (Scenario 1)
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initManualEstimation();
});

function initManualEstimation() {
    const form = document.getElementById('manual-form');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleManualEstimation();
    });
}

async function handleManualEstimation() {
    const { showLoading, hideLoading, showError, showSuccess, apiCall } = window.App;

    try {
        // Get form data
        const formData = getManualFormData();

        // Debug: Log request data
        console.log('🔍 Manual Estimation Request:', formData);

        // Validate
        if (!validateManualForm(formData)) {
            return;
        }

        // Show loading
        showLoading('🎨 Calculating paint requirements...');

        // Call API
        const response = await apiCall('/api/v1/estimate/manual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        // Debug: Log response data
        console.log('✅ Manual Estimation Response:', response);
        console.log('📊 Calculation Details:', {
            paintable_area: response.data?.area_calculation?.paintable_area,
            paint_quantity: response.data?.product_breakdown?.paint?.quantity,
            paint_cost: response.data?.product_breakdown?.paint?.total_cost,
            putty_quantity: response.data?.product_breakdown?.putty?.quantity,
            putty_cost: response.data?.product_breakdown?.putty?.total_cost,
            total_cost: response.data?.cost_breakdown?.total_cost
        });

        // Hide loading
        hideLoading();

        // Show success
        showSuccess('Calculation complete! 🎉');

        // Display results
        displayManualResults(response.data);

    } catch (error) {
        showError(error.message || 'Failed to calculate estimation');
    }
}

function getManualFormData() {
    const data = {
        room: {
            length: parseFloat(document.getElementById('length').value),
            width: parseFloat(document.getElementById('width').value),
            height: parseFloat(document.getElementById('height').value),
            num_doors: parseInt(document.getElementById('num_doors').value) || 0,
            num_windows: parseInt(document.getElementById('num_windows').value) || 0
        },
        paint_type: document.getElementById('paint_type').value,
        num_coats: parseInt(document.getElementById('num_coats').value),
        include_ceiling: document.getElementById('include_ceiling').checked
    };

    // Add custom door dimensions if provided
    const doorHeight = document.getElementById('door_height')?.value;
    const doorWidth = document.getElementById('door_width')?.value;
    if (doorHeight) data.room.door_height = parseFloat(doorHeight);
    if (doorWidth) data.room.door_width = parseFloat(doorWidth);

    // Add custom window dimensions if provided
    const windowHeight = document.getElementById('window_height')?.value;
    const windowWidth = document.getElementById('window_width')?.value;
    if (windowHeight) data.room.window_height = parseFloat(windowHeight);
    if (windowWidth) data.room.window_width = parseFloat(windowWidth);

    return data;
}

function validateManualForm(data) {
    const { showError } = window.App;

    if (data.room.length <= 0 || data.room.width <= 0 || data.room.height <= 0) {
        showError('Room dimensions must be greater than 0');
        return false;
    }

    if (data.room.length > 100 || data.room.width > 100 || data.room.height > 20) {
        showError('Room dimensions seem too large. Please check your inputs.');
        return false;
    }

    return true;
}

function displayManualResults(data) {
    const resultsSection = document.getElementById('manual-results');
    const resultsContent = document.getElementById('manual-results-content');

    if (!resultsSection || !resultsContent) return;

    const { formatCurrency, formatNumber } = window.App;

    // Build HTML
    const html = `
        <div class="result-grid">
            <!-- Summary Cards -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div class="result-card">
                    <div class="result-header">Paintable Area</div>
                    <div class="result-value">${formatNumber(data.area_calculation.paintable_area)}</div>
                    <div class="result-unit">sq ft</div>
                </div>
                <div class="result-card">
                    <div class="result-header">Paint Required</div>
                    <div class="result-value">${formatNumber(data.product_breakdown.paint.quantity)}</div>
                    <div class="result-unit">liters</div>
                </div>
                <div class="result-card">
                    <div class="result-header">Number of Coats</div>
                    <div class="result-value">${data.num_coats}</div>
                    <div class="result-unit">coats</div>
                </div>
            </div>
            
            <!-- Area Breakdown -->
            <div class="card">
                <h3 style="margin-bottom: 1rem; color: var(--dark-color);">📐 Area Breakdown</h3>
                <div class="product-breakdown">
                    <div class="product-item">
                        <span class="product-name">Total Wall Area</span>
                        <span class="product-quantity">${formatNumber(data.area_calculation.total_wall_area)} sq ft</span>
                    </div>
                    <div class="product-item">
                        <span class="product-name">Door Area</span>
                        <span class="product-quantity">${formatNumber(data.area_calculation.door_area)} sq ft</span>
                    </div>
                    <div class="product-item">
                        <span class="product-name">Window Area</span>
                        <span class="product-quantity">${formatNumber(data.area_calculation.window_area)} sq ft</span>
                    </div>
                    ${data.area_calculation.ceiling_area ? `
                        <div class="product-item">
                            <span class="product-name">Ceiling Area</span>
                            <span class="product-quantity">${formatNumber(data.area_calculation.ceiling_area)} sq ft</span>
                        </div>
                    ` : ''}
                    <div class="product-item" style="background: var(--light-color); font-weight: 600;">
                        <span class="product-name">Paintable Area</span>
                        <span class="product-quantity" style="color: var(--primary-color);">${formatNumber(data.area_calculation.paintable_area)} sq ft</span>
                    </div>
                </div>
            </div>
            
            <!-- Product Breakdown -->
            <div class="card">
                <h3 style="margin-bottom: 1rem; color: var(--dark-color);">🎨 Product Requirements</h3>
                <div class="product-breakdown">
                    ${data.product_breakdown.primer ? `
                        <div class="product-item">
                            <div>
                                <div class="product-name">${data.product_breakdown.primer.product_name}</div>
                                <div class="text-muted" style="font-size: 0.85rem;">Primer</div>
                            </div>
                            <div class="product-details">
                                <div class="product-quantity">${formatNumber(data.product_breakdown.primer.quantity)} ${data.product_breakdown.primer.unit}</div>
                                <div class="product-cost">${formatCurrency(data.product_breakdown.primer.total_cost)}</div>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${data.product_breakdown.putty ? `
                        <div class="product-item">
                            <div>
                                <div class="product-name">${data.product_breakdown.putty.product_name}</div>
                                <div class="text-muted" style="font-size: 0.85rem;">Putty</div>
                            </div>
                            <div class="product-details">
                                <div class="product-quantity">${formatNumber(data.product_breakdown.putty.quantity)} ${data.product_breakdown.putty.unit}</div>
                                <div class="product-cost">${formatCurrency(data.product_breakdown.putty.total_cost)}</div>
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="product-item">
                        <div>
                            <div class="product-name">${data.product_breakdown.paint.product_name}</div>
                            <div class="text-muted" style="font-size: 0.85rem;">${data.paint_type.charAt(0).toUpperCase() + data.paint_type.slice(1)} Paint</div>
                        </div>
                        <div class="product-details">
                            <div class="product-quantity">${formatNumber(data.product_breakdown.paint.quantity)} ${data.product_breakdown.paint.unit}</div>
                            <div class="product-cost">${formatCurrency(data.product_breakdown.paint.total_cost)}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Total Cost -->
            <div class="total-cost">
                <div class="total-label">Total Estimated Cost</div>
                <div class="total-amount">${formatCurrency(data.cost_breakdown.total_cost)}</div>
                <div style="margin-top: 1rem; opacity: 0.9; font-size: 0.9rem;">
                    Estimated range: ${data.summary.estimated_cost_range}
                </div>
            </div>
            
            <!-- Actions -->
            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1rem;">
                <button class="btn btn-secondary" onclick="window.print()">
                    <span class="btn-text">Print Results</span>
                    <span class="btn-icon">🖨️</span>
                </button>
                <button class="btn btn-secondary" onclick="copyResults()">
                    <span class="btn-text">Copy to Clipboard</span>
                    <span class="btn-icon">📋</span>
                </button>
            </div>
        </div>
        `;

    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';

    // Store data globally for debugging
    window.lastEstimationData = data;
    console.log('💾 Estimation data saved to window.lastEstimationData');
    console.log('💡 Tip: Open console and inspect window.lastEstimationData for detailed breakdown');

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function copyResults() {
    const { showSuccess, showError } = window.App;
    const resultsText = document.getElementById('manual-results-content').innerText;
    navigator.clipboard.writeText(resultsText).then(() => {
        showSuccess('Results copied to clipboard! 📋');
    }).catch(() => {
        showError('Failed to copy results');
    });
}
