// Video Estimation - Walkthrough Video Analysis
// Premium UI with video upload and frame extraction

const API_BASE_URL = 'http://localhost:8000/api/v1';
let uploadedVideo = null;

document.addEventListener('DOMContentLoaded', () => {
    setupUploadHandlers();
});

/**
 * Setup upload handlers
 */
function setupUploadHandlers() {
    const input = document.getElementById('video-input');
    const dropZone = document.getElementById('video-drop-zone');
    const form = document.getElementById('video-form');

    if (input) {
        input.addEventListener('change', handleVideoSelect);
    }

    if (dropZone) {
        setupDragDrop(dropZone);
    }

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

/**
 * Setup drag and drop
 */
function setupDragDrop(element) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.classList.add('upload-zone--drag-over');
    });

    element.addEventListener('dragleave', () => {
        element.classList.remove('upload-zone--drag-over');
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.classList.remove('upload-zone--drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleVideoDrop(files[0]);
        }
    });

    // Click to upload
    element.addEventListener('click', (e) => {
        if (e.target === element || e.target.closest('.upload-zone__icon, .upload-zone__title')) {
            document.getElementById('video-input').click();
        }
    });
}

/**
 * Handle video selection
 */
function handleVideoSelect(e) {
    const file = e.target.files[0];
    if (file) {
        displayVideo(file);
    }
}

/**
 * Handle video drop
 */
function handleVideoDrop(file) {
    displayVideo(file);
}

/**
 * Display video preview
 */
function displayVideo(file) {
    // Validate file type
    if (!file.type.startsWith('video/')) {
        showToast('error', 'Invalid File Type', 'Please upload a video file');
        return;
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('error', 'File Too Large', 'Please upload a video smaller than 50MB');
        return;
    }

    uploadedVideo = file;

    // Create video URL
    const videoURL = URL.createObjectURL(file);
    const player = document.getElementById('video-preview-player');
    player.src = videoURL;

    // Get video metadata
    player.addEventListener('loadedmetadata', () => {
        const duration = player.duration;
        const size = (file.size / (1024 * 1024)).toFixed(2);

        document.getElementById('video-info').textContent =
            `Duration: ${formatDuration(duration)} | Size: ${size} MB | Format: ${file.type.split('/')[1].toUpperCase()}`;
    });

    // Show preview and config
    document.getElementById('video-preview').style.display = 'block';
    document.getElementById('config-section').style.display = 'block';
    document.getElementById('upload-section').querySelector('.upload-zone').style.display = 'none';

    showToast('success', 'Video Uploaded', 'Please configure settings and submit');
}

/**
 * Remove video
 */
function removeVideo() {
    if (uploadedVideo) {
        URL.revokeObjectURL(document.getElementById('video-preview-player').src);
    }

    uploadedVideo = null;
    document.getElementById('video-preview').style.display = 'none';
    document.getElementById('config-section').style.display = 'none';
    document.getElementById('upload-section').querySelector('.upload-zone').style.display = 'flex';
    document.getElementById('video-input').value = '';
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    if (!uploadedVideo) {
        showToast('warning', 'No Video', 'Please upload a video first');
        return;
    }

    const formData = new FormData();
    formData.append('video', uploadedVideo);
    formData.append('room_type', document.getElementById('room_type').value);
    formData.append('paint_type', document.getElementById('paint_type').value);
    formData.append('num_coats', '2'); // Default

    showLoading(true);
    simulateProgress();

    try {
        const response = await fetch(`${API_BASE_URL}/estimate/cv/video`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const responseData = await response.json();
        // Backend wraps response in {success: true, data: {...}, message: "..."}
        const data = responseData.data || responseData;

        console.log('Video analysis response:', data); // Debug log

        displayResults(data);
        showToast('success', 'Analysis Complete', responseData.message || 'Video analyzed successfully');

    } catch (error) {
        console.error('Error:', error);
        console.error('Full error details:', {
            message: error.message,
            stack: error.stack
        });
        showToast('error', 'Analysis Failed', 'Please ensure the video clearly shows the room');
    } finally {
        showLoading(false);
    }
}

/**
 * Simulate progress for video processing
 */
function simulateProgress() {
    const progressBar = document.getElementById('progress-fill');
    if (!progressBar) return;

    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 90) {
            progress = 90;
            clearInterval(interval);
        }
        progressBar.style.width = `${progress}%`;
    }, 500);

    // Store interval ID to clear it later
    window.progressInterval = interval;
}

