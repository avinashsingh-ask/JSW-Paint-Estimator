/**
 * Floor Plan Estimation - JavaScript Module
 * Handles floor plan upload and result display
 */

// Configuration
const FLOORPLAN_API_URL = 'http://localhost:8000/api/v1/estimate/floorplan';

// DOM Elements
let floorplanUploadInput;
let floorplanPreview;
let floorplanPreviewImg;
let floorplanRemoveBtn;
let floorplanSubmitBtn;
let floorplanCeilingHeight;
let floorplanPaintType;
let floorplanNumCoats;
let floorplanIncludeCeiling;
let floorplanResults;
let floorplanResultsContent;

// State
let selectedFloorplanFile = null;

/**
 * Initialize floor plan upload functionality
 */
function initializeFloorPlanUpload() {
    // Get DOM elements
    floorplanUploadInput = document.getElementById('floorplan-image');
    floorplanPreview = document.getElementById('floorplan-preview');
    floorplanPreviewImg = document.getElementById('floorplan-preview-img');
    floorplanRemoveBtn = document.getElementById('remove-floorplan');
    floorplanSubmitBtn = document.getElementById('floorplan-submit-btn');
    floorplanCeilingHeight = document.getElementById('floorplan_ceiling_height');
    floorplanPaintType = document.getElementById('floorplan_paint_type');
    floorplanNumCoats = document.getElementById('floorplan_num_coats');
    floorplanIncludeCeiling = document.getElementById('floorplan_include_ceiling');
    floorplanResults = document.getElementById('floorplan-results');
    floorplanResultsContent = document.getElementById('floorplan-results-content');

    // Event listeners
    if (floorplanUploadInput) {
        floorplanUploadInput.addEventListener('change', handleFloorPlanSelection);
    }

    if (floorplanRemoveBtn) {
        floorplanRemoveBtn.addEventListener('click', removeFloorPlanImage);
    }

    // Browse button click handler
    const browsebtn = document.getElementById('floorplan-browse-btn');
    if (browsebtn) {
        browsebtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (floorplanUploadInput) floorplanUploadInput.click();
        });
    }

    // Make upload area clickable
    const uploadArea = document.getElementById('floorplan-upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('click', () => floorplanUploadInput?.click());

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

            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type.startsWith('image/')) {
                floorplanUploadInput.files = files;
                handleFloorPlanSelection({ target: floorplanUploadInput });
            }
        });
    }

    // Form submission
    const floorplanForm = document.getElementById('floorplan-form');
    if (floorplanForm) {
        floorplanForm.addEventListener('submit', handleFloorPlanSubmit);
    }

    console.log('✓ Floor plan upload initialized');
}

/**
 * Handle floor plan image selection
 */
function handleFloorPlanSelection(event) {
    const file = event.target.files[0];

    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('Image size must be less than 10MB', 'error');
        return;
    }

    selectedFloorplanFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        if (floorplanPreviewImg) {
            floorplanPreviewImg.src = e.target.result;
        }
        if (floorplanPreview) {
            floorplanPreview.style.display = 'block';
        }

        // Hide upload area
        const uploadArea = document.getElementById('floorplan-upload-area');
        if (uploadArea) {
            uploadArea.style.display = 'none';
        }

        // Enable submit button
        if (floorplanSubmitBtn) {
            floorplanSubmitBtn.disabled = false;
        }
    };
    reader.readAsDataURL(file);
}

/**
 * Remove selected floor plan image
 */
function removeFloorPlanImage() {
    selectedFloorplanFile = null;

    if (floorplanUploadInput) {
        floorplanUploadInput.value = '';
    }

    if (floorplanPreview) {
        floorplanPreview.style.display = 'none';
    }

    if (floorplanPreviewImg) {
        floorplanPreviewImg.src = '';
    }

    // Show upload area
    const uploadArea = document.getElementById('floorplan-upload-area');
    if (uploadArea) {
        uploadArea.style.display = 'flex';
    }

    // Disable submit button
    if (floorplanSubmitBtn) {
        floorplanSubmitBtn.disabled = true;
    }

    // Hide results
    if (floorplanResults) {
        floorplanResults.style.display = 'none';
    }
}

/**
 * Handle floor plan form submission
 */
