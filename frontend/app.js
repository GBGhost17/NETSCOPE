/**
 * NetScope Frontend Application
 */

const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function () {
    console.log('NetScope application loaded');
    initializeApp();
});

function initializeApp() {
    // Initialize the application
    console.log('Initializing NetScope...');
}

/**
 * Make a scan request to the API
 * @param {string} target - Target host or network to scan
 */
async function startScan(target) {
    try {
        const response = await fetch(`${API_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ target: target })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Scan started:', data);
            return data;
        } else {
            console.error('Failed to start scan');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

/**
 * Get scan results
 * @param {string} scanId - Scan ID to retrieve results
 */
async function getScanResults(scanId) {
    try {
        const response = await fetch(`${API_URL}/scan/${scanId}`);

        if (response.ok) {
            const data = await response.json();
            console.log('Scan results:', data);
            return data;
        } else {
            console.error('Failed to get scan results');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
