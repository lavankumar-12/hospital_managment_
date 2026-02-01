/**
 * SUNRISE HOSPITAL - Advanced Interactions & Animations
 * JavaScript-powered animations and micro-interactions
 * Performance-optimized for 60 FPS
 */

class AnimationController {
    constructor() {
        this.init();
    }

    init() {
        this.setupPageLoad();
        this.setupCounterAnimations();
        this.setupRippleEffects();
        this.setupTooltips();
        this.setupCardAnimations();
        this.checkReducedMotion();
    }

    /**
     * Check for reduced motion preference
     */
    checkReducedMotion() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) {
            document.documentElement.classList.add('reduced-motion');
        }
    }

    /**
     * Page Load Animations with Stagger
     */
    setupPageLoad() {
        const elements = document.querySelectorAll('.animate-on-load');

        elements.forEach((el, index) => {
            el.classList.add('fade-in-up');
            el.classList.add(`stagger-${Math.min(index + 1, 6)}`);
        });
    }

    /**
     * Animated Number Counter
     * @param {HTMLElement} element - Element containing the number
     * @param {number} target - Target number
     * @param {number} duration - Animation duration in ms
     */
    animateCounter(element, target, duration = 1000) {
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16); // 60 FPS
        let current = start;

        const timer = setInterval(() => {
            current += increment;

            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                element.textContent = Math.round(target);
                clearInterval(timer);
                element.classList.add('counter-animate');
                setTimeout(() => element.classList.remove('counter-animate'), 500);
            } else {
                element.textContent = Math.round(current);
            }
        }, 16);
    }

    /**
     * Setup counter animations for all elements with data-counter
     */
    setupCounterAnimations() {
        const counters = document.querySelectorAll('[data-counter]');

        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.counted) {
                    const target = parseInt(entry.target.dataset.counter);
                    const duration = parseInt(entry.target.dataset.duration) || 1000;
                    this.animateCounter(entry.target, target, duration);
                    entry.target.dataset.counted = 'true';
                }
            });
        }, observerOptions);

        counters.forEach(counter => observer.observe(counter));
    }

    /**
     * Ripple Effect on Click
     */
    setupRippleEffects() {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('.btn-animated, .ripple-effect');
            if (!target) return;

            const ripple = document.createElement('span');
            const rect = target.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');

            const existingRipple = target.querySelector('.ripple');
            if (existingRipple) existingRipple.remove();

            target.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    }

    /**
     * Enhanced Tooltip System
     */
    setupTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');

        tooltips.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltipText = element.dataset.tooltip;
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip-animate fixed bg-gray-900 text-white text-sm px-3 py-2 rounded-lg shadow-lg z-50';
                tooltip.textContent = tooltipText;
                tooltip.id = 'active-tooltip';

                document.body.appendChild(tooltip);

                const rect = element.getBoundingClientRect();
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
            });

            element.addEventListener('mouseleave', () => {
                const tooltip = document.getElementById('active-tooltip');
                if (tooltip) tooltip.remove();
            });
        });
    }

    /**
     * Card Entrance Animations with Intersection Observer
     */
    setupCardAnimations() {
        const cards = document.querySelectorAll('.card-animate');

        const observerOptions = {
            threshold: 0.2,
            rootMargin: '50px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('card-entrance');
                }
            });
        }, observerOptions);

        cards.forEach(card => observer.observe(card));
    }

    /**
     * Shake animation for form validation errors
     */
    shakeElement(element) {
        element.classList.add('shake-error');
        setTimeout(() => element.classList.remove('shake-error'), 500);
    }

    /**
     * Show success checkmark animation
     */
    showSuccessCheck(element) {
        const svg = `
            <svg class="w-16 h-16 mx-auto" viewBox="0 0 52 52">
                <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none" stroke="#10B981" stroke-width="2"/>
                <path class="checkmark-draw" fill="none" stroke="#10B981" stroke-width="3" stroke-linecap="round" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
            </svg>
        `;
        element.innerHTML = svg;
    }
}

/**
 * Toast Notification System with Animations
 */
class ToastController {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed bottom-8 right-8 z-50 space-y-3';
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.className = `${colors[type]} text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 min-w-[300px] toast-in`;
        toast.innerHTML = `
            <span class="text-xl font-bold">${icons[type]}</span>
            <span class="font-medium">${message}</span>
            <button class="ml-auto hover:opacity-70 transition" onclick="this.parentElement.classList.add('toast-out'); setTimeout(() => this.parentElement.remove(), 300)">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        `;

        this.container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('toast-out');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

/**
 * Queue Display with Live Updates
 */
class QueueAnimationController {
    constructor(queueElement) {
        this.queueElement = queueElement;
    }

