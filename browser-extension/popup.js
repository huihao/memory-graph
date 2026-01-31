// Default backend URL
const DEFAULT_BACKEND_URL = 'http://localhost:8000';

let isProcessing = false;
let processedCount = 0;
let totalBookmarks = 0;

// Load settings
async function loadSettings() {
    const result = await chrome.storage.sync.get(['backendUrl']);
    const backendUrl = result.backendUrl || DEFAULT_BACKEND_URL;
    document.getElementById('backendUrl').value = backendUrl;
    return backendUrl;
}

// Save settings
async function saveSettings() {
    const backendUrl = document.getElementById('backendUrl').value;
    await chrome.storage.sync.set({ backendUrl });
}

// Update UI
function updateUI() {
    document.getElementById('processedCount').textContent = processedCount;
    document.getElementById('totalBookmarks').textContent = totalBookmarks || '-';
    
    const progress = totalBookmarks > 0 ? (processedCount / totalBookmarks * 100) : 0;
    document.getElementById('progressFill').style.width = `${progress}%`;
    
    document.getElementById('processAll').disabled = isProcessing;
    document.getElementById('processFolder').disabled = isProcessing;
    document.getElementById('stopProcessing').disabled = !isProcessing;
}

// Show status message
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
}

// Get all bookmarks recursively
async function getAllBookmarks(node, bookmarks = []) {
    if (node.url) {
        bookmarks.push(node);
    }
    
    if (node.children) {
        for (const child of node.children) {
            await getAllBookmarks(child, bookmarks);
        }
    }
    
    return bookmarks;
}

// Process a single bookmark
async function processBookmark(bookmark, backendUrl) {
    try {
        const response = await fetch(`${backendUrl}/api/articles/analyze-url?url=${encodeURIComponent(bookmark.url)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return { success: true, result };
    } catch (error) {
        console.error(`Error processing ${bookmark.url}:`, error);
        return { success: false, error: error.message };
    }
}

// Process all bookmarks
async function processAllBookmarks() {
    isProcessing = true;
    processedCount = 0;
    updateUI();
    
    const backendUrl = await loadSettings();
    showStatus('Fetching bookmarks...', 'processing');
    
    try {
        const bookmarkTree = await chrome.bookmarks.getTree();
        const bookmarks = await getAllBookmarks(bookmarkTree[0]);
        
        totalBookmarks = bookmarks.length;
        updateUI();
        
        showStatus(`Processing ${totalBookmarks} bookmarks...`, 'processing');
        
        for (const bookmark of bookmarks) {
            if (!isProcessing) break;
            
            showStatus(`Processing: ${bookmark.title || bookmark.url}`, 'processing');
            await processBookmark(bookmark, backendUrl);
            
            processedCount++;
            updateUI();
            
            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        showStatus(`Complete! Processed ${processedCount} bookmarks.`, 'success');
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        isProcessing = false;
        updateUI();
    }
}

// Stop processing
function stopProcessing() {
    isProcessing = false;
    showStatus('Processing stopped by user', 'info');
    updateUI();
}

// Event listeners
document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    updateUI();
    
    document.getElementById('backendUrl').addEventListener('change', saveSettings);
    document.getElementById('processAll').addEventListener('click', processAllBookmarks);
    document.getElementById('stopProcessing').addEventListener('click', stopProcessing);
    
    // Get initial bookmark count
    try {
        const bookmarkTree = await chrome.bookmarks.getTree();
        const bookmarks = await getAllBookmarks(bookmarkTree[0]);
        totalBookmarks = bookmarks.length;
        updateUI();
    } catch (error) {
        console.error('Error counting bookmarks:', error);
    }
});