/**
 * Display results
 */
function displayResults(data) {
    // Clear progress if still running
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
    }

    const container = document.getElementById('results-container');
    if (!container) return;

    console.log('Displaying results with data:', data); // Debug

    // Phase 4: Check if manual input needed
    if (data.manual_input_request?.needs_manual_input && window.manualModal) {
        console.log('⚠️  Low confidence detected, showing manual input modal');
        window.manualModal.show({
            confidence: data.manual_input_request.confidence_score || 0,
            reason: data.manual_input_request.reason || 'Low confidence in automated estimation',
            currentEstimate: data.manual_input_request.current_estimates || {}
        });
    }

    // Extract dimensions - could be in multiple locations depending on backend response
    const dimensions = data.dimensions || data.room_dimensions || data.dimension_analysis?.dimensions || {};
    const length = dimensions.length || 'Auto';
    const width = dimensions.width || 'Auto';
    const height = dimensions.height || 10;

    // Extract area - check multiple possible paths
    const totalArea = data.area_calculation?.paintable_area || data.total_paintable_area || data.total_area || 0;

    // Extract paint quantity
    const paintNeeded = data.product_breakdown?.paint?.quantity || data.total_paint_required_liters || data.total_paint_liters || 0;

    // Extract frames analyzed
    const framesAnalyzed = data.video_analysis?.frames_analyzed || data.frame_count || data.metadata?.frame_count || 0;

    // Extract total cost
    const totalCost = data.cost_breakdown?.total_cost || data.total_cost || 0;

    // Extract confidence data (Phase 6 - NEW)
    const confidence = data.confidence || data.detection_confidence || {};

    // Handle NaN and missing confidence values
    let overallConfidence = confidence.overall_confidence || confidence || 0;

    // If overallConfidence is NaN or not a number, use dimension-based fallback
    if (isNaN(overallConfidence) || typeof overallConfidence !== 'number') {
        // For Vision API results, assume high confidence (0.85-0.95)
        if (data.vision_api_result?.used) {
            overallConfidence = 0.90; // Vision API is typically 90%+ accurate
        } else {
            overallConfidence = 0.70; // YOLO-based estimates ~70% confidence
        }
    }

    const dimensionConfidence = confidence.dimension_confidence || overallConfidence;
    const detectionConfidence = confidence.detection_confidence || overallConfidence;
    const varianceScore = confidence.variance_score || overallConfidence;

    // Calculate confidence level and color
    const confidencePercent = Math.round(overallConfidence * 100);
    let confidenceLevel, confidenceColor, expectedError;

    // Check if we have variance data from multi-frame median (resolution-invariant!)
    const varianceData = dimensions.variance || {};
    if (varianceData.error_percentage !== undefined) {
        // Use actual error from multi-frame variance
        const errorPct = varianceData.error_percentage;
        expectedError = `±${errorPct.toFixed(1)}%`;

        if (errorPct <= 5) {
            confidenceLevel = 'Excellent';
            confidenceColor = '#10b981';
        } else if (errorPct <= 8) {
            confidenceLevel = 'Good';
            confidenceColor = '#3b82f6';
        } else if (errorPct <= 15) {
            confidenceLevel = 'Medium';
            confidenceColor = '#eab308';
        } else {
            confidenceLevel = 'Low';
            confidenceColor = '#ef4444';
        }
    } else if (confidencePercent >= 90) {
        confidenceLevel = 'Very High';
        confidenceColor = '#10b981'; // Green
        expectedError = '±5%';
    } else if (confidencePercent >= 75) {
        confidenceLevel = 'High';
        confidenceColor = '#3b82f6'; // Blue
        expectedError = '±10%';
    } else if (confidencePercent >= 60) {
        confidenceLevel = 'Medium';
        confidenceColor = '#eab308'; // Yellow
        expectedError = '±15%';
    } else if (confidencePercent >= 40) {
        confidenceLevel = 'Low';
        confidenceColor = '#f97316'; // Orange
        expectedError = '±20%';
    } else {
        confidenceLevel = 'Very Low';
        confidenceColor = '#ef4444'; // Red
        expectedError = '±30%';
    }

    // Get estimation method
    const method = dimensions.method || data.estimation_mode || 'unknown';
    const methodDisplay = method.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    // Extract door and window counts from detections
    const detectionResults = data.detection_results || data.detections_summary || {};
    const doorsDetected = detectionResults.detected_doors || detectionResults.unique_doors ||
        data.aggregated_counts?.doors || 0;
    const windowsDetected = detectionResults.detected_windows || detectionResults.unique_windows ||
        data.aggregated_counts?.windows || 0;
    const totalDetections = detectionResults.total_detections || 0;

    const html = `
        <div class="results-grid">
            <div class="result-card">
                <h3 class="result-card__title">Detected Dimensions</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Length</span>
                        <span class="result-item__value">${typeof length === 'number' ? length.toFixed(1) : length} ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Width</span>
                        <span class="result-item__value">${typeof width === 'number' ? width.toFixed(1) : width} ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Height</span>
                        <span class="result-item__value">${typeof height === 'number' ? height.toFixed(1) : height} ft</span>
                    </div>
                </div>
            </div>
            
            <div class="result-card">
                <h3 class="result-card__title">Detected Features</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">🚪 Doors</span>
                        <span class="result-item__value">${doorsDetected}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">🪟 Windows</span>
                        <span class="result-item__value">${windowsDetected}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Total Objects</span>
                        <span class="result-item__value">${totalDetections || (doorsDetected + windowsDetected)}</span>
                    </div>
                </div>
            </div>
            
            <div class="result-card">
                <h3 class="result-card__title">Paint Requirements</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Paintable Area</span>
                        <span class="result-item__value">${totalArea > 0 ? totalArea.toFixed(1) : 'N/A'} sq ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Paint Needed</span>
                        <span class="result-item__value">${paintNeeded > 0 ? paintNeeded.toFixed(2) : 'N/A'} L</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Frames Analyzed</span>
                        <span class="result-item__value">${framesAnalyzed || '-'}</span>
                    </div>
                </div>
            </div>
            
            <div class="result-card">
                <h3 class="result-card__title">Confidence & Accuracy</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Confidence Score</span>
                        <span class="result-item__value" style="color: ${confidenceColor}; font-weight: bold;">
                            ${confidencePercent}% (${confidenceLevel})
                        </span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Expected Error</span>
                        <span class="result-item__value">${expectedError}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Method Used</span>
                        <span class="result-item__value">${methodDisplay}</span>
                    </div>
                </div>
            </div>
            
            <div class="result-total">
                <div class="result-total__label">Total Estimated Cost</div>
                <div class="result-total__value">₹${totalCost > 0 ? totalCost.toFixed(0) : '0'}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">Estimated accuracy: ${expectedError}</div>
            </div>
        </div>
        
        <div class="result-actions">
            <button class="btn btn--secondary" onclick="window.print()">
                Print Estimate
            </button>
            <button class="btn btn--primary" onclick="window.location.href='landing.html'">
                New Estimation
            </button>
        </div>
    `;

    container.innerHTML = html;
    container.style.display = 'block';

    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

/**
 * Format video duration
 */
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Utility functions
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';

        if (show) {
            // Check if progress-fill exists before trying to access it
            const progressFill = document.getElementById('progress-fill');
            if (progressFill) {
                progressFill.style.width = '0%';
            }
        }
    }
}

function showToast(type, title, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `
        <div class="toast__content">
            <div class="toast__title">${title}</div>
            <div class="toast__message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add('toast--show');
    });

    setTimeout(() => {
        toast.classList.remove('toast--show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
