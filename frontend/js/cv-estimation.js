// ============================================
// CV-based Estimation (Scenario 2)
// ============================================

let selectedImage = null;
let uploadMode = 'single'; // 'single', 'multi', or 'video'
let selectedWalls = []; // Array of {file, name, preview} for multi-wall mode
let selectedVideo = null; // Video file for video mode

document.addEventListener('DOMContentLoaded', () => {
    initCVEstimation();
    initUploadModeToggle();
    initMultiWallUpload();
    initVideoUpload();
});

function initCVEstimation() {
    const form = document.getElementById('cv-form');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('room-image');
    const browseBtn = document.getElementById('browse-btn');
    const removeBtn = document.getElementById('remove-image');

    if (!form) return;

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleCVEstimation();
    });

    // Click to browse
    uploadArea.addEventListener('click', () => fileInput.click());
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleFileSelect(file);
        }
    });

    // Remove image
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearImage();
    });

    // DIRECT BUTTON CLICK HANDLER (Debug workaround)
    const submitBtn = document.getElementById('cv-submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', async (e) => {
            console.log('🔍 CV Submit button clicked!', {
                disabled: submitBtn.disabled,
                selectedImage: !!selectedImage,
                uploadMode: uploadMode
            });

            if (submitBtn.disabled) {
                console.warn('⚠️ Button is disabled - cannot submit');
                alert('Please upload an image first!');
                return;
            }

            // Let the form handler take over
        });
    }
}

function handleFileSelect(file) {
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        window.App.showError('Please select a valid image file');
        return;
    }

    // Store selected file
    selectedImage = file;

    // Preview image
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('image-preview');
        const previewImg = document.getElementById('preview-img');
        const uploadArea = document.getElementById('upload-area');

        previewImg.src = e.target.result;
        preview.style.display = 'block';
        uploadArea.style.display = 'none';

        // Enable submit button
        document.getElementById('cv-submit-btn').disabled = false;
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    selectedImage = null;

    const preview = document.getElementById('image-preview');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('room-image');

    preview.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInput.value = '';

    // Disable submit button
    document.getElementById('cv-submit-btn').disabled = true;
}

async function handleCVEstimation() {
    if (uploadMode === 'single') {
        await handleSingleWallEstimation();
    } else {
        await handleMultiWallEstimation();
    }
}

// Note: handleSingleWallEstimation and handleMultiWallEstimation are defined later in the file

function displayCVResults(data) {
    const resultsSection = document.getElementById('cv-results');
    const resultsContent = document.getElementById('cv-results-content');

    if (!resultsSection || !resultsContent) return;

    const { formatCurrency, formatNumber } = window.App;

    // Build HTML
    const html = `
        <div class="result-grid">
            <!-- Detection Results -->
            ${data.detection_results ? `
                <div class="card">
                    <h3 style="margin-bottom: 1rem; color: var(--dark-color);">🔍 Detection Results</h3>
                    <div class="detection-info">
                        <div class="detection-badge">
                            🚪 ${data.detection_results.detected_doors} Door${data.detection_results.detected_doors !== 1 ? 's' : ''} Detected
                        </div>
                        <div class="detection-badge">
                            🪟 ${data.detection_results.detected_windows} Window${data.detection_results.detected_windows !== 1 ? 's' : ''} Detected
                        </div>
                        <div class="detection-badge">
                            📊 Total Detections: ${data.detection_results.total_detections}
                        </div>
                    </div>
                    ${data.image_analysis ? `
                        <div style="margin-top: 1rem; padding: 1rem; background: var(--light-color); border-radius: 8px;">
                            <div style="font-size: 0.9rem; color: #666;">
                                <strong>Dimension Method:</strong> ${data.image_analysis.dimensions_method || 'cv_estimation'}
                            </div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
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
                <button class="btn btn-secondary" onclick="copyCVResults()">
                    <span class="btn-text">Copy to Clipboard</span>
                    <span class="btn-icon">📋</span>
                </button>
            </div>
        </div>
    `;

    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function copyCVResults() {
    const { showSuccess, showError } = window.App;
    const resultsText = document.getElementById('cv-results-content').innerText;
    navigator.clipboard.writeText(resultsText).then(() => {
        showSuccess('Results copied to clipboard! 📋');
    }).catch(() => {
        showError('Failed to copy results');
    });
}

// ============================================
// Multi-Wall Upload Functionality
// ============================================

function initUploadModeToggle() {
    const modeButtons = document.querySelectorAll('.mode-btn');

    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            handleModeToggle(mode);
        });
    });
}

