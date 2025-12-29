// Image Estimation - Handles both single and multi-wall modes
// Premium UI with drag-drop upload and backend integration

const API_BASE_URL = 'http://localhost:8000/api/v1';
let uploadedImages = [];
let currentMode = 'single'; // 'single' or 'multi'

document.addEventListener('DOMContentLoaded', () => {
    initializePage();
    setupUploadHandlers();
});

/**
 * Initialize page based on URL parameter
 */
function initializePage() {
    const params = new URLSearchParams(window.location.search);
    const mode = params.get('mode') || 'single';

    currentMode = mode;

    if (mode === 'multi') {
        showMultiMode();
    } else {
        showSingleMode();
    }
}

/**
 * Show single wall mode
 */
function showSingleMode() {
    document.getElementById('page-title').textContent = 'Single Wall Estimation';
    document.getElementById('page-subtitle').textContent = 'Upload one room image for quick estimation';
    document.getElementById('single-upload-container').style.display = 'block';
    document.getElementById('multi-upload-container').style.display = 'none';
}

/**
 * Show multi wall mode
 */
function showMultiMode() {
    document.getElementById('page-title').textContent = 'Multi-Wall Estimation';
    document.getElementById('page-subtitle').textContent = 'Upload 2-4 wall images for comprehensive large room analysis';
    document.getElementById('single-upload-container').style.display = 'none';
    document.getElementById('multi-upload-container').style.display = 'block';
}

/**
 * Setup upload handlers
 */
function setupUploadHandlers() {
    // Single image upload
    const singleInput = document.getElementById('single-image-input');
    const singleDropZone = document.getElementById('single-drop-zone');
    const singleForm = document.getElementById('single-upload-form');

    if (singleInput && singleDropZone) {
        singleInput.addEventListener('change', handleSingleImageSelect);
        setupDragDrop(singleDropZone, handleSingleImageDrop);
    }

    if (singleForm) {
        singleForm.addEventListener('submit', handleSingleSubmit);
    }

    // Multi image upload
    const multiInput = document.getElementById('multi-image-input');
    const multiDropZone = document.getElementById('multi-drop-zone');
    const multiForm = document.getElementById('multi-upload-form');

    if (multiInput && multiDropZone) {
        multiInput.addEventListener('change', handleMultiImageSelect);
        setupDragDrop(multiDropZone, handleMultiImageDrop);
    }

    if (multiForm) {
        multiForm.addEventListener('submit', handleMultiSubmit);
    }
}

/**
 * Setup drag and drop for upload zone
 */
function setupDragDrop(element, onDrop) {
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
        onDrop(e.dataTransfer.files);
    });

    // Click to upload
    element.addEventListener('click', (e) => {
        if (e.target === element || e.target.closest('.upload-zone__icon, .upload-zone__title')) {
            if (currentMode === 'single') {
                document.getElementById('single-image-input').click();
            } else {
                document.getElementById('multi-image-input').click();
            }
        }
    });
}

/**
 * Handle single image selection
 */
function handleSingleImageSelect(e) {
    const file = e.target.files[0];
    if (file) {
        displaySingleImage(file);
    }
}

/**
 * Handle single image drop
 */
function handleSingleImageDrop(files) {
    if (files.length > 0) {
        displaySingleImage(files[0]);
    }
}

/**
 * Display single image preview
 */
function displaySingleImage(file) {
    if (!file.type.startsWith('image/')) {
        showToast('error', 'Invalid File', 'Please upload an image file');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('single-preview-img').src = e.target.result;
        document.getElementById('single-preview').style.display = 'block';
        document.getElementById('single-options').style.display = 'block';
        document.getElementById('single-drop-zone').style.display = 'none';
        uploadedImages = [file];
    };
    reader.readAsDataURL(file);
}

/**
 * Remove single image
 */
