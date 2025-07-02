/**
 * Camera Timelapse frontend debugging tools.
 */
class HaCameraTimelapseDebug {
    constructor() {
        this.enabled = false;
        this.connectionPromise = null;
        this.styleElement = null;
        this.debugOverlay = null;
        this.debugMessages = [];
        this.maxMessages = 100;
    }

    /**
     * Initialize the debug tools.
     */
    async init() {
        console.log("Initializing Camera Timelapse debug tools");
        this.setupStyles();
        this.createOverlay();
        await this.connect();
        
        // Check current debug status
        this.checkDebugStatus();
        
        // Add command to window for user access
        window.haCameraTimelapseDebug = {
            enable: () => this.enable(),
            disable: () => this.disable(),
            clear: () => this.clearMessages(),
            toggle: () => this.toggle(),
            status: () => this.logStatus()
        };
        
        console.info("Camera Timelapse debug tools initialized. Use window.haCameraTimelapseDebug.toggle() to enable/disable");
    }

    /**
     * Connect to Home Assistant websocket API.
     */
    async connect() {
        if (!window.hassConnection) {
            console.error("Home Assistant connection not available");
            return;
        }
        
        try {
            const conn = await window.hassConnection;
            this.connection = conn.connection;
            
            // Subscribe to debug events
            this.connection.subscribeEvents(
                (event) => this.handleDebugEvent(event),
                "ha_camera_timelapse_debug_event"
            );
            
            console.log("Connected to Home Assistant websocket");
        } catch (err) {
            console.error("Failed to connect to Home Assistant", err);
        }
    }

    /**
     * Check current debug status.
     */
    async checkDebugStatus() {
        if (!this.connection) return;
        
        try {
            const result = await this.connection.sendMessagePromise({
                type: "ha_camera_timelapse/debug/status"
            });
            
            this.enabled = result.debug_enabled;
            this.updateOverlayVisibility();
            console.log(`Camera Timelapse debug mode is ${this.enabled ? 'enabled' : 'disabled'}`);
        } catch (err) {
            console.error("Failed to check debug status", err);
        }
    }

    /**
     * Enable debug mode.
     */
    async enable() {
        if (!this.connection) await this.connect();
        if (!this.connection) return;
        
        try {
            const result = await this.connection.sendMessagePromise({
                type: "ha_camera_timelapse/debug/toggle",
                enable: true
            });
            
            this.enabled = result.debug_enabled;
            this.updateOverlayVisibility();
            console.log("Camera Timelapse debug mode enabled");
            this.addMessage("Debug mode enabled", "info");
        } catch (err) {
            console.error("Failed to enable debug mode", err);
        }
    }

    /**
     * Disable debug mode.
     */
    async disable() {
        if (!this.connection) return;
        
        try {
            const result = await this.connection.sendMessagePromise({
                type: "ha_camera_timelapse/debug/toggle",
                enable: false
            });
            
            this.enabled = result.debug_enabled;
            this.updateOverlayVisibility();
            console.log("Camera Timelapse debug mode disabled");
            this.addMessage("Debug mode disabled", "info");
        } catch (err) {
            console.error("Failed to disable debug mode", err);
        }
    }

    /**
     * Toggle debug mode.
     */
    toggle() {
        if (this.enabled) {
            this.disable();
        } else {
            this.enable();
        }
    }

    /**
     * Log current status.
     */
    logStatus() {
        console.log(`Camera Timelapse debug mode: ${this.enabled ? 'enabled' : 'disabled'}`);
        return this.enabled;
    }

    /**
     * Handle debug event from backend.
     */
    handleDebugEvent(event) {
        const { message, level = "info", data } = event.data;
        
        // Log to console
        switch (level) {
            case "error":
                console.error(`[Camera Timelapse] ${message}`, data);
                break;
            case "warning":
                console.warn(`[Camera Timelapse] ${message}`, data);
                break;
            case "info":
            default:
                console.info(`[Camera Timelapse] ${message}`, data);
                break;
        }
        
        // Add to overlay
        this.addMessage(message, level, data);
    }

