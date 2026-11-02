// api.js - API Client for BloodConnect
const API_BASE = '/api';

async function apiCall(endpoint, method, data, token = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const options = {
        method: method,
        headers: headers
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || result.msg || 'API call failed');
        }
        
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ============================================
// AUTH FUNCTIONS
// ============================================

async function login(email, password) {
    const result = await apiCall('/auth/login', 'POST', { email, password });
    if (result.success) {
        return { 
            success: true, 
            access_token: result.data.access_token,
            user: result.data.user
        };
    }
    return { success: false, error: result.error };
}

async function register(data) {
    return await apiCall('/auth/register', 'POST', data);
}

// ============================================
// DONOR API FUNCTIONS
// ============================================

async function getDonorDashboard(token) {
    return await apiCall('/donor/dashboard', 'GET', null, token);
}

async function getDonorAppointments(token) {
    return await apiCall('/donor/appointments', 'GET', null, token);
}

async function bookAppointment(token, data) {
    return await apiCall('/donor/appointments/book', 'POST', data, token);
}

async function getDonorAlerts(token) {
    return await apiCall('/donor/alerts', 'GET', null, token);
}

async function getNearbyHospitals(city = '') {
    return await apiCall(`/donor/hospitals/nearby?city=${city}`, 'GET');
}

// ============================================
// DONOR ALERT MANAGEMENT
// ============================================

/**
 * Mark a single alert as read
 * @param {string} token - JWT token
 * @param {number} alertId - Alert ID
 */
async function markAlertAsRead(token, alertId) {
    return await apiCall(`/donor/alerts/${alertId}/read`, 'PUT', null, token);
}

/**
 * Mark all alerts as read
 * @param {string} token - JWT token
 */
async function markAllAlertsAsRead(token) {
    return await apiCall('/donor/alerts/mark-all-read', 'PUT', null, token);
}

/**
 * Delete an alert
 * @param {string} token - JWT token
 * @param {number} alertId - Alert ID
 */
async function deleteAlert(token, alertId) {
    return await apiCall(`/donor/alerts/${alertId}`, 'DELETE', null, token);
}

// ============================================
// DONOR BADGE FUNCTIONS
// ============================================

/**
 * Get donor badges
 * @param {string} token - JWT token
 */
async function getDonorBadges(token) {
    return await apiCall('/donor/badges', 'GET', null, token);
}

/**
 * Check badge eligibility
 * @param {string} token - JWT token
 */
async function checkBadgeEligibility(token) {
    return await apiCall('/donor/badges/check', 'GET', null, token);
}

/**
 * Get donation history
 * @param {string} token - JWT token
 */
async function getDonationHistory(token) {
    return await apiCall('/donor/donations', 'GET', null, token);
}

// ============================================
// HOSPITAL API FUNCTIONS
// ============================================

async function getHospitalDashboard(token) {
    return await apiCall('/hospital/dashboard', 'GET', null, token);
}

async function getHospitalAppointments(token, status = '') {
    const url = status ? `/hospital/appointments?status=${status}` : '/hospital/appointments';
    return await apiCall(url, 'GET', null, token);
}

async function updateAppointmentStatus(token, appointmentId, status) {
    return await apiCall(`/hospital/appointments/${appointmentId}/update`, 'PUT', { status }, token);
}

async function getBloodTests(token) {
    return await apiCall('/hospital/blood-tests', 'GET', null, token);
}

// ============================================
// HOSPITAL DONATION FUNCTIONS
// ============================================

/**
 * Record a donation
 * @param {string} token - JWT token
 * @param {object} data - Donation data { donor_id, test_type, test_result, quantity_ml }
 */
async function recordDonation(token, data) {
    return await apiCall('/hospital/donations/record', 'POST', data, token);
}

/**
 * Send health alert to donor
 * @param {string} token - JWT token
 * @param {object} alertData - Alert data { donor_id, alert_type, title, message, test_details }
 */
async function sendHealthAlert(token, alertData) {
    return await apiCall('/hospital/alerts/send', 'POST', alertData, token);
}

// ============================================
// BLOOD TEST FUNCTIONS
// ============================================

/**
 * Upload image for cell type classification (WBC)
 * @param {string} token - JWT token
 * @param {string} donorId - Donor ID
 * @param {string} appointmentId - Appointment ID (optional)
 * @param {File} imageFile - Image file to upload
 */