function handleModeToggle(mode) {
    uploadMode = mode;

    // Update button states
    document.querySelectorAll('.mode-btn').forEach(btn => {
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Show/hide appropriate sections
    const singleSection = document.getElementById('single-upload-section');
    const multiSection = document.getElementById('multi-wall-section');
    const videoSection = document.getElementById('video-upload-section');
    const floorplanSection = document.getElementById('floorplan-upload-section');
    const floorplanConfig = document.getElementById('floorplan-config-section');
    const cvForm = document.getElementById('cv-form');
    const cvRoomDetails = document.getElementById('cv-room-details-section');

    if (mode === 'single') {
        singleSection.style.display = 'block';
        multiSection.style.display = 'none';
        videoSection.style.display = 'none';
        if (floorplanSection) floorplanSection.style.display = 'none';
        if (floorplanConfig) floorplanConfig.style.display = 'none';
        if (cvForm) cvForm.style.display = 'block';
        if (cvRoomDetails) cvRoomDetails.style.display = 'block';

        // Clear other modes
        selectedWalls = [];
        selectedVideo = null;

        // Enable/disable submit based on single image
        const submitBtn = document.getElementById('cv-submit-btn');
        submitBtn.disabled = !selectedImage;
        submitBtn.innerHTML = `
            <span class="btn-text">Analyze Image & Calculate Paint</span>
            <span class="btn-icon">🔍</span>
        `;
    } else if (mode === 'multi') {
        singleSection.style.display = 'none';
        multiSection.style.display = 'block';
        videoSection.style.display = 'none';
        if (floorplanSection) floorplanSection.style.display = 'none';
        if (floorplanConfig) floorplanConfig.style.display = 'none';
        if (cvForm) cvForm.style.display = 'block';
        if (cvRoomDetails) cvRoomDetails.style.display = 'block';

        // Clear other modes
        clearImage();
        selectedVideo = null;

        // Enable/disable submit based on walls
        const submitBtn = document.getElementById('cv-submit-btn');
        submitBtn.disabled = selectedWalls.length < 2;
        submitBtn.innerHTML = `
            <span class="btn-text">Analyze Walls & Calculate Paint</span>
            <span class="btn-icon">🔍</span>
        `;
    } else if (mode === 'video') {
        singleSection.style.display = 'none';
        multiSection.style.display = 'none';
        videoSection.style.display = 'block';
        if (floorplanSection) floorplanSection.style.display = 'none';
        if (floorplanConfig) floorplanConfig.style.display = 'none';
        if (cvForm) cvForm.style.display = 'block';
        if (cvRoomDetails) cvRoomDetails.style.display = 'block';

        // Clear other modes
        clearImage();
        selectedWalls = [];

        // Enable/disable submit based on video
        const submitBtn = document.getElementById('cv-submit-btn');
        submitBtn.disabled = !selectedVideo;
        submitBtn.innerHTML = `
            <span class="btn-text">Analyze Video & Calculate Paint</span>
            <span class="btn-icon">🎥</span>
        `;
    } else if (mode === 'floorplan') {
        singleSection.style.display = 'none';
        multiSection.style.display = 'none';
        videoSection.style.display = 'none';
        if (floorplanSection) floorplanSection.style.display = 'block';
        if (floorplanConfig) floorplanConfig.style.display = 'block';
        if (cvForm) cvForm.style.display = 'none';
        if (cvRoomDetails) cvRoomDetails.style.display = 'none';

        // Clear other modes
        clearImage();
        selectedWalls = [];
        selectedVideo = null;

        // The floor plan form has its own submit button that's managed separately
    }
}

function initMultiWallUpload() {
    const multiTrigger = document.getElementById('multi-upload-trigger');
    const multiFileInput = document.getElementById('multi-wall-images');
    const multiBrowseBtn = document.getElementById('multi-browse-btn');

    if (!multiTrigger || !multiFileInput) return;

    // Click to browse
    multiTrigger.addEventListener('click', () => multiFileInput.click());
    multiBrowseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        multiFileInput.click();
    });

    // File selection
    multiFileInput.addEventListener('change', (e) => {
        handleMultiWallSelect(Array.from(e.target.files));
    });

    // Drag and drop
    multiTrigger.addEventListener('dragover', (e) => {
        e.preventDefault();
        multiTrigger.parentElement.classList.add('drag-over');
    });

    multiTrigger.addEventListener('dragleave', () => {
        multiTrigger.parentElement.classList.remove('drag-over');
    });

    multiTrigger.addEventListener('drop', (e) => {
        e.preventDefault();
        multiTrigger.parentElement.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (files.length > 0) {
            handleMultiWallSelect(files);
        }
    });
}

