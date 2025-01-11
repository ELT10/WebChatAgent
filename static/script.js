let ws = null;

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

async function initializeChatbot() {
    const websiteUrl = document.getElementById('websiteUrl').value;
    const forceScrape = document.getElementById('forceScrape').checked;

    if (!websiteUrl) {
        alert('Please enter a website URL');
        return;
    }

    showLoading();

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
            
            // Initialize WebSocket connection
            initializeWebSocket();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert('Error initializing chatbot');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
}

function initializeWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/chat`);

    ws.onmessage = function(event) {
        const response = JSON.parse(event.data);
        displayMessage(response.answer, 'bot', response.sources);
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        alert('Error connecting to chat server');
    };

    ws.onclose = function() {
        console.log('WebSocket connection closed');
    };
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Display user message
    displayMessage(message, 'user');
    
    // Send message through WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(message);
    } else {
        alert('Chat connection not available');
    }

    // Clear input
    messageInput.value = '';
}

function displayMessage(message, type, sources = []) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    messageDiv.textContent = message;

    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        sourcesDiv.textContent = 'Sources: ' + sources.join(', ');
        messageDiv.appendChild(sourcesDiv);
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle Enter key in message input
document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}); 