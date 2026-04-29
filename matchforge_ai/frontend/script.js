document.addEventListener('DOMContentLoaded', () => {
    console.log('MatchForge-AI Frontend Loaded');

    const startBtn = document.getElementById('start-matching');
    
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            alert('MatchForge-AI Agents are warming up! This feature is coming soon.');
            console.log('User clicked Start Matching');
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
