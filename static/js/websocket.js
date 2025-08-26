// WebSocket connection management
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000; // Start with 1 second
        this.listeners = {};
        
        this.connect();
    }
    
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('Attempting to connect to WebSocket:', wsUrl);
            
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (event) => {
                console.log('WebSocket connected successfully');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectInterval = 1000;
                
                this.updateConnectionStatus('connected');
                this.showToast('Connected', 'Real-time connection established', 'success');
                
                this.emit('connected', event);
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data.type);
                    
                    this.emit('message', data);
                    this.emit(data.type, data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.socket.onclose = (event) => {
                console.log('WebSocket connection closed:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                
                this.emit('disconnected', event);
                
                // Attempt to reconnect if not a clean close
                if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    this.showToast('Connection Failed', 'Unable to establish real-time connection', 'error');
                    this.updateConnectionStatus('error');
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus('error');
        }
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts), 30000);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        this.showToast('Reconnecting', `Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'warning');
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    send(type, data) {
        if (!this.isConnected || this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected, message not sent:', type, data);
            return false;
        }
        
        try {
            const message = { type, data };
            this.socket.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    off(event, callback) {
        if (!this.listeners[event]) return;
        
        const index = this.listeners[event].indexOf(callback);
        if (index > -1) {
            this.listeners[event].splice(index, 1);
        }
    }
    
    emit(event, data) {
        if (!this.listeners[event]) return;
        
        this.listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in WebSocket event listener for ${event}:`, error);
            }
        });
    }
    
    updateConnectionStatus(status) {
        const connectionStatus = document.getElementById('connection-status');
        const icon = connectionStatus.querySelector('i');
        const text = connectionStatus.querySelector('span');
        
        // Remove all status classes
        connectionStatus.classList.remove('connected', 'disconnected', 'error');
        
        switch (status) {
            case 'connected':
                connectionStatus.classList.add('connected');
                text.textContent = 'Connected';
                break;
            case 'disconnected':
                text.textContent = 'Disconnected';
                break;
            case 'error':
                connectionStatus.classList.add('error');
                text.textContent = 'Connection Error';
                break;
            default:
                text.textContent = 'Connecting...';
        }
    }
    
    showToast(title, message, type = 'info') {
        // Use the global showToast function if available
        if (typeof showToast === 'function') {
            showToast(title, message, type);
        } else {
            console.log(`Toast: ${title} - ${message}`);
        }
    }
    
    close() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Global WebSocket instance
let wsManager = null;

// Initialize WebSocket when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    wsManager = new WebSocketManager();
    
    // Set up WebSocket event listeners
    wsManager.on('initial_data', (data) => {
        console.log('Received initial data:', data.data);
        if (window.sentimentApp) {
            window.sentimentApp.updateAnalyticsSummary(data.data);
        }
    });
    
    wsManager.on('analysis_result', (data) => {
        console.log('Received analysis result:', data.data);
        if (window.sentimentApp) {
            window.sentimentApp.displayAnalysisResult(data.data);
        }
    });
    
    wsManager.on('new_analysis', (data) => {
        console.log('New analysis broadcast:', data.data);
        
        // Add to recent reviews list
        if (window.sentimentApp) {
            window.sentimentApp.addToRecentReviews(data.data);
        }
        
        // Show notification
        wsManager.showToast('New Analysis', `${data.data.sentiment.toUpperCase()} sentiment detected`, 'info');
        
        // Update analytics (request fresh data)
        wsManager.send('get_analytics', {});
    });
    
    wsManager.on('analytics_update', (data) => {
        console.log('Analytics updated:', data.data);
        if (window.sentimentApp) {
            window.sentimentApp.updateAnalyticsSummary(data.data);
        }
    });
    
    wsManager.on('connected', () => {
        // Request initial analytics data
        setTimeout(() => {
            wsManager.send('get_analytics', {});
        }, 500);
    });
    
    wsManager.on('disconnected', () => {
        wsManager.showToast('Disconnected', 'Real-time connection lost. Features limited.', 'warning');
    });
    
    wsManager.on('error', () => {
        wsManager.showToast('Connection Error', 'Unable to establish real-time connection', 'error');
    });
});

// Helper function to analyze text via WebSocket
function analyzeTextWebSocket(text) {
    if (!wsManager || !wsManager.isConnected) {
        console.warn('WebSocket not available, falling back to HTTP');
        return false;
    }
    
    return wsManager.send('analyze_text', { text });
}

// Helper function to get analytics via WebSocket
function getAnalyticsWebSocket() {
    if (!wsManager || !wsManager.isConnected) {
        console.warn('WebSocket not available');
        return false;
    }
    
    return wsManager.send('get_analytics', {});
}

// Expose WebSocket manager globally
window.wsManager = wsManager;
