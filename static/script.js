let ws = null;
let isProcessing = false;

function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = overlay.querySelector('p');
    if (loadingText) {
        loadingText.textContent = message;
    }
    overlay.style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

async function initializeChatbot() {
    const websiteUrlInput = document.getElementById('websiteUrl');
    const websiteUrl = websiteUrlInput.value.trim();
    const forceScrape = document.getElementById('forceScrape').checked;

    if (!websiteUrl) {
        showError('Please enter a website URL');
        websiteUrlInput.focus();
        return;
    }

    // Basic URL validation
    try {
        new URL(websiteUrl);
    } catch (e) {
        showError('Please enter a valid URL (e.g., https://example.com)');
        websiteUrlInput.focus();
        return;
    }

    const loadingMessage = forceScrape ? 
        'Scraping website... This may take a few minutes.' : 
        'Initializing chatbot...';
    showLoading(loadingMessage);

    try {
        const response = await fetch('/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                website_url: websiteUrl,
                force_scrape: forceScrape
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Show chat interface
            document.getElementById('setupContainer').style.display = 'none';
            document.getElementById('chatContainer').style.display = 'block';
            
            // Add welcome message
            const welcomeMessage = data.message || 'Hi there! How can I help you?';
            displayMessage(welcomeMessage, 'bot');
            
            // Initialize WebSocket connection
            initializeWebSocket();
        } else {
            showError(`Initialization failed: ${data.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to connect to server. Please check your connection and try again.');
    } finally {
        hideLoading();
    }
}

function showError(message) {
    // Create or update error message element
    let errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'errorMessage';
        errorDiv.className = 'error-message';
        const setupContainer = document.getElementById('setupContainer');
        setupContainer.insertBefore(errorDiv, setupContainer.firstChild);
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/chat`);

    ws.onopen = function() {
        console.log('WebSocket connection established');
    };

    ws.onmessage = function(event) {
        isProcessing = false;
        const response = JSON.parse(event.data);
        
        if (response.error) {
            displayMessage(`Error: ${response.error}`, 'error');
        } else {
            displayMessage(response.answer, 'bot', response.sources);
        }
        
        // Re-enable input
        const messageInput = document.getElementById('messageInput');
        messageInput.disabled = false;
        messageInput.focus();
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        isProcessing = false;
        displayMessage('Connection error. Please refresh the page.', 'error');
    };

    ws.onclose = function() {
        console.log('WebSocket connection closed');
        isProcessing = false;
        displayMessage('Connection closed. Please refresh the page to reconnect.', 'error');
    };
}

function sendMessage() {
    if (isProcessing) return;
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Display user message
    displayMessage(message, 'user');
    
    // Send message through WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(message);
        isProcessing = true;
        messageInput.disabled = true;
        
        // Show typing indicator
        displayTypingIndicator();
    } else {
        displayMessage('Connection not available. Please refresh the page.', 'error');
    }

    // Clear input
    messageInput.value = '';
}

function displayTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function displayMessage(message, type, sources = []) {
    // Remove typing indicator if present
    removeTypingIndicator();
    
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    // Create message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    messageDiv.appendChild(contentDiv);

    // Add sources if present
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        sourcesDiv.innerHTML = '<strong>Sources:</strong><br>';
        
        sources.forEach((source, index) => {
            const sourceLink = document.createElement('a');
            sourceLink.href = source;
            sourceLink.textContent = source;
            sourceLink.target = '_blank';
            sourceLink.rel = 'noopener noreferrer';
            sourcesDiv.appendChild(sourceLink);
            
            if (index < sources.length - 1) {
                sourcesDiv.appendChild(document.createElement('br'));
            }
        });
        
        messageDiv.appendChild(sourcesDiv);
    }

    // Add timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    messageDiv.appendChild(timestamp);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle Enter key in message input
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    const websiteUrlInput = document.getElementById('websiteUrl');
    if (websiteUrlInput) {
        websiteUrlInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                initializeChatbot();
            }
        });
    }
}); 