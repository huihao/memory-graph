// Background service worker for the extension
chrome.runtime.onInstalled.addListener(() => {
    console.log('Memory Graph extension installed');
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'processBookmark') {
        processBookmark(request.url, request.backendUrl)
            .then(result => sendResponse({ success: true, result }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // Keep the message channel open for async response
    }
});

async function processBookmark(url, backendUrl) {
    const response = await fetch(`${backendUrl}/api/articles/analyze-url?url=${encodeURIComponent(url)}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}
