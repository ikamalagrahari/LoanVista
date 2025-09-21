// Common JavaScript functions for the Credit Approval System

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        updateThemeIcon(savedTheme);
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'light' ? '🌙' : '☀️';
    }
}

// Navigation Management
function initNavigation() {
    // Set active nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Search functionality
    const searchInput = document.getElementById('nav-search');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }
}

function handleSearch(e) {
    const query = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.dashboard-card');

    cards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const description = card.querySelector('p').textContent.toLowerCase();

        if (title.includes(query) || description.includes(query)) {
            card.style.display = 'block';
            card.classList.add('fade-in');
        } else {
            card.style.display = 'none';
        }
    });
}

// Loading States
function showLoading(button) {
    button.disabled = true;
    button.innerHTML = '<span class="loading"></span> Loading...';
}

function hideLoading(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

function showGlobalLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(overlay);
}

function hideGlobalLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Progress Bar for Uploads
function initProgressBar() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const fill = bar.querySelector('.progress-fill');
        if (fill) {
            fill.style.width = '0%';
        }
    });
}

function updateProgress(progress) {
    const progressBars = document.querySelectorAll('.progress-bar .progress-fill');
    progressBars.forEach(fill => {
        fill.style.width = progress + '%';
    });
}

// Utility function to display results
function displayResult(resultDiv, data, isSuccess = true) {
    resultDiv.className = `result ${isSuccess ? 'success' : 'error'} fade-in`;
    if (typeof data === 'object') {
        resultDiv.innerHTML = formatResult(data, isSuccess);
    } else {
        resultDiv.innerHTML = data;
    }
    resultDiv.style.display = 'block';

    // Auto-hide success messages after 5 seconds
    if (isSuccess) {
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 5000);
    }
}

// Format result data for display
function formatResult(data, isSuccess) {
    if (isSuccess && Array.isArray(data)) {
        // Display array data as table
        return formatArrayAsTable(data);
    } else if (isSuccess && typeof data === 'object') {
        // Display object data as formatted list
        return formatObjectAsList(data);
    } else {
        // Display error or simple message
        return `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
}

// Format array as table
function formatArrayAsTable(data) {
    if (data.length === 0) {
        return '<p>No data found.</p>';
    }

    const keys = Object.keys(data[0]);
    let table = '<table class="table"><thead><tr>';
    keys.forEach(key => {
        table += `<th>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>`;
    });
    table += '</tr></thead><tbody>';

    data.forEach(item => {
        table += '<tr>';
        keys.forEach(key => {
            table += `<td>${item[key]}</td>`;
        });
        table += '</tr>';
    });

    table += '</tbody></table>';
    return table;
}

// Format object as list
function formatObjectAsList(data) {
    let html = '<ul>';
    for (const [key, value] of Object.entries(data)) {
        const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `<li><strong>${displayKey}:</strong> ${value}</li>`;
    }
    html += '</ul>';
    return html;
}

// Generic form submission handler
async function submitForm(formId, url, method = 'POST', isFormData = false) {
    const form = document.getElementById(formId);
    const resultDiv = document.getElementById('result') || document.createElement('div');
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;

    if (!resultDiv.id) {
        resultDiv.id = 'result';
        form.appendChild(resultDiv);
    }

    showLoading(submitBtn);

    try {
        let fetchUrl = url;
        let body;
        let headers = {};

        if (isFormData) {
            body = new FormData(form);
            // Show progress for file uploads
            showGlobalLoading();
            updateProgress(0);
        } else {
            const formData = new FormData(form);
            const data = {};
            for (let [key, value] of formData.entries()) {
                if (key === 'csrfmiddlewaretoken') continue;
                data[key] = isNaN(value) ? value : (value.includes('.') ? parseFloat(value) : parseInt(value));
            }

            if (method === 'GET') {
                // For GET requests, append data as query parameters
                const params = new URLSearchParams();
                for (let [key, value] of Object.entries(data)) {
                    if (value !== '' && value !== null && value !== undefined) {
                        params.append(key, value);
                    }
                }
                fetchUrl += '?' + params.toString();
                body = null;
            } else {
                body = JSON.stringify(data);
                headers['Content-Type'] = 'application/json';
            }
        }

        // Add CSRF token for non-FormData requests
        if (!isFormData && method !== 'GET') {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
        }

        const response = await fetch(fetchUrl, {
            method: method,
            headers: headers,
            body: body
        });

        const result = await response.json();

        if (response.ok) {
            displayResult(resultDiv, result, true);
            // Update stats if on dashboard
            if (window.location.pathname === '/api/') {
                updateDashboardStats();
            }
        } else {
            displayResult(resultDiv, result, false);
        }

    } catch (error) {
        displayResult(resultDiv, { error: error.message }, false);
    } finally {
        hideLoading(submitBtn, originalBtnText);
        hideGlobalLoading();
        updateProgress(100);
    }
}

// Dashboard Stats Update
async function updateDashboardStats() {
    try {
        // This would fetch real stats from the backend
        // For now, just animate the existing stats
        const statCards = document.querySelectorAll('.stat-card h4');
        statCards.forEach(card => {
            card.classList.add('pulse');
            setTimeout(() => card.classList.remove('pulse'), 2000);
        });
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'var(--error-color)';
            isValid = false;
        } else {
            input.style.borderColor = 'var(--border-color)';
        }
    });

    return isValid;
}

// Real-time updates simulation
function initRealTimeUpdates() {
    // Simulate real-time updates every 30 seconds
    setInterval(() => {
        if (window.location.pathname === '/api/') {
            updateDashboardStats();
        }
    }, 30000);
}

// Initialize tooltips
function initTooltips() {
    const tooltipElements = document.querySelectorAll('.tooltip');
    tooltipElements.forEach(elem => {
        elem.addEventListener('mouseenter', showTooltip);
        elem.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = e.target.querySelector('.tooltip-text');
    if (tooltip) {
        tooltip.style.visibility = 'visible';
        tooltip.style.opacity = '1';
    }
}

function hideTooltip(e) {
    const tooltip = e.target.querySelector('.tooltip-text');
    if (tooltip) {
        tooltip.style.visibility = 'hidden';
        tooltip.style.opacity = '0';
    }
}

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all features
    initTheme();
    initNavigation();
    initProgressBar();
    initRealTimeUpdates();
    initTooltips();

    // Clear result on form input
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.style.borderColor = 'var(--border-color)';
                const resultDiv = document.getElementById('result');
                if (resultDiv) {
                    resultDiv.style.display = 'none';
                }
            });
        });
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.dashboard-card, .card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Skip link functionality
    const skipLink = document.querySelector('.skip-link');
    if (skipLink) {
        skipLink.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.focus();
                target.scrollIntoView();
            }
        });
    }
});