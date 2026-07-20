// Main JavaScript for Café Rodante Crepipuntos

document.addEventListener("DOMContentLoaded", function() {
    // Sidebar drawer toggle logic
    const menuToggle = document.getElementById('menuToggle');
    const closeSidebar = document.getElementById('closeSidebar');
    const sidebar = document.getElementById('appSidebar');

    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.add('active');
        });
    }

    if (closeSidebar && sidebar) {
        closeSidebar.addEventListener('click', function() {
            sidebar.classList.remove('active');
        });
    }

    // Close sidebar on tapping outside on mobile
    document.addEventListener('click', function(event) {
        if (sidebar && sidebar.classList.contains('active')) {
            const isClickInside = sidebar.contains(event.target) || menuToggle.contains(event.target);
            if (!isClickInside) {
                sidebar.classList.remove('active');
            }
        }
    });
});

/**
 * Dynamically displays a premium toast flash notification on the screen
 * @param {string} message The text to display
 * @param {string} type 'success', 'error', or 'info'
 */
function showFlashMessage(message, type = 'info') {
    let container = document.querySelector('.messages-container');
    
    // Create container if it doesn't exist
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        const main = document.querySelector('.app-content');
        if (main) {
            main.insertBefore(container, main.firstChild);
        } else {
            document.body.appendChild(container);
        }
    }
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    
    // Pick icon
    let iconClass = 'fa-circle-info';
    if (type === 'success') iconClass = 'fa-circle-check';
    if (type === 'error' || type === 'danger') iconClass = 'fa-circle-xmark';
    
    alertDiv.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
        <button class="close-alert" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></button>
    `;
    
    // Append to container
    container.appendChild(alertDiv);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateY(-10px)';
        alertDiv.style.transition = 'all 0.4s ease-out';
        setTimeout(() => {
            alertDiv.remove();
        }, 400);
    }, 4000);
}
