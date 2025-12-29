// Blueprint Estimation - Floor Plan Analysis
// Premium UI with automated room detection

const API_BASE_URL = 'http://localhost:8000/api/v1';
let uploadedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    setupUploadHandlers();
});

/**
 * Setup upload handlers
 */
function setupUploadHandlers() {
    const input = document.getElementById('blueprint-input');
    const dropZone = document.getElementById('blueprint-drop-zone');
    const form = document.getElementById('blueprint-form');

    if (input) {
        input.addEventListener('change', handleFileSelect);
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
            handleFileDrop(files[0]);
        }
    });

    // Click to upload
    element.addEventListener('click', (e) => {
        if (e.target === element || e.target.closest('.upload-zone__icon, .upload-zone__title')) {
            document.getElementById('blueprint-input').click();
        }
    });
}

/**
 * Handle file selection
 */
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        displayBlueprint(file);
    }
}

/**
 * Handle file drop
 */
function handleFileDrop(file) {
    displayBlueprint(file);
}

/**
 * Display blueprint preview
 */
function displayBlueprint(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
        showToast('error', 'Invalid File Type', 'Please upload an image or PDF floor plan');
        return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('error', 'File Too Large', 'Please upload a file smaller than 10MB');
        return;
    }

    uploadedFile = file;

    // For images, show preview
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('blueprint-preview-img').src = e.target.result;
            document.getElementById('blueprint-preview').style.display = 'block';
            document.getElementById('config-section').style.display = 'block';
            document.getElementById('upload-section').querySelector('.upload-zone').style.display = 'none';
        };
        reader.readAsDataURL(file);
    } else {
        // For PDF, show placeholder
        document.getElementById('blueprint-preview-img').src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect width="400" height="300" fill="%23f5f5f5"/><text x="50%" y="50%" text-anchor="middle" font-family="Arial" font-size="20" fill="%23666">PDF Floor Plan Uploaded</text></svg>';
        document.getElementById('blueprint-preview').style.display = 'block';
        document.getElementById('config-section').style.display = 'block';
        document.getElementById('upload-section').querySelector('.upload-zone').style.display = 'none';
    }

    showToast('success', 'Floor Plan Uploaded', 'Please configure settings and submit');
}

/**
 * Remove blueprint
 */
function removeBlueprint() {
    uploadedFile = null;
    document.getElementById('blueprint-preview').style.display = 'none';
    document.getElementById('config-section').style.display = 'none';
    document.getElementById('upload-section').querySelector('.upload-zone').style.display = 'flex';
    document.getElementById('blueprint-input').value = '';
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    if (!uploadedFile) {
        showToast('warning', 'No Floor Plan', 'Please upload a floor plan first');
        return;
    }

    const formData = new FormData();
    formData.append('image', uploadedFile);
    formData.append('ceiling_height', document.getElementById('ceiling_height').value);
    formData.append('paint_type', document.getElementById('paint_type').value);
    formData.append('num_coats', '2'); // Default
    formData.append('include_ceiling', document.getElementById('include_ceiling').checked ? 'true' : 'false');

    showLoading(true);

    try {

        const response = await fetch(`${API_BASE_URL}/estimate/floorplan`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const responseData = await response.json();

        // Backend wraps response in {success: true, data: {...}, message: "..."}
        // Extract the actual data
        const data = responseData.data || responseData;

        console.log('Received data:', data); // Debug log

        displayResults(data);
        showToast('success', 'Analysis Complete', responseData.message || 'Floor plan analyzed successfully');

    } catch (error) {
        console.error('Error:', error);
        showToast('error', 'Analysis Failed', 'Please ensure the floor plan is clear and try again');
    } finally {
        showLoading(false);
    }
}


/**
 * Display results
 */
function displayResults(data) {
    const container = document.getElementById('results-container');
    if (!container) return;

    console.log('Full backend response:', data); // Debug

    // Check if we have multi-room data
    const isMultiRoom = data.rooms && Array.isArray(data.rooms);

    let roomsHTML = '';
    if (isMultiRoom) {
        roomsHTML = `
            <div class="result-card" style="grid-column: 1 / -1;">
                <h3 class="result-card__title">Detected Rooms</h3>
                <div class="result-card__content">
                    ${data.rooms.map((room, index) => {
            // Backend returns nested: room.areas.floor_area
            const floorArea = room.areas?.floor_area || 0;

            return `
                            <div class="result-item">
                                <span class="result-item__label">${room.name || `Room ${index + 1}`}</span>
                                <span class="result-item__value">${floorArea > 0 ? floorArea.toFixed(1) : 'N/A'} sq ft</span>
                            </div>
                        `;
        }).join('')}
                </div>
            </div>
        `;
    }

    // Backend returns both floor area and paintable (wall) area
    // Show FLOOR area to match individual room totals
    const paintLiters = data.total_paint_required_liters || 0;
    const totalFloorArea = data.total_floor_area || 0;  // FLOOR area (matches room sum)
    const totalPaintableArea = data.total_paintable_area || 0;  // WALL area (for reference)

    const html = `
        <div class="results-grid">
            ${roomsHTML}
            
            <div class="result-card">
                <h3 class="result-card__title">Total Summary</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Total Floor Area</span>
                        <span class="result-item__value">${totalFloorArea > 0 ? totalFloorArea.toFixed(1) : 'N/A'} sq ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Paintable Wall Area</span>
                        <span class="result-item__value">${totalPaintableArea > 0 ? totalPaintableArea.toFixed(1) : 'N/A'} sq ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Paint Required</span>
                        <span class="result-item__value">${paintLiters > 0 ? paintLiters.toFixed(2) : 'N/A'} L</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Rooms Detected</span>
                        <span class="result-item__value">${data.total_rooms || 0}</span>
                    </div>
                </div>
            </div>

            <div class="result-card">
                <h3 class="result-card__title">Configuration</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Ceiling Height</span>
                        <span class="result-item__value">${document.getElementById('ceiling_height').value} ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Paint Type</span>
                        <span class="result-item__value">${document.getElementById('paint_type').value}</span>
                    </div>
                </div>
            </div>
            
            <div class="result-total">
                <div class="result-total__label">Total Estimated Cost</div>
                <div class="result-total__value">₹${data.total_cost?.toFixed(0) || '0'}</div>
            </div>
        </div>
        
        <div class="result-actions">
            <button class="btn btn--secondary" onclick="window.print()">
                Print Detailed Report
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

// Utility functions
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
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
