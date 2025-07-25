// Main JavaScript file for Erasmus Admin Panel

// Constants
const API_BASE_URL = '/api/v1';
const NOTIFICATION_TIMEOUT_MS = 5000;

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
    }

    try {
        const response = await fetch(url, { ...defaultOptions, ...options });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
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
        // Logout failed, but continue with cleanup
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
    }, NOTIFICATION_TIMEOUT_MS);
}

// Update navbar based on auth status
function updateNavbar(isAuthenticated, user = null) {
    const navbar = document.querySelector('.navbar');
    const footer = document.querySelector('.footer');
    const authNavItem = document.getElementById('auth-nav-item');
    const navLinks = document.querySelectorAll('.nav-links li:not(.language-selector-container):not(#auth-nav-item)');

    if (navbar) {
        // Always show navbar to keep language selector visible
        navbar.style.display = 'block';

        if (isAuthenticated && user) {
            // Show footer and nav links when authenticated
            if (footer) footer.style.display = 'block';
            navLinks.forEach(link => link.style.display = 'block');

            if (authNavItem) {
                // Use consistent translation function
                const logoutText = window.erasmusAdmin.translate('auth.logout');
                authNavItem.innerHTML = `
                    <a href="#" onclick="logout(); return false;" style="cursor: pointer;">
                        ${logoutText} (${user.username})
                    </a>
                `;
                authNavItem.style.display = 'block';
            }
        } else {
            // Hide footer and nav links when not authenticated, but keep language selector
            if (footer) footer.style.display = 'none';
            navLinks.forEach(link => link.style.display = 'none');

            if (authNavItem) {
                authNavItem.innerHTML = `<a href="/login" data-i18n="auth.login">${window.erasmusAdmin.translate('auth.login')}</a>`;
                authNavItem.style.display = 'block';
            }
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    const currentPath = window.location.pathname;
    const protectedPaths = ['/dashboard', '/patients', '/settings'];
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
    translate: (key, variables = {}) => {
        // Use the global i18n system
        return window.i18n ? window.i18n.translate(key, variables) : key;
    },
    // Interpretation functions for severity, engagement, and risk levels
    getSeverityInterpretation: (severity) => {
        if (severity <= 2) return window.erasmusAdmin.translate('reports.severity_interpretation.low');
        if (severity <= 3.5) return window.erasmusAdmin.translate('reports.severity_interpretation.moderate');
        if (severity <= 4.5) return window.erasmusAdmin.translate('reports.severity_interpretation.high');
        return window.erasmusAdmin.translate('reports.severity_interpretation.very_high');
    },
    getEngagementInterpretation: (rate) => {
        if (rate >= 90) return window.erasmusAdmin.translate('reports.engagement_interpretation.excellent');
        if (rate >= 80) return window.erasmusAdmin.translate('reports.engagement_interpretation.very_good');
        if (rate >= 60) return window.erasmusAdmin.translate('reports.engagement_interpretation.good');
        if (rate >= 40) return window.erasmusAdmin.translate('reports.engagement_interpretation.fair');
        return window.erasmusAdmin.translate('reports.engagement_interpretation.poor');
    },
    getRiskInterpretation: (severity, distressRate) => {
        if (severity <= 2 && distressRate <= 30) return window.erasmusAdmin.translate('reports.risk_interpretation.low');
        if (severity <= 3 && distressRate <= 50) return window.erasmusAdmin.translate('reports.risk_interpretation.moderate');
        if (severity <= 4 || distressRate > 50) return window.erasmusAdmin.translate('reports.risk_interpretation.high');
        if (severity > 4 && distressRate > 70) return window.erasmusAdmin.translate('reports.risk_interpretation.immediate');
        return window.erasmusAdmin.translate('reports.risk_interpretation.no_chances');
    }
};