async function uploadCellTypeTest(token, donorId, appointmentId, imageFile) {
    const formData = new FormData();
    formData.append('donor_id', donorId);
    if (appointmentId && appointmentId !== '') {
        formData.append('appointment_id', appointmentId);
    }
    formData.append('image', imageFile);
    
    try {
        const response = await fetch(`${API_BASE}/hospital/blood-test/cell`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Upload image for malaria detection (RBC)
 * @param {string} token - JWT token
 * @param {string} donorId - Donor ID
 * @param {string} appointmentId - Appointment ID (optional)
 * @param {File} imageFile - Image file to upload
 */
async function uploadMalariaTest(token, donorId, appointmentId, imageFile) {
    const formData = new FormData();
    formData.append('donor_id', donorId);
    if (appointmentId && appointmentId !== '') {
        formData.append('appointment_id', appointmentId);
    }
    formData.append('image', imageFile);
    
    try {
        const response = await fetch(`${API_BASE}/hospital/blood-test/malaria`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Upload image for leukemia detection (ALL)
 * @param {string} token - JWT token
 * @param {string} donorId - Donor ID
 * @param {string} appointmentId - Appointment ID (optional)
 * @param {File} imageFile - Image file to upload
 */
async function uploadLeukemiaTest(token, donorId, appointmentId, imageFile) {
    const formData = new FormData();
    formData.append('donor_id', donorId);
    if (appointmentId && appointmentId !== '') {
        formData.append('appointment_id', appointmentId);
    }
    formData.append('image', imageFile);
    
    try {
        const response = await fetch(`${API_BASE}/hospital/blood-test/leukemia`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Upload image for sickle cell detection
 * @param {string} token - JWT token
 * @param {string} donorId - Donor ID
 * @param {string} appointmentId - Appointment ID (optional)
 * @param {File} imageFile - Image file to upload
 */
async function uploadSickleCellTest(token, donorId, appointmentId, imageFile) {
    const formData = new FormData();
    formData.append('donor_id', donorId);
    if (appointmentId && appointmentId !== '') {
        formData.append('appointment_id', appointmentId);
    }
    formData.append('image', imageFile);
    
    try {
        const response = await fetch(`${API_BASE}/hospital/blood-test/sickle`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Generic upload function that selects the appropriate test based on testType
 * @param {string} token - JWT token
 * @param {string} donorId - Donor ID
 * @param {string} appointmentId - Appointment ID (optional)
 * @param {File} imageFile - Image file to upload
 * @param {string} testType - Type of test: 'cell', 'malaria', 'leukemia', or 'sickle'
 */
async function uploadBloodTest(token, donorId, appointmentId, imageFile, testType = 'cell') {
    if (testType === 'malaria') {
        return await uploadMalariaTest(token, donorId, appointmentId, imageFile);
    } else if (testType === 'leukemia') {
        return await uploadLeukemiaTest(token, donorId, appointmentId, imageFile);
    } else if (testType === 'sickle') {
        return await uploadSickleCellTest(token, donorId, appointmentId, imageFile);
    } else {
        return await uploadCellTypeTest(token, donorId, appointmentId, imageFile);
    }
}

// ============================================
// AUTH HELPER FUNCTIONS
// ============================================

function isAuthenticated() {
    const token = localStorage.getItem('token');
    return token !== null;
}

function getToken() {
    return localStorage.getItem('token');
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// ============================================
// THEME TOGGLE FUNCTIONALITY
// ============================================

function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeToggleActive(savedTheme);
    } else {
        // Check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const defaultTheme = prefersDark ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', defaultTheme);
        updateThemeToggleActive(defaultTheme);
    }
    
    // Add click handler
    themeToggle.addEventListener('click', (e) => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeToggleActive(newTheme);
    });
}

function updateThemeToggleActive(theme) {
    const icons = document.querySelectorAll('.theme-toggle-icon');
    icons.forEach(icon => {
        if (icon.getAttribute('data-theme') === theme) {
            icon.classList.add('active');
        } else {
            icon.classList.remove('active');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initThemeToggle);

// ============================================
// EXPORT FUNCTIONS (for module usage if needed)
// ============================================

// Make all functions available globally
if (typeof window !== 'undefined') {
    window.apiCall = apiCall;
    window.login = login;
    window.register = register;
    window.getDonorDashboard = getDonorDashboard;
    window.getDonorAppointments = getDonorAppointments;
    window.bookAppointment = bookAppointment;
    window.getDonorAlerts = getDonorAlerts;
    window.markAlertAsRead = markAlertAsRead;
    window.markAllAlertsAsRead = markAllAlertsAsRead;
    window.deleteAlert = deleteAlert;
    window.getDonorBadges = getDonorBadges;
    window.checkBadgeEligibility = checkBadgeEligibility;
    window.getDonationHistory = getDonationHistory;
    window.getHospitalDashboard = getHospitalDashboard;
    window.getHospitalAppointments = getHospitalAppointments;
    window.updateAppointmentStatus = updateAppointmentStatus;
    window.getBloodTests = getBloodTests;
    window.recordDonation = recordDonation;
    window.sendHealthAlert = sendHealthAlert;
    window.uploadCellTypeTest = uploadCellTypeTest;
    window.uploadMalariaTest = uploadMalariaTest;
    window.uploadLeukemiaTest = uploadLeukemiaTest;
    window.uploadSickleCellTest = uploadSickleCellTest;
    window.uploadBloodTest = uploadBloodTest;
    window.getNearbyHospitals = getNearbyHospitals;
    window.isAuthenticated = isAuthenticated;
    window.getToken = getToken;
    window.getUser = getUser;
    window.logout = logout;
}
// ---------- Display helpers ----------
function fmtDate(v) {
    if (!v) return '—';
    const d = new Date(v);
    if (isNaN(d)) return v;
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
}
function fmtDateTime(v) {
    if (!v) return '—';
    const d = new Date(String(v).replace(' ', 'T'));
    if (isNaN(d)) return v;
    return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
