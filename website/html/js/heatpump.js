/**
 * Heatpump Control Interface
 * Communicates with the PHP API bridge which calls the Pico API
 */

const API_BASE = '/heatpump-api.php';

/**
 * Show status message
 */
function showMessage(text, type = 'info') {
    const container = document.getElementById('message-container');
    const message = document.createElement('div');
    message.className = `message message-${type}`;
    message.textContent = text;
    
    container.innerHTML = '';
    container.appendChild(message);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        message.classList.add('fade-out');
        setTimeout(() => message.remove(), 500);
    }, 5000);
}

/**
 * Make API call through PHP bridge
 */
async function callAPI(endpoint, method = 'GET') {
    try {
        const url = `${API_BASE}${endpoint}`;
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showMessage(`Error: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Refresh status from API
 */
async function refreshStatus() {
    try {
        const data = await callAPI('/status', 'GET');
        
        // Update status display
        document.getElementById('status-power').textContent = data.power || 'Unknown';
        document.getElementById('status-mode').textContent = data.mode || 'Unknown';
        document.getElementById('status-temp').textContent = (data.temperature || '?') + '°C';
        document.getElementById('status-fan').textContent = data.fan_speed || 'Unknown';
        
        showMessage('Status updated', 'success');
    } catch (error) {
        showMessage('Failed to get status', 'error');
    }
}

/**
 * Set power state
 */
async function setPower(state) {
    try {
        await callAPI(`/power/${state}`, 'PUT');
        showMessage(`Heat pump turned ${state}`, 'success');
        setTimeout(refreshStatus, 500);
    } catch (error) {
        showMessage(`Failed to turn ${state}`, 'error');
    }
}

/**
 * Set operating mode
 */
async function setMode(mode) {
    try {
        await callAPI(`/mode/${mode}`, 'PUT');
        showMessage(`Mode set to ${mode}`, 'success');
        setTimeout(refreshStatus, 500);
    } catch (error) {
        showMessage(`Failed to set mode`, 'error');
    }
}

/**
 * Set temperature
 */
async function setTemp(delta) {
    const input = document.getElementById('temp-input');
    let currentTemp = parseInt(input.value);
    let newTemp = currentTemp + delta;
    
    // Validate range
    if (newTemp < 10 || newTemp > 32) {
        showMessage('Temperature out of range (10-32°C)', 'warning');
        return;
    }
    
    try {
        await callAPI(`/temp/${newTemp}`, 'PUT');
        input.value = newTemp;
        showMessage(`Temperature set to ${newTemp}°C`, 'success');
        setTimeout(refreshStatus, 500);
    } catch (error) {
        showMessage('Failed to set temperature', 'error');
    }
}

/**
 * Set fan speed
 */
async function setFan(speed) {
    try {
        await callAPI(`/fan/${speed}`, 'PUT');
        showMessage(`Fan set to ${speed}`, 'success');
        setTimeout(refreshStatus, 500);
    } catch (error) {
        showMessage('Failed to set fan', 'error');
    }
}

/**
 * Set vertical swing
 */
async function setSwing(position) {
    try {
        await callAPI(`/swing/${position}`, 'PUT');
        showMessage(`Swing set to ${position}`, 'success');
        setTimeout(refreshStatus, 500);
    } catch (error) {
        showMessage('Failed to set swing', 'error');
    }
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Heatpump control interface loaded');
    
    // Load initial status
    refreshStatus();
    
    // Auto-refresh status every 30 seconds
    setInterval(refreshStatus, 30000);
});