function handleMultiWallSelect(files) {
    const { showError } = window.App;

    // Validate number of files
    if (files.length + selectedWalls.length > 4) {
        showError('Maximum 4 walls allowed. Please select fewer images.');
        return;
    }

    if (files.length < 1) {
        showError('Please select at least one image.');
        return;
    }

    // Add each file
    files.forEach((file, index) => {
        if (!file.type.startsWith('image/')) {
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            selectedWalls.push({
                file: file,
                name: `Wall ${selectedWalls.length + 1}`,
                preview: e.target.result
            });

            updateWallPreviewsGrid();
        };
        reader.readAsDataURL(file);
    });
}

function updateWallPreviewsGrid() {
    const grid = document.getElementById('wall-previews-grid');
    const container = document.getElementById('wall-previews-container');

    if (!grid) return;

    // Show container if walls exist
    if (selectedWalls.length > 0) {
        container.style.display = 'block';

        // Clear and rebuild grid
        grid.innerHTML = '';

        selectedWalls.forEach((wall, index) => {
            const tile = document.createElement('div');
            tile.className = 'wall-preview-tile';
            tile.innerHTML = `
                <img src="${wall.preview}" alt="${wall.name}">
                <div class="wall-preview-label">${wall.name}</div>
                <button class="btn-remove-wall" data-index="${index}">×</button>
            `;

            // Add remove handler
            const removeBtn = tile.querySelector('.btn-remove-wall');
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeWall(index);
            });

            grid.appendChild(tile);
        });

        // Update submit button
        const submitBtn = document.getElementById('cv-submit-btn');
        submitBtn.disabled = selectedWalls.length < 2;
    } else {
        container.style.display = 'none';

        // Disable submit
        const submitBtn = document.getElementById('cv-submit-btn');
        submitBtn.disabled = true;
    }
}

function removeWall(index) {
    selectedWalls.splice(index, 1);

    // Renumber remaining walls
    selectedWalls.forEach((wall, i) => {
        wall.name = `Wall ${i + 1}`;
    });

    updateWallPreviewsGrid();
}

async function handleCVEstimation() {
    if (uploadMode === 'single') {
        await handleSingleWallEstimation();
    } else if (uploadMode === 'multi') {
        await handleMultiWallEstimation();
    } else if (uploadMode === 'video') {
        await handleVideoEstimation();
    }
}

async function handleSingleWallEstimation() {
    const { showLoading, hideLoading, showError, showSuccess, API_BASE_URL } = window.App;

    if (!selectedImage) {
        showError('Please select an image first');
        return;
    }

    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('image', selectedImage);
        formData.append('room_type', document.getElementById('room_type').value);
        formData.append('paint_type', document.getElementById('cv_paint_type').value);
        formData.append('num_coats', document.getElementById('cv_num_coats').value);
        formData.append('include_ceiling', document.getElementById('cv_include_ceiling').checked);

        // Add manual overrides if provided
        const length = document.getElementById('cv_length').value;
        const width = document.getElementById('cv_width').value;
        const height = document.getElementById('cv_height').value;

        if (length) formData.append('length', length);
        if (width) formData.append('width', width);
        if (height) formData.append('height', height);

        // Show loading
        showLoading('🔍 Analyzing image and detecting objects...');

        // Call API
        const response = await fetch(`${API_BASE_URL}/api/v1/estimate/cv/single-room`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || result.detail || 'Request failed');
        }

        // Hide loading
        hideLoading();

        // Show success
        showSuccess('Image analysis complete! 🎉');

        // Display results
        displayCVResults(result.data);

    } catch (error) {
        showError(error.message || 'Failed to analyze image');
    }
}

async function handleMultiWallEstimation() {
    const { showLoading, hideLoading, showError, showSuccess, API_BASE_URL } = window.App;

    if (selectedWalls.length < 2) {
        showError('Please select at least 2 wall images for multi-wall mode');
        return;
    }

    try {
        // Prepare form data
        const formData = new FormData();

        // Append all wall images
        selectedWalls.forEach(wall => {
            formData.append('images', wall.file);
        });

        // Create room data array
        const roomData = selectedWalls.map(wall => ({
            room_type: document.getElementById('room_type').value,
            room_name: wall.name,
            paint_type: document.getElementById('cv_paint_type').value,
            num_coats: parseInt(document.getElementById('cv_num_coats').value),
            include_ceiling: false // Only count ceiling once
        }));

        formData.append('room_data', JSON.stringify(roomData));

        // Show loading
        showLoading(`🏠 Analyzing ${selectedWalls.length} walls...`);

        // Call multi-room API
        const response = await fetch(`${API_BASE_URL}/api/v1/estimate/cv/multi-room`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || result.detail || 'Request failed');
        }

        // Hide loading
        hideLoading();

        // Show success
        showSuccess(`Multi-wall analysis complete! 🎉`);

        // Display multi-wall results
        displayMultiWallResults(result.data);

    } catch (error) {
        hideLoading();
        showError(error.message || 'Failed to analyze walls');
    }
}