    /**
     * Update queue with flip animation
     */
    updateToken(newToken) {
        if (!this.queueElement) return;

        this.queueElement.classList.add('flip-update');

        setTimeout(() => {
            this.queueElement.textContent = newToken;
            this.queueElement.classList.remove('flip-update');
        }, 300);
    }

    /**
     * Highlight current token
     */
    highlightCurrent(tokenElement) {
        // Remove previous highlights
        document.querySelectorAll('.pulse-current').forEach(el => {
            el.classList.remove('pulse-current');
        });

        // Add highlight to current
        if (tokenElement) {
            tokenElement.classList.add('pulse-current');
        }
    }

    /**
     * Ticker animation for new queue entry
     */
    addToQueue(tokenElement) {
        if (!tokenElement) return;

        tokenElement.classList.add('ticker-slide');
        setTimeout(() => tokenElement.classList.remove('ticker-slide'), 500);
    }
}

/**
 * Shopping Cart Animations
 */
class CartAnimationController {
    constructor(cartIconElement) {
        this.cartIcon = cartIconElement;
        this.cartCount = 0;
    }

    /**
     * Fly to cart animation when item added
     */
    flyToCart(itemElement) {
        if (!itemElement) return;

        const clone = itemElement.cloneNode(true);
        const rect = itemElement.getBoundingClientRect();
        const cartRect = this.cartIcon.getBoundingClientRect();

        clone.style.position = 'fixed';
        clone.style.left = rect.left + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.width = rect.width + 'px';
        clone.style.height = rect.height + 'px';
        clone.style.zIndex = '9999';
        clone.style.pointerEvents = 'none';

        document.body.appendChild(clone);

        // Animate to cart
        setTimeout(() => {
            clone.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            clone.style.left = cartRect.left + 'px';
            clone.style.top = cartRect.top + 'px';
            clone.style.transform = 'scale(0.2)';
            clone.style.opacity = '0';
        }, 10);

        setTimeout(() => {
            clone.remove();
            this.bounceCart();
        }, 850);
    }

    /**
     * Cart badge bounce
     */
    bounceCart() {
        const badge = this.cartIcon.querySelector('.cart-badge');
        if (badge) {
            badge.classList.add('cart-badge-bounce');
            setTimeout(() => badge.classList.remove('cart-badge-bounce'), 400);
        }
    }

    /**
     * Update cart count with animation
     */
    updateCount(newCount) {
        this.cartCount = newCount;
        const badge = this.cartIcon.querySelector('.cart-badge');
        if (badge) {
            badge.textContent = newCount;
            this.bounceCart();
        }
    }
}

/**
 * Modal Controller with Animations
 */
class ModalController {
    show(modalElement) {
        if (!modalElement) return;

        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fixed inset-0 bg-black/50 z-40';
        backdrop.id = 'modal-backdrop';
        document.body.appendChild(backdrop);

        // Show modal
        modalElement.classList.remove('hidden');
        modalElement.classList.add('modal-animate', 'fixed', 'inset-0', 'z-50', 'flex', 'items-center', 'justify-center');
        document.body.style.overflow = 'hidden';

        // Close on backdrop click
        backdrop.addEventListener('click', () => this.hide(modalElement));
    }

    hide(modalElement) {
        if (!modalElement) return;

        const backdrop = document.getElementById('modal-backdrop');
        if (backdrop) backdrop.remove();

        modalElement.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

/**
 * Initialize all animation controllers
 */
document.addEventListener('DOMContentLoaded', () => {
    window.animationController = new AnimationController();
    window.toastController = new ToastController();
    window.modalController = new ModalController();

    // Initialize queue animations if queue element exists
    const queueElement = document.getElementById('current-token');
    if (queueElement) {
        window.queueAnimationController = new QueueAnimationController(queueElement);
    }

    // Initialize cart animations if cart icon exists
    const cartIcon = document.getElementById('cart-icon');
    if (cartIcon) {
        window.cartAnimationController = new CartAnimationController(cartIcon);
    }

    console.log('🎨 Advanced Animation System Loaded');
});

/**
 * Utility Functions
 */

// Show toast notification (shorthand)
function showToast(message, type = 'info', duration = 3000) {
    if (window.toastController) {
        window.toastController.show(message, type, duration);
    }
}

// Shake element on error
function shakeOnError(elementId) {
    const element = document.getElementById(elementId);
    if (element && window.animationController) {
        window.animationController.shakeElement(element);
    }
}

// Show success checkmark
function showSuccess(elementId) {
    const element = document.getElementById(elementId);
    if (element && window.animationController) {
        window.animationController.showSuccessCheck(element);
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AnimationController,
        ToastController,
        QueueAnimationController,
        CartAnimationController,
        ModalController
    };
}
