// Landing Page JavaScript
// Handles interactions and animations for the landing page

document.addEventListener('DOMContentLoaded', () => {
    initializeHelpButton();
    addCardAnimations();
});

/**
 * Initialize help button functionality
 */
function initializeHelpButton() {
    const helpBtn = document.getElementById('help-btn');

    if (helpBtn) {
        helpBtn.addEventListener('click', () => {
            showHelpModal();
        });
    }
}

/**
 * Add hover effect enhancements to mode cards
 */
function addCardAnimations() {
    const modeCards = document.querySelectorAll('.mode-card');

    modeCards.forEach(card => {
        // Add subtle scale animation on mouse move
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            card.style.transform = `translateY(-6px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
}

/**
 * Show help modal
 */
function showHelpModal() {
    const modal = createHelpModal();
    document.body.appendChild(modal);

    // Trigger animation
    requestAnimationFrame(() => {
        modal.classList.add('modal--open');
    });
}

/**
 * Create help modal element
 */
function createHelpModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal__backdrop"></div>
        <div class="modal__content">
            <div class="modal__header">
                <h2 class="modal__title">How to Use JSW Paint Estimator</h2>
                <button class="modal__close" aria-label="Close">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 6l8 8M14 6l-8 8"/>
                    </svg>
                </button>
            </div>
            <div class="modal__body">
                <h3 style="margin-bottom: 1rem; font-size: 1.1rem;">Choose Your Method:</h3>
                <ul style="line-height: 1.8; color: var(--text-secondary);">
                    <li><strong>Blueprint:</strong> Upload floor plans for multi-room estimation</li>
                    <li><strong>Video:</strong> Record a room walkthrough for automatic analysis</li>
                    <li><strong>Multiple Walls:</strong> Upload 2-4 images for large rooms</li>
                    <li><strong>Single Wall:</strong> Quick estimation from one photo</li>
                    <li><strong>Manual:</strong> Enter dimensions for instant calculation</li>
                </ul>
            </div>
            <div class="modal__footer">
                <button class="btn btn--primary modal-close-btn">Got it</button>
            </div>
        </div>
    `;

    // Add close handlers
    const closeBtn = modal.querySelector('.modal__close');
    const modalCloseBtn = modal.querySelector('.modal-close-btn');
    const backdrop = modal.querySelector('.modal__backdrop');

    const closeModal = () => {
        modal.classList.remove('modal--open');
        setTimeout(() => modal.remove(), 300);
    };

    closeBtn.addEventListener('click', closeModal);
    modalCloseBtn.addEventListener('click', closeModal);
    backdrop.addEventListener('click', closeModal);

    return modal;
}