    /**
     * Add message to debug overlay.
     */
    addMessage(message, level = "info", data = null) {
        if (!this.debugOverlay) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const msgElement = document.createElement('div');
        msgElement.className = `camera-timelapse-debug-message camera-timelapse-debug-${level}`;
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'camera-timelapse-debug-time';
        timeSpan.textContent = timestamp;
        
        const levelSpan = document.createElement('span');
        levelSpan.className = 'camera-timelapse-debug-level';
        levelSpan.textContent = level.toUpperCase();
        
        const messageSpan = document.createElement('span');
        messageSpan.className = 'camera-timelapse-debug-text';
        messageSpan.textContent = message;
        
        msgElement.appendChild(timeSpan);
        msgElement.appendChild(levelSpan);
        msgElement.appendChild(messageSpan);
        
        if (data) {
            const dataButton = document.createElement('button');
            dataButton.className = 'camera-timelapse-debug-data-button';
            dataButton.textContent = 'Data';
            dataButton.onclick = () => {
                console.log('Debug data:', data);
                alert('Data logged to console');
            };
            msgElement.appendChild(dataButton);
        }
        
        const messagesContainer = this.debugOverlay.querySelector('.camera-timelapse-debug-messages');
        messagesContainer.appendChild(msgElement);
        
        // Keep message history limited
        this.debugMessages.push({
            message,
            level,
            timestamp,
            data
        });
        
        if (this.debugMessages.length > this.maxMessages) {
            this.debugMessages.shift();
            const children = messagesContainer.children;
            if (children.length > this.maxMessages) {
                messagesContainer.removeChild(children[0]);
            }
        }
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Clear all debug messages.
     */
    clearMessages() {
        const messagesContainer = this.debugOverlay.querySelector('.camera-timelapse-debug-messages');
        while (messagesContainer.firstChild) {
            messagesContainer.removeChild(messagesContainer.firstChild);
        }
        this.debugMessages = [];
        this.addMessage("Debug messages cleared", "info");
    }

    /**
     * Set up styles for debug overlay.
     */
    setupStyles() {
        if (this.styleElement) return;
        
        this.styleElement = document.createElement('style');
        this.styleElement.textContent = `
            .camera-timelapse-debug-overlay {
                position: fixed;
                bottom: 10px;
                right: 10px;
                width: 400px;
                max-height: 300px;
                background-color: rgba(0, 0, 0, 0.85);
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                font-family: monospace;
                font-size: 12px;
                z-index: 9999;
                display: none;
                flex-direction: column;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
            }
            
            .camera-timelapse-debug-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 5px 10px;
                background-color: #333;
                border-bottom: 1px solid #555;
                cursor: move;
            }
            
            .camera-timelapse-debug-title {
                font-weight: bold;
            }
            
            .camera-timelapse-debug-controls {
                display: flex;
                gap: 5px;
            }
            
            .camera-timelapse-debug-button {
                background: #444;
                border: none;
                color: white;
                padding: 2px 5px;
                font-size: 10px;
                cursor: pointer;
                border-radius: 3px;
            }
            
            .camera-timelapse-debug-button:hover {
                background: #555;
            }
            
            .camera-timelapse-debug-messages {
                overflow-y: auto;
                padding: 5px;
                flex-grow: 1;
                max-height: 250px;
            }
            
            .camera-timelapse-debug-message {
                margin-bottom: 3px;
                padding: 3px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: flex-start;
                gap: 5px;
            }
            
            .camera-timelapse-debug-time {
                color: #aaa;
                font-size: 10px;
                white-space: nowrap;
            }
            
            .camera-timelapse-debug-level {
                font-size: 10px;
                padding: 1px 3px;
                border-radius: 2px;
                min-width: 40px;
                text-align: center;
            }
            
            .camera-timelapse-debug-info .camera-timelapse-debug-level {
                background-color: #2962FF;
            }
            
            .camera-timelapse-debug-warning .camera-timelapse-debug-level {
                background-color: #FF9800;
            }
            
            .camera-timelapse-debug-error .camera-timelapse-debug-level {
                background-color: #F44336;
            }
            
            .camera-timelapse-debug-text {
                flex-grow: 1;
                word-break: break-word;
            }
            
            .camera-timelapse-debug-data-button {
                background: #555;
                border: none;
                color: white;
                padding: 1px 4px;
                font-size: 9px;
                cursor: pointer;
                border-radius: 3px;
            }
        `;
        document.head.appendChild(this.styleElement);
    }

    /**
     * Create debug overlay UI.
     */
    createOverlay() {
        if (this.debugOverlay) return;
        
        this.debugOverlay = document.createElement('div');
        this.debugOverlay.className = 'camera-timelapse-debug-overlay';
        
        const header = document.createElement('div');
        header.className = 'camera-timelapse-debug-header';
        
        const title = document.createElement('div');
        title.className = 'camera-timelapse-debug-title';
        title.textContent = 'Camera Timelapse Debug';
        
        const controls = document.createElement('div');
        controls.className = 'camera-timelapse-debug-controls';
        
        const clearButton = document.createElement('button');
        clearButton.className = 'camera-timelapse-debug-button';
        clearButton.textContent = 'Clear';
        clearButton.onclick = () => this.clearMessages();
        
        const closeButton = document.createElement('button');
        closeButton.className = 'camera-timelapse-debug-button';
        closeButton.textContent = 'Close';
        closeButton.onclick = () => this.disable();
        
        controls.appendChild(clearButton);
        controls.appendChild(closeButton);
        
        header.appendChild(title);
        header.appendChild(controls);
        
        const messages = document.createElement('div');
        messages.className = 'camera-timelapse-debug-messages';
        
        this.debugOverlay.appendChild(header);
        this.debugOverlay.appendChild(messages);
        
        document.body.appendChild(this.debugOverlay);
        
        // Make overlay draggable
        this.makeDraggable(this.debugOverlay, header);
    }

    /**
     * Make an element draggable.
     */
    makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        handle.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            // get the mouse cursor position at startup
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            // call a function whenever the cursor moves
            document.onmousemove = elementDrag;
        }
        
        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            // calculate the new cursor position
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            // set the element's new position
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
            // Remove bottom/right positioning when dragged
            element.style.bottom = 'auto';
            element.style.right = 'auto';
        }
        
        function closeDragElement() {
            // stop moving when mouse button is released
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    /**
     * Update overlay visibility based on debug status.
     */
    updateOverlayVisibility() {
        if (!this.debugOverlay) return;
        
        this.debugOverlay.style.display = this.enabled ? 'flex' : 'none';
    }
}

// Initialize when the page is fully loaded
window.addEventListener('load', () => {
    const debugTools = new HaCameraTimelapseDebug();
    debugTools.init();
});