function removeSingleImage() {
    document.getElementById('single-preview').style.display = 'none';
    document.getElementById('single-options').style.display = 'none';
    document.getElementById('single-drop-zone').style.display = 'flex';
    document.getElementById('single-image-input').value = '';
    uploadedImages = [];
}

/**
 * Handle multi image selection
 */
function handleMultiImageSelect(e) {
    const files = Array.from(e.target.files);
    addMultipleImages(files);
}

/**
 * Handle multi image drop
 */
function handleMultiImageDrop(files) {
    const fileArray = Array.from(files);
    addMultipleImages(fileArray);
}

/**
 * Add multiple images
 */
function addMultipleImages(files) {
    const imageFiles = files.filter(f => f.type.startsWith('image/'));

    if (imageFiles.length === 0) {
        showToast('error', 'Invalid Files', 'Please upload image files');
        return;
    }

    if (uploadedImages.length + imageFiles.length > 4) {
        showToast('warning', 'Too Many Images', 'Maximum 4 images allowed');
        return;
    }

    uploadedImages.push(...imageFiles);
    displayMultiImages();
}

/**
 * Display multiple images grid
 */
function displayMultiImages() {
    const grid = document.getElementById('wall-grid');
    const count = document.getElementById('wall-count');

    grid.innerHTML = '';
    count.textContent = uploadedImages.length;

    uploadedImages.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.style.position = 'relative';
            div.innerHTML = `
                <img src="${e.target.result}" style="width: 100%; border-radius: 12px; box-shadow: var(--shadow-md);">
                <button type="button" class="btn btn--tertiary btn--sm" style="margin-top: 0.5rem; width: 100%;" onclick="removeMultiImage(${index})">
                    Remove
                </button>
            `;
            grid.appendChild(div);
        };
        reader.readAsDataURL(file);
    });

    document.getElementById('multi-preview-grid').style.display = 'block';
    document.getElementById('multi-options').style.display = 'block';
    document.getElementById('multi-drop-zone').style.display = uploadedImages.length < 4 ? 'flex' : 'none';
}

/**
 * Remove image from multi upload
 */
function removeMultiImage(index) {
    uploadedImages.splice(index, 1);
    displayMultiImages();

    if (uploadedImages.length === 0) {
        document.getElementById('multi-preview-grid').style.display = 'none';
        document.getElementById('multi-options').style.display = 'none';
        document.getElementById('multi-drop-zone').style.display = 'flex';
    }
}

/**
 * Handle single image form submission
 */
async function handleSingleSubmit(e) {
    e.preventDefault();

    if (uploadedImages.length === 0) {
        showToast('warning', 'No Image', 'Please upload an image first');
        return;
    }

    const formData = new FormData();
    formData.append('image', uploadedImages[0]);
    formData.append('room_type', document.getElementById('single_room_type').value);
    formData.append('paint_type', document.getElementById('single_paint_type').value);
    formData.append('num_coats', '2');

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/estimate/cv/single-room`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
        showToast('success', 'Analysis Complete', 'Room dimensions extracted successfully');

    } catch (error) {
        console.error('Error:', error);
        showToast('error', 'Analysis Failed', 'Please try again with a clearer image');
    } finally {
        showLoading(false);
    }
}

/**
 * Handle multi image form submission
 */
async function handleMultiSubmit(e) {
    e.preventDefault();

    if (uploadedImages.length < 2) {
        showToast('warning', 'Not Enough Images', 'Please upload at least 2 wall images');
        return;
    }

    const formData = new FormData();
    uploadedImages.forEach(file => {
        formData.append('images', file);
    });

    // Create room data array (one config per image)
    const roomData = uploadedImages.map((file, index) => ({
        room_type: document.getElementById('multi_room_type').value,
        room_name: `Wall ${index + 1}`,
        paint_type: document.getElementById('multi_paint_type').value,
        num_coats: parseInt('2'),
        include_ceiling: false
    }));

    // Send as JSON string
    formData.append('room_data', JSON.stringify(roomData));

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/estimate/cv/multi-room`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
        showToast('success', 'Analysis Complete', 'Multi-wall estimation completed');

    } catch (error) {
        console.error('Error:', error);
        showToast('error', 'Analysis Failed', 'Please try again');
    } finally {
        showLoading(false);
    }
}

