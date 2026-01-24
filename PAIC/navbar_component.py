# Navbar Component Template
# This can be imported and used across different pages

NAVBAR_COMPONENT = """
<style>
/* Navbar Styles */
.navbar {
    background: linear-gradient(135deg, #00264D, #00498D);
    padding: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.navbar-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
}

.navbar-brand {
    font-size: 24px;
    font-weight: bold;
    color: #FFFADA;
    padding: 15px 0;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 10px;
}

.navbar-brand:hover {
    color: #FFCC00;
    transition: color 0.3s ease;
}

.navbar-tabs {
    display: flex;
    gap: 0;
    list-style: none;
    margin: 0;
    padding: 0;
}

.navbar-tab {
    position: relative;
}

.navbar-tab a {
    display: block;
    padding: 20px 24px;
    color: #FFFADA;
    text-decoration: none;
    font-weight: 500;
    font-size: 16px;
    transition: all 0.3s ease;
    border-bottom: 3px solid transparent;
}

.navbar-tab a:hover {
    background: rgba(255, 250, 218, 0.1);
    border-bottom-color: #FFCC00;
}

.navbar-tab.active a {
    background: rgba(255, 250, 218, 0.15);
    border-bottom-color: #FFFADA;
    color: #FFFFFF;
}

/* Mobile Menu Toggle */
.navbar-toggle {
    display: none;
    background: none;
    border: none;
    color: #FFFADA;
    font-size: 28px;
    cursor: pointer;
    padding: 10px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .navbar-toggle {
        display: block;
    }
    
    .navbar-tabs {
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #00264D;
        flex-direction: column;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .navbar-tabs.active {
        display: flex;
    }
    
    .navbar-tab a {
        border-bottom: 1px solid rgba(255, 250, 218, 0.1);
        border-left: 3px solid transparent;
    }
    
    .navbar-tab a:hover,
    .navbar-tab.active a {
        border-bottom-color: rgba(255, 250, 218, 0.1);
        border-left-color: #FFCC00;
    }
}
</style>

<nav class="navbar">
    <div class="navbar-container">
        <a href="/" class="navbar-brand">
            <span>🏢</span>
            <span>Business Builder</span>
        </a>
        
        <button class="navbar-toggle" onclick="toggleMobileMenu()">☰</button>
        
        <ul class="navbar-tabs" id="navbarTabs">
            {{TABS}}
        </ul>
    </div>
</nav>

<script>
function toggleMobileMenu() {
    const tabs = document.getElementById('navbarTabs');
    tabs.classList.toggle('active');
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
    const navbar = document.querySelector('.navbar');
    const tabs = document.getElementById('navbarTabs');
    const toggle = document.querySelector('.navbar-toggle');
    
    if (!navbar.contains(event.target) && tabs.classList.contains('active')) {
        tabs.classList.remove('active');
    }
});
</script>
"""

def create_navbar(tabs, active_tab=None):
    """
    Create a navbar with the specified tabs.
    
    Args:
        tabs: List of tuples (label, url) for each tab
              Example: [("Home", "/"), ("Results", "/result"), ("About", "/about")]
        active_tab: The label of the currently active tab (optional)
    
    Returns:
        HTML string for the navbar
    """
    tab_html = ""
    for label, url in tabs:
        active_class = 'class="active"' if label == active_tab else ''
        tab_html += f'<li class="navbar-tab" {active_class}><a href="{url}">{label}</a></li>\n            '
    
    return NAVBAR_COMPONENT.replace("{{TABS}}", tab_html.strip())
