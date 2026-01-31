// Load settings
async function loadSettings() {
    const result = await chrome.storage.sync.get(['backendUrl', 'apiKey']);
    document.getElementById('backendUrl').value = result.backendUrl || 'http://localhost:8000';
    document.getElementById('apiKey').value = result.apiKey || '';
}

// Save settings
async function saveSettings() {
    const backendUrl = document.getElementById('backendUrl').value;
    const apiKey = document.getElementById('apiKey').value;
    
    await chrome.storage.sync.set({ backendUrl, apiKey });
    
    // Show success message
    const status = document.getElementById('status');
    status.style.display = 'block';
    
    setTimeout(() => {
        status.style.display = 'none';
    }, 3000);
}

// Event listeners
document.addEventListener('DOMContentLoaded', loadSettings);
document.getElementById('save').addEventListener('click', saveSettings);
