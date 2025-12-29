/**
 * Manual Input Modal for Phase 4 - Manual Fallback
 * 
 * Shows when confidence is low and requests user measurement.
 */

class ManualInputModal {
    constructor() {
        this.modal = null;
        this.onSubmitCallback = null;
        this.createModal();
    }

    createModal() {
        // Create modal HTML
        const modalHTML = `
            <div class="manual-input-modal" id="manualInputModal">
                <div class="manual-input-modal__content">
                    <div class="manual-input-modal__header">
                        <span class="manual-input-modal__icon">📏</span>
                        <h2 class="manual-input-modal__title">Manual Measurement Needed</h2>
                    </div>
                    
                    <p class="manual-input-modal__message" id="modalMessage">
                        We need your help! The automated estimation has low confidence.
                        Please provide one measurement to improve accuracy.
                    </p>
                    
                    <div class="manual-input-modal__confidence" id="modalConfidence">
                        <span class="manual-input-modal__confidence-text">
                            Current confidence: <span id="confidenceValue">--</span>%
                        </span>
                    </div>
                    
                    <form class="manual-input-form" id="manualInputForm">
                        <div class="manual-input-form__group">
                            <label class="manual-input-form__label" for="ceilingHeight">
                                Ceiling Height (feet)
                            </label>
                            <input 
                                type="number" 
                                id="ceilingHeight" 
                                class="manual-input-form__input"
                                placeholder="e.g., 10"
                                step="0.1"
                                min="6"
                                max="20"
                                required
                            />
                            <span class="manual-input-form__help">
                                Measure from floor to ceiling. Typical range: 8-12 feet
                            </span>
                        </div>
                        
                        <div class="manual-input-form__actions">
                            <button 
                                type="button" 
                                class="manual-input-form__button manual-input-form__button--secondary"
                                id="modalSkip"
                            >
                                Skip (Use Auto)
                            </button>
                            <button 
                                type="submit" 
                                class="manual-input-form__button manual-input-form__button--primary"
                            >
                                Use My Measurement
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Append to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        this.modal = document.getElementById('manualInputModal');
        this.setupEventListeners();
    }

    setupEventListeners() {
        const form = document.getElementById('manualInputForm');
        const skipBtn = document.getElementById('modalSkip');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const ceilingHeight = parseFloat(document.getElementById('ceilingHeight').value);

            if (ceilingHeight && this.onSubmitCallback) {
                this.onSubmitCallback({
                    ceiling_height: ceilingHeight,
                    user_provided: true
                });
            }

            this.hide();
        });

        skipBtn.addEventListener('click', () => {
            if (this.onSubmitCallback) {
                this.onSubmitCallback({
                    user_provided: false,
                    skipped: true
                });
            }
            this.hide();
        });
    }

    show(data = {}) {
        const {
            confidence = 0,
            reason = 'Low confidence in automated estimation',
            currentEstimate = null
        } = data;

        // Update modal content
        document.getElementById('modalMessage').textContent = reason;
        document.getElementById('confidenceValue').textContent = Math.round(confidence * 100);

        // Pre-fill with current estimate if available
        if (currentEstimate && currentEstimate.height) {
            document.getElementById('ceilingHeight').value = currentEstimate.height.toFixed(1);
        }

        // Show modal
        this.modal.classList.add('active');
    }

    hide() {
        this.modal.classList.remove('active');
        document.getElementById('manualInputForm').reset();
    }

    onSubmit(callback) {
        this.onSubmitCallback = callback;
    }
}

// Export for use in video-estimation-new.js
if (typeof window !== 'undefined') {
    window.ManualInputModal = ManualInputModal;
}
