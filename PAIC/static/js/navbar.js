// Navbar Component JavaScript

function toggleMobileMenu() {
    const tabs = document.getElementById('navbarTabs');
    tabs.classList.toggle('active');
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
    const navbar = document.querySelector('.navbar');
    const tabs = document.getElementById('navbarTabs');
    const toggle = document.querySelector('.navbar-toggle');
    
    if (!navbar.contains(event.target) && tabs && tabs.classList.contains('active')) {
        tabs.classList.remove('active');
    }
});