async function handleFloorPlanSubmit(event) {
    event.preventDefault();

    if (!selectedFloorplanFile) {
        showToast('Please select a floor plan image', 'error');
        return;
    }

    // Get form values
    const ceilingHeight = parseFloat(floorplanCeilingHeight?.value || 10.0);
    const paintType = floorplanPaintType?.value || 'interior';
    const numCoats = parseInt(floorplanNumCoats?.value || 2);
    const includeCeiling = floorplanIncludeCeiling?.checked || false;

    // Prepare form data
    const formData = new FormData();
    formData.append('image', selectedFloorplanFile);
    formData.append('ceiling_height', ceilingHeight);
    formData.append('paint_type', paintType);
    formData.append('num_coats', numCoats);
    formData.append('include_ceiling', includeCeiling);

    // Show loading
    showLoading('Analyzing floor plan...');

    try {
        const response = await fetch(FLOORPLAN_API_URL, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Floor plan analysis failed');
        }

        const result = await response.json();

        if (result.success) {
            displayFloorPlanResults(result.data);
            showToast(result.message || 'Floor plan analyzed successfully!', 'success');
        } else {
            throw new Error('Floor plan analysis failed');
        }
    } catch (error) {
        console.error('Floor plan analysis error:', error);
        showToast(error.message || 'Failed to analyze floor plan', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Display floor plan analysis results
 */
function displayFloorPlanResults(data) {
    if (!floorplanResultsContent) return;

    console.log('Floor plan data received:', data); // Debug log

    // Safely extract data with fallbacks
    const rooms = data.rooms || [];
    const total_rooms = data.total_rooms || 0;
    const total_floor_area = data.total_floor_area || 0;
    const total_paintable_area = data.total_paintable_area || 0;
    const total_paint_required_liters = data.total_paint_required_liters || data.total_paint_required || 0;
    const total_cost = data.total_cost || 0;
    const ocr_metadata = data.ocr_metadata || {};

    // Check if we have valid rooms data
    if (!rooms || rooms.length === 0) {
        floorplanResultsContent.innerHTML = `
            <div style="padding: 2rem; text-align: center; background: #fff3cd; border-radius: 8px;">
                <p style="color: #856404; margin: 0;">⚠️ No rooms with dimensions could be extracted. Please ensure the image contains clear dimension annotations (e.g., "13'2\" x 9'1\"").</p>
            </div>
        `;
        return;
    }

    // Build results HTML
    let html = '<div class="floorplan-results">';

    // OCR Metadata
    html += `
        <div class="ocr-info" style="margin-bottom: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
            <h4 style="margin: 0 0 0.5rem 0;">📊 Extraction Summary</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; font-size: 0.9rem;">
                <div><strong>Rooms Found:</strong> ${total_rooms}</div>
                <div><strong>Dimensions Found:</strong> ${ocr_metadata.dimensions_found || 'N/A'}</div>
                <div><strong>Text Regions:</strong> ${ocr_metadata.text_regions || 'N/A'}</div>
            </div>
        </div>
    `;

    // Rooms Table
    if (rooms && rooms.length > 0) {
        html += `
        <div class="rooms-table-container">
                <h3 style="margin-bottom: 1rem;">Room-by-Room Analysis</h3>
                <div style="overflow-x: auto;">
                    <table class="results-table" style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                <th style="padding: 12px; text-align: left;">Room Name</th>
                                <th style="padding: 12px; text-align: left;">Dimensions</th>
                                <th style="padding: 12px; text-align: right;">Floor Area</th>
                                <th style="padding: 12px; text-align: right;">Wall Area</th>
                                <th style="padding: 12px; text-align: center;">Doors/Windows</th>
                                <th style="padding: 12px; text-align: right;">Paint (L)</th>
                                <th style="padding: 12px; text-align: right;">Cost (₹)</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        rooms.forEach((room, index) => {
            const bgColor = index % 2 === 0 ? '#ffffff' : '#f8f9fa';
            const floorArea = room.areas?.floor_area || 0;
            const paintableArea = room.areas?.paintable_area || 0;
            const paintLiters = room.paint?.liters || 0;
            const cost = room.total_cost || room.cost || 0;
            const dimensions = `${room.dimensions?.length || '?'}' x ${room.dimensions?.width || '?'}'`;

            html += `
                <tr style="background: ${bgColor}; border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 12px; font-weight: 500;">${room.name}</td>
                    <td style="padding: 12px; font-size: 0.9rem;">${dimensions}</td>
                    <td style="padding: 12px; text-align: right;">${floorArea.toFixed(1)} sq ft</td>
                    <td style="padding: 12px; text-align: right;">${paintableArea.toFixed(1)} sq ft</td>
                    <td style="padding: 12px; text-align: center;">${room.num_doors}D / ${room.num_windows}W</td>
                    <td style="padding: 12px; text-align: right; font-weight: 600;">${paintLiters.toFixed(2)}</td>
                    <td style="padding: 12px; text-align: right; font-weight: 600;">₹${cost.toLocaleString()}</td>
                </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // Totals Summary
    html += `
        <div class="totals-summary" style="margin-top: 2rem; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white;">
            <h3 style="margin: 0 0 1.5rem 0; font-size: 1.5rem;">Total Estimate</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
                <div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Total Rooms</div>
                    <div style="font-size: 2rem; font-weight: 700; margin-top: 0.25rem;">${total_rooms}</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Total Floor Area</div>
                    <div style="font-size: 2rem; font-weight: 700; margin-top: 0.25rem;">${total_floor_area.toLocaleString()} sq ft</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Paintable Area</div>
                    <div style="font-size: 2rem; font-weight: 700; margin-top: 0.25rem;">${total_paintable_area.toLocaleString()} sq ft</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Paint Required</div>
                    <div style="font-size: 2rem; font-weight: 700; margin-top: 0.25rem;">${total_paint_required_liters.toFixed(1)} L</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">Total Cost</div>
                    <div style="font-size: 2rem; font-weight: 700; margin-top: 0.25rem;">₹${total_cost.toLocaleString()}</div>
                </div>
            </div>
        </div>
        `;

    html += '</div>';

    // Update results content
    floorplanResultsContent.innerHTML = html;

    // Show results
    if (floorplanResults) {
        floorplanResults.style.display = 'block';

        // Smooth scroll to results
        setTimeout(() => {
            floorplanResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeFloorPlanUpload);
} else {
    initializeFloorPlanUpload();
}