function displayMultiWallResults(data) {
    const resultsSection = document.getElementById('cv-results');
    const resultsContent = document.getElementById('cv-results-content');

    if (!resultsSection || !resultsContent) return;

    const { formatCurrency, formatNumber } = window.App;

    // Calculate averaged dimensions
    const rooms = data.rooms || [];
    let avgLength = 0, avgWidth = 0, avgHeight = 0;

    rooms.forEach(room => {
        const dims = room.estimation.dimensions || {};
        avgLength += dims.length || 0;
        avgWidth += dims.width || 0;
        avgHeight += dims.height || 0;
    });

    avgLength = (avgLength / rooms.length).toFixed(1);
    avgWidth = (avgWidth / rooms.length).toFixed(1);
    avgHeight = (avgHeight / rooms.length).toFixed(1);

    // Build HTML
    const html = `
        <div class="result-grid">
            <!-- Averaged Dimensions (Highlighted) -->
            <div class="averaged-dimensions">
                <h3>📊 Averaged Room Dimensions</h3>
                <p style="opacity: 0.9; margin-bottom: 1rem;">Calculated from ${rooms.length} wall images</p>
                <div class="dimensions-grid">
                    <div class="dimension-item">
                        <div>Length</div>
                        <strong>${avgLength} ft</strong>
                    </div>
                    <div class="dimension-item">
                        <div>Width</div>
                        <strong>${avgWidth} ft</strong>
                    </div>
                    <div class="dimension-item">
                        <div>Height</div>
                        <strong>${avgHeight} ft</strong>
                    </div>
                </div>
            </div>
            
            <!-- Individual Wall Results -->
            <div class="card">
                <h3 style="margin-bottom: 1.5rem; color: var(--dark);">📸 Individual Wall Detections</h3>
                <div class="individual-wall-results">
                    ${rooms.map(room => {
        const est = room.estimation;
        const dims = est.dimensions || {};
        const det = est.detection_results || {};

        return `
                            <div class="wall-result-card">
                                <h4>${room.room_name}</h4>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 0.75rem;">
                                    <div>
                                        <div style="font-size: 0.85rem; color: #666;">Dimensions</div>
                                        <div style="font-weight: 700; color: var(--dark);">${dims.length} × ${dims.width} × ${dims.height} ft</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.85rem; color: #666;">Detections</div>
                                        <div style="font-weight: 700; color: var(--dark);">
                                            🚪 ${det.detected_doors || 0} | 🪟 ${det.detected_windows || 0}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
    }).join('')}
                </div>
            </div>
            
            <!-- Summary Cards -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div class="result-card">
                    <div class="result-header">Total Paintable Area</div>
                    <div class="result-value">${formatNumber(data.total_paintable_area)}</div>
                    <div class="result-unit">sq ft</div>
                </div>
                <div class="result-card">
                    <div class="result-header">Total Paint Required</div>
                    <div class="result-value">${formatNumber(data.total_paint_required)}</div>
                    <div class="result-unit">liters</div>
                </div>
                <div class="result-card">
                    <div class="result-header">Walls Analyzed</div>
                    <div class="result-value">${data.total_summary.total_rooms}</div>
                    <div class="result-unit">walls</div>
                </div>
            </div>
            
            <!-- Total Cost -->
            <div class="total-cost">
                <div class="total-label">Total Estimated Cost</div>
                <div class="total-amount">${formatCurrency(data.total_cost)}</div>
                <div style="margin-top: 1rem; opacity: 0.9; font-size: 0.9rem;">
                    For all ${rooms.length} walls combined
                </div>
            </div>
            
            <!-- Actions -->
            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1rem;">
                <button class="btn btn-secondary" onclick="window.print()">
                    <span class="btn-text">Print Results</span>
                    <span class="btn-icon">🖨️</span>
                </button>
                <button class="btn btn-secondary" onclick="copyCVResults()">
                    <span class="btn-text">Copy to Clipboard</span>
                    <span class="btn-icon">📋</span>
                </button>
            </div>
        </div>
    `;

    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
