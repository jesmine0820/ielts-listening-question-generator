// Generate floating particles
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        
        // Random properties
        const size = Math.random() * 5 + 2;
        const posX = Math.random() * 100;
        const duration = Math.random() * 20 + 10;
        const delay = Math.random() * 5;
        const opacity = Math.random() * 0.3 + 0.1;
        
        // Apply styles
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}%`;
        particle.style.background = `rgba(255, ${Math.random() * 50 + 50}, ${Math.random() * 50 + 50}, ${opacity})`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        
        particlesContainer.appendChild(particle);
    }
}

// Mouse interaction effect
function setupMouseInteraction() {
    document.addEventListener('mousemove', (e) => {
        const shapes = document.querySelectorAll('.shape');
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        shapes.forEach((shape, index) => {
            // Store original transform from CSS animation
            const computedStyle = window.getComputedStyle(shape);
            const originalTransform = computedStyle.transform;
            
            const speed = 0.3 + (index * 0.05);
            const x = (mouseX * 30 * speed) - 15;
            const y = (mouseY * 30 * speed) - 15;
            
            // Apply parallax effect without overriding animation
            shape.style.transform = `${originalTransform} translate(${x}px, ${y}px)`;
        });
    });
}

// Reset mouse effect when mouse leaves the window
function setupMouseLeaveReset() {
    document.addEventListener('mouseleave', () => {
        const shapes = document.querySelectorAll('.shape');
        shapes.forEach(shape => {
            // Clear the inline transform to revert to CSS animation
            shape.style.transform = '';
        });
    });
}

// Initialize background effects
function initBackgroundEffects() {
    // Create particles container if it doesn't exist
    if (!document.getElementById('particles')) {
        const particlesDiv = document.createElement('div');
        particlesDiv.id = 'particles';
        particlesDiv.classList.add('particles');
        document.body.appendChild(particlesDiv);
    }
    
    // Initialize all effects
    createParticles();
    setupMouseInteraction();
    setupMouseLeaveReset();
}

// Initialize when DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBackgroundEffects);
} else {
    initBackgroundEffects();
}

// Handle window resize
window.addEventListener('resize', () => {
    // Clear and recreate particles on resize for better positioning
    const particlesContainer = document.getElementById('particles');
    if (particlesContainer) {
        particlesContainer.innerHTML = '';
        createParticles();
    }
});