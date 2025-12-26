// Add to end of cv-estimation.js

// ============================================
// Video Upload Functionality
// ============================================

function initVideoUpload() {
    const videoTrigger = document.getElementById('video-upload-trigger');
    const videoFileInput = document.getElementById('room-video');
    const videoBrowseBtn = document.getElementById('video-browse-btn');
    const removeVideoBtn = document.getElementById('remove-video');

    if (!videoTrigger || !videoFileInput) return;

    // Click to browse
    videoTrigger.addEventListener('click', () => videoFileInput.click());
    videoBrowseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        videoFileInput.click();
    });

    // File selection
    videoFileInput.addEventListener('change', (e) => {
        handleVideoSelect(e.target.files[0]);
    });

    // Drag and drop
    videoTrigger.addEventListener('dragover', (e) => {
        e.preventDefault();
        videoTrigger.parentElement.classList.add('drag-over');
    });

    videoTrigger.addEventListener('dragleave', () => {
        videoTrigger.parentElement.classList.remove('drag-over');
    });

    videoTrigger.addEventListener('drop', (e) => {
        e.preventDefault();
        videoTrigger.parentElement.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('video/')) {
            handleVideoSelect(file);
        }
    });

    // Remove video
    if (removeVideoBtn) {
        removeVideoBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            clearVideo();
        });
    }
}

function handleVideoSelect(file) {
    const { showError } = window.App;

    if (!file) return;

    if (!file.type.startsWith('video/')) {
        showError('Please select a valid video file');
        return;
    }

    // Check file size (50 MB limit)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('Video file is too large. Maximum size is 50 MB.');
        return;
    }

    // Store selected video
    selectedVideo = file;

    // Preview video
    const videoPreview = document.getElementById('preview-video');
    const videoSource = document.getElementById('video-source');
    const videoContainer = document.getElementById('video-preview-container');
    const uploadArea = document.querySelector('.video-upload-area');

    const videoURL = URL.createObjectURL(file);
    videoSource.src = videoURL;
    videoSource.type = file.type;
    videoPreview.load();

    // Show metadata once loaded
    videoPreview.addEventListener('loadedmetadata', () => {
        const duration = videoPreview.duration;
        const width = videoPreview.videoWidth;
        const height = videoPreview.videoHeight;

        const metadataDiv = document.getElementById('video-metadata');
        metadataDiv.innerHTML = `
            <div style="display: grid; gap: 0.5rem; margin-top: 0.5rem;">
                <div>📹 Duration: ${formatDuration(duration)}</div>
                <div>📐 Resolution: ${width} × ${height}px</div>
                <div>📦 Size: ${formatFileSize(file.size)}</div>
            </div>
        `;

        // Check duration (30 seconds limit)
        if (duration > 30) {
            showError('Video is too long. Maximum duration is 30 seconds.');
            clearVideo();
            return;
        }
    });

    videoContainer.style.display = 'block';
    uploadArea.style.display = 'none';

    // Enable submit button
    document.getElementById('cv-submit-btn').disabled = false;
}

function clearVideo() {
    selectedVideo = null;

    const videoPreview = document.getElementById('preview-video');
    const videoSource = document.getElementById('video-source');
    const videoContainer = document.getElementById('video-preview-container');
    const uploadArea = document.querySelector('.video-upload-area');
    const fileInput = document.getElementById('room-video');

    videoSource.src = '';
    videoPreview.load();
    videoContainer.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInput.value = '';

    // Disable submit button
    document.getElementById('cv-submit-btn').disabled = true;
}

async function handleVideoEstimation() {
    const { showLoading, hideLoading, showError, showSuccess, API_BASE_URL } = window.App;

    if (!selectedVideo) {
        showError('Please select a video first');
        return;
    }

    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('video', selectedVideo);
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
        showLoading('🎥 Processing video and analyzing frames...<br><small>This may take a moment</small>');

        // Call API
        const response = await fetch(`${API_BASE_URL}/api/v1/estimate/cv/video`, {
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
        showSuccess(`Video analysis complete! 🎉 (Analyzed ${result.data.video_analysis.frames_analyzed} frames)`);

        // Display results
        displayVideoResults(result.data);

    } catch (error) {
        hideLoading();
        showError(error.message || 'Failed to analyze video');
    }
}

function displayVideoResults(data) {
    const resultsSection = document.getElementById('cv-results');
    const resultsContent = document.getElementById('cv-results-content');

    if (!resultsSection || !resultsContent) return;

    const { formatCurrency, formatNumber } = window.App;

    const videoAnalysis = data.video_analysis || {};
    const conf = videoAnalysis.detection_confidence || {};

    // Build HTML
    const html = `
        <div class="result-grid">
            <!-- Video Analysis Summary -->
            <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 2rem;">
                <h3 style="margin-bottom: 1rem; color: white;">🎥 Video Analysis Summary</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    <div>
                        <div style="font-size: 0.85rem; opacity: 0.9;">Frames Analyzed</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">${videoAnalysis.frames_analyzed}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.85rem; opacity: 0.9;">Duration</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">${formatDuration(videoAnalysis.metadata.duration)}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.85rem; opacity: 0.9;">Overall Confidence</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">${Math.round(conf.overall_confidence * 100)}%</div>
                    </div>
                </div>
            </div>
            
            <!-- Detection Results -->
            ${data.detection_results ? `
                <div class="card">
                    <h3 style="margin-bottom: 1rem; color: var(--dark-color);">🔍 Aggregated Detection Results</h3>
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
                    ${conf.detection_confidence ? `
                        <div style="margin-top: 1rem; padding: 1rem; background: #e8f5e9; border-radius: 8px;">
                            <div style="font-size: 0.9rem; color: #2e7d32;">
                                <strong>Detection Confidence:</strong> ${Math.round(conf.detection_confidence * 100)}% (consistent across frames)
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
                    Estimated from video analysis
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

// Helper functions
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
        return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
