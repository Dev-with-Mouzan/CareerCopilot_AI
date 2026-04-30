document.addEventListener('DOMContentLoaded', () => {
    console.log('CareerCopilot-AI Frontend Loaded');

    // Add interactivity or fetch data from API here
    const getStartedBtn = document.querySelector('.cta-btn');
    if(getStartedBtn) {
        getStartedBtn.addEventListener('click', (e) => {
            e.preventDefault();
            alert('CareerCopilot-AI Agents are warming up! This feature is coming soon.');
        });
    }

    // Smooth scroll for nav links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add a simple scroll effect to the nav
    window.addEventListener('scroll', () => {
        const nav = document.querySelector('nav');
        if (window.scrollY > 50) {
            nav.style.padding = '1rem 5%';
            nav.style.background = 'rgba(5, 5, 5, 0.9)';
        } else {
            nav.style.padding = '1.5rem 5%';
            nav.style.background = 'rgba(5, 5, 5, 0.5)';
        }
    });
});
