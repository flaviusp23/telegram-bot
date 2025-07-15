// Main JavaScript file for Erasmus Admin Panel

// API base URL
const API_BASE_URL = '/api/v1';

// Utility function for making API requests
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = localStorage.getItem('access_token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
    };
    
    // Add Authorization header if token exists
    if (token) {
        defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        console.log('API Request with token:', endpoint);
    } else {
        console.log('API Request without token:', endpoint);
    }
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            console.error(`API Error: ${response.status} ${response.statusText} for ${endpoint}`);
            const error = await response.json();
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Check authentication status
async function checkAuth() {
    try {
        const response = await apiRequest('/auth/me');
        return response;
    } catch (error) {
        return null;
    }
}

// Logout function
async function logout() {
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            await apiRequest('/auth/logout', { 
                method: 'POST',
                body: JSON.stringify({ refresh_token: refreshToken })
            });
        }
    } catch (error) {
        console.error('Logout failed:', error);
    } finally {
        // Clear tokens from localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Update navbar before redirecting
        updateNavbar(false);
        window.location.href = '/login';
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return '-';
    
    // Parse the date string and ensure it's interpreted correctly
    let date = new Date(dateString);
    
    // If the date string doesn't have timezone info, treat it as UTC
    if (!dateString.includes('T') || (!dateString.includes('Z') && !dateString.includes('+'))) {
        // This is likely a MySQL timestamp without timezone - treat as UTC
        date = new Date(dateString + 'Z');
    }
    
    // Format in user's local timezone
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Update navbar based on auth status
function updateNavbar(isAuthenticated, user = null) {
    const navbar = document.querySelector('.navbar');
    const footer = document.querySelector('.footer');
    const authNavItem = document.getElementById('auth-nav-item');
    
    if (navbar) {
        if (isAuthenticated && user) {
            // Show navbar and update auth item
            navbar.style.display = 'block';
            if (footer) footer.style.display = 'block';
            if (authNavItem) {
                authNavItem.innerHTML = `
                    <a href="#" onclick="logout(); return false;" style="cursor: pointer;">
                        Logout (${user.username})
                    </a>
                `;
            }
        } else {
            // Hide navbar and footer when not authenticated
            navbar.style.display = 'none';
            if (footer) footer.style.display = 'none';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    const currentPath = window.location.pathname;
    const protectedPaths = ['/dashboard', '/users', '/settings'];
    const publicPaths = ['/', '/login'];
    
    // Check authentication status
    const user = await checkAuth();
    
    // Update navbar
    updateNavbar(!!user, user);
    
    // Handle routing based on auth status
    if (user) {
        // User is logged in
        if (currentPath === '/login' || currentPath === '/') {
            // Redirect to dashboard if on login or home page
            window.location.href = '/dashboard';
        }
    } else {
        // User is not logged in
        if (protectedPaths.includes(currentPath)) {
            // Redirect to login if trying to access protected page
            window.location.href = '/login';
        }
    }
    
    // Add logout handler if logout button exists
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

// Export functions for use in other scripts
window.erasmusAdmin = {
    apiRequest,
    checkAuth,
    logout,
    formatDate,
    showNotification,
    updateNavbar,
};