/**
 * Display results (reuse manual estimation display function)
 */
function displayResults(response) {
    const container = document.getElementById('results-container');
    if (!container) return;

    // Extract data - handle both single and multi-room responses
    const data = response.data || response;
    console.log('🔍 Response:', response);
    console.log('🔍 Data keys:', Object.keys(data));

    // For multi-room, get dimensions from first room
    let dimensions = {};
    if (data.rooms && data.rooms.length > 0) {
        const firstRoom = data.rooms[0];
        console.log('🔍 First room:', firstRoom);
        // Try estimation.dimensions first, then estimation itself
        dimensions = firstRoom.estimation?.dimensions || firstRoom.estimation || {};
    } else {
        dimensions = data.dimensions || {};
    }
    console.log('🔍 Dimensions:', dimensions);

    // Extract values
    let length = dimensions.length || 0;
    let width = dimensions.width || 0;
    let height = dimensions.height || 0;

    // If dimensions are not available, try to estimate from area
    const paintableArea = data.total_paintable_area || data.area_calculation?.paintable_area;
    if (length === 0 && width === 0 && paintableArea) {
        // Rough estimation: assume square room, calculate from total area
        // Total paintable area ≈ 2 * (length + width) * height
        // Assuming standard height of 10ft
        const estimatedHeight = 10;
        const roomCount = (data.rooms && data.rooms.length) || 1; // Default to 1 for single wall
        const wallArea = paintableArea / roomCount; // Area per wall
        // For a rectangular room: wall_area ≈ (L + W) * H / 2 for one wall
        const perimeter = (wallArea * 2) / estimatedHeight;
        // Assume square room for simplicity
        const estimatedSide = perimeter / 2;

        length = estimatedSide;
        width = estimatedSide;
        height = estimatedHeight;
        console.log('📐 Estimated dimensions from area:', { length, width, height });
    }

    const html = `
        <div class="results-grid">
            <div class="result-card">
                <h3 class="result-card__title">Surface Details</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Paintable Area</span>
                        <span class="result-item__value">${(data.total_paintable_area || data.area_calculation?.paintable_area || 0).toFixed(1)} sq ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Paint Required</span>
                        <span class="result-item__value">${(data.total_paint_required || data.product_breakdown?.paint?.quantity || 0).toFixed(2)} L</span>
                    </div>
                </div>
            </div>
            
            <div class="result-card">
                <h3 class="result-card__title">Detected Dimensions</h3>
                <div class="result-card__content">
                    <div class="result-item">
                        <span class="result-item__label">Length</span>
                        <span class="result-item__value">${length > 0 ? length.toFixed(1) : 'Auto'} ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Width</span>
                        <span class="result-item__value">${width > 0 ? width.toFixed(1) : 'Auto'} ft</span>
                    </div>
                    <div class="result-item">
                        <span class="result-item__label">Height</span>
                        <span class="result-item__value">${height > 0 ? height.toFixed(1) : 'Auto'} ft</span>
                    </div>
                </div>
            </div>
            
            <div class="result-total">
                <div class="result-total__label">Total Estimated Cost</div>
                <div class="result-total__value">₹${(data.total_cost || data.cost_breakdown?.total_cost || 0).toFixed(0)}</div>
            </div>
        </div>
        
        <div class="result-actions">
            <button class="btn btn--secondary" onclick="window.location.href='landing.html'">
                New Estimate
            </button>
        </div>
    `;

    container.innerHTML = html;
    container.style.display = 'block';

    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Reuse utility functions from manual estimation
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
