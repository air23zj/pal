import { rooms } from '../utils/rooms-api';
import { video } from '../utils/video-api';
import { showLoading, showError, showSuccess } from '../utils/ui';
import { loadLoginForm } from './auth';
import { loadMainContent } from '../main.js';

export function loadVideoCallInterface() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold">Video Calls</h2>
                <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>
                    Back to Home
                </button>
            </div>
            <div id="videoCallContainer">
                <!-- Video call content will be loaded here -->
            </div>
        </div>
    `;

    // Add back button functionality
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', () => {
        if (videoCall.socket) {
            videoCall.cleanup(true);
        }
        history.pushState(null, '', '/');
        loadMainContent();
    });

    // Initialize video call functionality
    videoCall.init();
}

class VideoCall {
    constructor() {
        this.peerConnections = {};
        this.localStream = null;
        this.socket = null;
        this.currentRoom = null;
        this.configuration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' }
            ]
        };
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2 seconds
        this.heartbeatTimeout = null;
        this.lastHeartbeat = null;
        this.screenStream = null;
        this.isScreenSharing = false;
        this.chatMessages = [];
        this.unreadMessages = 0;
        this.recognition = null;
        this.isTranscribing = false;
        this.transcriptionHistory = [];
    }

    async init() {
        const container = document.getElementById('videoCallContainer');
        container.innerHTML = `
            <!-- Rooms List View -->
            <div id="videoCallRoomsList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Rooms will be loaded here -->
            </div>

            <!-- Active Room View (initially hidden) -->
            <div id="videoCallActiveRoom" class="hidden">
                <div class="flex items-center justify-between mb-6">
                    <h3 id="videoCallRoomName" class="text-xl font-semibold"></h3>
                    <div class="flex items-center space-x-4">
                        <button id="videoCallToggleVideo" class="p-2 rounded-full hover:bg-gray-100" title="Toggle Video">
                            <i class="fas fa-video"></i>
                            <i class="fas fa-video-slash hidden"></i>
                        </button>
                        <button id="videoCallToggleAudio" class="p-2 rounded-full hover:bg-gray-100" title="Toggle Audio">
                            <i class="fas fa-microphone"></i>
                            <i class="fas fa-microphone-slash hidden"></i>
                        </button>
                        <button id="videoCallToggleScreenShare" class="p-2 rounded-full hover:bg-gray-100" title="Share Screen">
                            <i class="fas fa-desktop"></i>
                            <i class="fas fa-stop hidden"></i>
                        </button>
                        <button id="videoCallToggleTranscription" class="p-2 rounded-full hover:bg-gray-100" title="Toggle Live Transcription">
                            <i class="fas fa-closed-captioning"></i>
                        </button>
                        <button id="videoCallToggleChat" class="p-2 rounded-full hover:bg-gray-100" title="Toggle Chat">
                            <i class="fas fa-comments"></i>
                            <span id="unreadBadge" class="hidden absolute top-0 right-0 transform translate-x-1/2 -translate-y-1/2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">0</span>
                        </button>
                        <button id="videoCallLeaveRoomButton" class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700">
                            Leave Room
                        </button>
                    </div>
                </div>

                <div class="flex gap-4 h-[calc(100vh-200px)]">
                    <!-- Video Grid -->
                    <div class="flex-1 flex flex-col">
                        <div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 auto-rows-fr">
                            <!-- Local Video -->
                            <div id="videoCallLocalContainer" class="relative bg-gray-900 rounded-lg overflow-hidden">
                                <video id="videoCallLocalVideo" autoplay playsinline muted class="w-full h-full object-cover"></video>
                                <div class="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
                                    You
                                </div>
                            </div>
                            <!-- Remote Videos -->
                            <div id="videoCallRemoteVideos" class="grid gap-4 auto-rows-fr">
                                <!-- Remote videos will be added here -->
                            </div>
                        </div>
                        <!-- Transcription Area -->
                        <div id="transcriptionArea" class="hidden mt-4 bg-white rounded-lg p-4 h-48 overflow-y-auto">
                            <div class="flex justify-between items-center text-sm text-gray-500 mb-2">
                                <div>Live Transcription</div>
                                <div class="flex gap-2">
                                    <button id="summarizeTranscriptionBtn" class="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 transition-colors">
                                        Summarize
                                    </button>
                                    <button id="clearTranscriptionBtn" class="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors">
                                        Clear
                                    </button>
                                </div>
                            </div>
                            <div id="transcriptionText" class="text-gray-800 mb-4"></div>
                            <div id="transcriptionSummary" class="hidden mt-4 p-4 bg-gray-50 rounded-lg">
                                <div class="text-sm font-medium text-gray-700 mb-2">Summary:</div>
                                <div id="summaryText" class="text-gray-600"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Chat Section (initially hidden) -->
                    <div class="chat-section collapsed w-0 transition-all duration-300 bg-white rounded-lg shadow-sm">
                        <div class="flex flex-col h-full">
                            <div class="p-4 border-b">
                                <h4 class="text-lg font-semibold">Chat</h4>
                            </div>
                            <div id="videoCallChatMessages" class="flex-1 overflow-y-auto p-4 space-y-4">
                                <!-- Chat messages will appear here -->
                            </div>
                            <div class="p-4 border-t">
                                <div class="flex items-center space-x-2">
                                    <input type="text" id="videoCallMessageInput" 
                                        class="flex-1 rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500" 
                                        placeholder="Type a message...">
                                    <button id="videoCallSendMessage" class="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                                        <i class="fas fa-paper-plane"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Create Room Button -->
            <div class="fixed bottom-8 right-8">
                <button id="videoCallCreateRoomButton" class="bg-primary-600 hover:bg-primary-700 text-white rounded-full p-4 shadow-lg">
                    <i class="fas fa-plus text-xl"></i>
                </button>
            </div>
        `;

        // Add event listeners
        this.addEventListeners();

        // Load initial rooms
        await this.loadRooms();

        // Initialize speech recognition
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;

            this.recognition.onresult = (event) => {
                const transcriptionText = document.getElementById('transcriptionText');
                if (transcriptionText) {
                    let finalTranscript = '';
                    let interimTranscript = '';

                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript;
                            // Add to history when we get final results
                            this.transcriptionHistory.push({
                                text: event.results[i][0].transcript,
                                timestamp: new Date().toISOString()
                            });
                        } else {
                            interimTranscript += event.results[i][0].transcript;
                        }
                    }

                    // Display both final and interim transcripts
                    transcriptionText.innerHTML = `
                        ${this.transcriptionHistory.map(t => `<div class="mb-2">${t.text}</div>`).join('')}
                        <span class="text-gray-400">${interimTranscript}</span>
                    `;
                    transcriptionText.scrollTop = transcriptionText.scrollHeight;
                }
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.stopTranscription();
            };

            // Automatically restart recognition if it ends
            this.recognition.onend = () => {
                if (this.isTranscribing) {
                    console.log('Restarting speech recognition...');
                    this.recognition.start();
                }
            };
        }
    }

    async addEventListeners() {
        // Toggle video
        const toggleVideoBtn = document.getElementById('videoCallToggleVideo');
        if (toggleVideoBtn) {
            toggleVideoBtn.addEventListener('click', () => {
                const videoTrack = this.localStream?.getVideoTracks()[0];
                if (!videoTrack) return;

                // Toggle video track
                videoTrack.enabled = !videoTrack.enabled;

                // Update UI
                const videoIcon = toggleVideoBtn.querySelector('.fa-video');
                const videoSlashIcon = toggleVideoBtn.querySelector('.fa-video-slash');

                if (videoTrack.enabled) {
                    videoIcon.classList.remove('hidden');
                    videoSlashIcon.classList.add('hidden');
                } else {
                    videoIcon.classList.add('hidden');
                    videoSlashIcon.classList.remove('hidden');
                }
            });
        }

        // Toggle audio
        const toggleAudioBtn = document.getElementById('videoCallToggleAudio');
        if (toggleAudioBtn) {
            toggleAudioBtn.addEventListener('click', () => {
                const audioTrack = this.localStream?.getAudioTracks()[0];
                if (!audioTrack) return;

                // Toggle audio track
                audioTrack.enabled = !audioTrack.enabled;

                // Update UI
                const audioIcon = toggleAudioBtn.querySelector('.fa-microphone');
                const audioSlashIcon = toggleAudioBtn.querySelector('.fa-microphone-slash');

                if (audioTrack.enabled) {
                    audioIcon.classList.remove('hidden');
                    audioSlashIcon.classList.add('hidden');
                } else {
                    audioIcon.classList.add('hidden');
                    audioSlashIcon.classList.remove('hidden');
                }
            });
        }

        // Toggle screen share
        const toggleScreenShareBtn = document.getElementById('videoCallToggleScreenShare');
        if (toggleScreenShareBtn) {
            toggleScreenShareBtn.addEventListener('click', async () => {
                if (this.isScreenSharing) {
                    await this.stopScreenShare();
                } else {
                    await this.startScreenShare();
                }
            });
        }

        // Toggle chat
        const toggleChatBtn = document.getElementById('videoCallToggleChat');
        const chatSection = document.querySelector('.chat-section');
        if (toggleChatBtn && chatSection) {
            toggleChatBtn.addEventListener('click', () => {
                chatSection.classList.toggle('collapsed');
                if (chatSection.classList.contains('collapsed')) {
                    chatSection.style.width = '0';
                } else {
                    chatSection.style.width = '320px';
                    this.unreadMessages = 0;
                    this.updateUnreadBadge();
                }
            });
        }

        // Create room
        const createRoomBtn = document.getElementById('videoCallCreateRoomButton');
        if (createRoomBtn) {
            createRoomBtn.addEventListener('click', () => {
                const name = prompt('Enter room name:');
                if (name) this.createRoom(name);
            });
        }

        // Leave room
        const leaveRoomBtn = document.getElementById('videoCallLeaveRoomButton');
        if (leaveRoomBtn) {
            leaveRoomBtn.addEventListener('click', () => {
                this.leaveRoom();
            });
        }

        // Send message
        const sendMessageBtn = document.getElementById('videoCallSendMessage');
        const messageInput = document.getElementById('videoCallMessageInput');
        if (sendMessageBtn && messageInput) {
            const sendMessage = () => {
                const message = messageInput.value.trim();
                if (message) {
                    this.sendChatMessage(message);
                    messageInput.value = '';
                }
            };

            sendMessageBtn.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        }

        // Toggle transcription
        const toggleTranscriptionBtn = document.getElementById('videoCallToggleTranscription');
        if (toggleTranscriptionBtn) {
            toggleTranscriptionBtn.addEventListener('click', () => {
                if (this.isTranscribing) {
                    this.stopTranscription();
                } else {
                    this.startTranscription();
                }
            });
        }

        // Summarize transcription
        const summarizeBtn = document.getElementById('summarizeTranscriptionBtn');
        if (summarizeBtn) {
            summarizeBtn.addEventListener('click', () => this.summarizeTranscription());
        }

        // Clear transcription
        const clearBtn = document.getElementById('clearTranscriptionBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearTranscription());
        }
    }

    async loadRooms() {
        try {
            if (!document.getElementById('videoCallRoomsList')) {
                console.log('Rooms list element does not exist');
                return;
            }

            const roomsList = document.getElementById('videoCallRoomsList');
            if (!roomsList) {
                console.error('Rooms list element not found');
                return;
            }

            showLoading('Loading rooms...');
            const roomsData = await rooms.getRooms();
            
            if (!document.getElementById('videoCallRoomsList')) {
                console.log('Rooms list element no longer exists');
                return;
            }

            roomsList.innerHTML = '';

            if (Array.isArray(roomsData)) {
                roomsData.forEach(room => {
                    const roomCard = document.createElement('div');
                    roomCard.className = 'bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-300 border border-gray-200 overflow-hidden';
                    roomCard.innerHTML = `
                        <div class="p-6">
                            <div class="flex items-center justify-between mb-4">
                                <h3 class="text-lg font-semibold text-gray-900">${room.name}</h3>
                                <span class="text-sm text-gray-500">${room.participants || 0} participants</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <button class="join-room-btn px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors" data-room-id="${room.id}" data-room-name="${room.name}">
                                    Join Room
                                </button>
                                <button class="delete-room-btn text-red-600 hover:text-red-700 transition-colors" data-room-id="${room.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `;

                    // Add event listeners
                    const joinBtn = roomCard.querySelector('.join-room-btn');
                    const deleteBtn = roomCard.querySelector('.delete-room-btn');

                    joinBtn.addEventListener('click', () => {
                        const roomId = joinBtn.dataset.roomId;
                        const roomName = joinBtn.dataset.roomName;
                        this.joinRoom(roomId, roomName);
                    });

                    deleteBtn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (confirm('Are you sure you want to delete this room?')) {
                            try {
                                await rooms.deleteRoom(deleteBtn.dataset.roomId);
                                await this.loadRooms();
                                showSuccess('Room deleted successfully');
                            } catch (error) {
                                showError('Failed to delete room');
                            }
                        }
                    });

                    roomsList.appendChild(roomCard);
                });

                if (roomsData.length === 0) {
                    roomsList.innerHTML = `
                        <div class="text-center py-8">
                            <div class="mb-4">
                                <i class="fas fa-video text-4xl text-gray-400"></i>
                            </div>
                            <p class="text-lg font-medium">No rooms available</p>
                            <p class="text-sm mt-2">Create a room to get started with video calls!</p>
                        </div>
                    `;
                }
            } else {
                showError('Invalid response format from server');
            }
        } catch (error) {
            console.error('Error loading rooms:', error);
            if (document.getElementById('videoCallRoomsList')) {
                showError('Error loading rooms: ' + error);
            }
        } finally {
            showLoading(false);
        }
    }

    async createRoom(name) {
        try {
            // Validate room name
            if (!name || name.trim().length === 0) {
                showError('Room name cannot be empty');
                return;
            }
            
            if (name.trim().length < 3) {
                showError('Room name must be at least 3 characters long');
                return;
            }
            
            showLoading('Creating room...');
            const room = await rooms.createRoom(name.trim());
            await this.joinRoom(room.id, room.name, true);  // Pass isNewRoom flag
        } catch (error) {
            showError('Error creating room: ' + error);
        } finally {
            showLoading(false);
        }
    }

    async joinRoom(roomId, roomName, isNewRoom = false) {
        try {
            showLoading('Joining room...');
            this.currentRoom = roomId;
            document.getElementById('videoCallRoomsList').style.display = 'none';
            document.getElementById('videoCallActiveRoom').style.display = 'block';
            document.getElementById('videoCallRoomName').textContent = roomName;

            // Get user media with explicit constraints
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true
                });
                
                this.localStream = stream;
                
                // Show local video immediately
                const localVideo = document.getElementById('videoCallLocalVideo');
                localVideo.srcObject = stream;
                localVideo.muted = true; // Mute local video to prevent echo
                
                // Set initial states for tracks
                const videoTrack = stream.getVideoTracks()[0];
                const audioTrack = stream.getAudioTracks()[0];
                
                if (videoTrack) {
                    videoTrack.enabled = true;
                }
                if (audioTrack) {
                    audioTrack.enabled = true;
                }

                // Set initial UI states
                const videoButton = document.getElementById('videoCallToggleVideo');
                const audioButton = document.getElementById('videoCallToggleAudio');
                
                if (videoButton) {
                    videoButton.querySelector('.fa-video').classList.remove('hidden');
                    videoButton.querySelector('.fa-video-slash').classList.add('hidden');
                }
                
                if (audioButton) {
                    audioButton.querySelector('.fa-microphone').classList.remove('hidden');
                    audioButton.querySelector('.fa-microphone-slash').classList.add('hidden');
                }

            } catch (mediaError) {
                console.error('Media access error:', mediaError);
                throw new Error('Failed to access camera and microphone. Please ensure they are connected and permissions are granted.');
            }

            // Connect to WebSocket
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('Authentication required');
            }

            // Use the same host and port as the API
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//localhost:8000/ws/room/${roomId}?token=${encodeURIComponent(token)}`;
            console.log('Attempting WebSocket connection to:', wsUrl);

            // Try to connect to WebSocket with retries
            let retries = 3;
            let lastError = null;
            
            while (retries > 0) {
                try {
                    console.log(`WebSocket connection attempt ${4 - retries}/3...`);
                    
                    this.socket = new WebSocket(wsUrl);
                    
                    // Wait for connection to be established
                    await new Promise((resolve, reject) => {
                        const timeout = setTimeout(() => {
                            console.error('WebSocket connection timeout');
                            if (this.socket) {
                                this.socket.close();
                            }
                            reject(new Error('Connection timeout after 10 seconds'));
                        }, 10000);

                        this.socket.onopen = () => {
                            console.log('WebSocket connection established successfully');
                            clearTimeout(timeout);
                            resolve();
                        };

                        this.socket.onerror = (error) => {
                            console.error('WebSocket connection error:', error);
                            clearTimeout(timeout);
                            reject(new Error('Failed to connect to room server. Please check your network connection.'));
                        };

                        // Add onclose handler during connection phase
                        this.socket.onclose = (event) => {
                            console.error('WebSocket closed during connection:', {
                                code: event.code,
                                reason: event.reason,
                                wasClean: event.wasClean
                            });
                            clearTimeout(timeout);
                            reject(new Error(`Connection closed: ${event.reason || 'Unknown reason'}`));
                        };
                    });

                    // If we get here, connection was successful
                    this.setupWebSocket();
                    if (!isNewRoom) {  // Only show join message if not a new room
                        showSuccess('Joined room successfully');
                    }
                    return;
                    
                } catch (error) {
                    console.error('WebSocket connection attempt failed:', {
                        error: error.message,
                        retryNumber: 4 - retries,
                        remainingRetries: retries - 1
                    });
                    lastError = error;
                    retries--;
                    
                    if (retries > 0) {
                        console.log(`Retrying WebSocket connection in 2 seconds... (${retries} attempts remaining)`);
                        await new Promise(resolve => setTimeout(resolve, 2000));
                    }
                }
            }
            
            // If we get here, all retries failed
            throw new Error(`Failed to establish WebSocket connection after 3 attempts. Last error: ${lastError?.message}`);
            
        } catch (error) {
            console.error('Room join error:', {
                error: error.message,
                stack: error.stack,
                roomId: roomId
            });
            
            if (error.message === 'Authentication required') {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                history.pushState(null, '', '/login');
                loadLoginForm();
                showError('Please login to join rooms');
            } else {
                showError(`Error joining room: ${error.message}`);
                this.leaveRoom();
            }
        } finally {
            showLoading(false);
        }
    }

    setupWebSocket() {
        if (!this.socket) return;

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
            this.reconnectAttempts = 0;
            this.startHeartbeat();
        };

        this.socket.onmessage = async (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('Received WebSocket message:', message);
                
                // Reset reconnection counter on any successful message
                this.reconnectAttempts = 0;
                this.lastHeartbeat = Date.now();
                
                switch (message.type) {
                    case 'heartbeat':
                        this.lastHeartbeat = Date.now();
                        break;
                    case 'user-joined':
                        await this.handleUserJoined(message.userId, message.username);
                        break;
                    case 'user-left':
                        this.handleUserLeft(message.userId);
                        break;
                    case 'offer':
                        await this.handleOffer(message.userId, message.offer);
                        break;
                    case 'answer':
                        await this.handleAnswer(message.userId, message.answer);
                        break;
                    case 'ice-candidate':
                        await this.handleIceCandidate(message.userId, message.candidate);
                        break;
                    case 'chat':
                        this.displayChatMessage(message);
                        break;
                    default:
                        console.warn('Unknown message type:', message.type);
                }
            } catch (error) {
                console.error('Error handling WebSocket message:', {
                    error: error.message,
                    data: event.data
                });
            }
        };

        this.socket.onclose = async (event) => {
            console.log('WebSocket connection closed:', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean,
                attempts: this.reconnectAttempts
            });
            
            this.stopHeartbeat();

            if (event.code === 1008) {
                // Authentication error - no retry
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                history.pushState(null, '', '/login');
                loadLoginForm();
                showError('Please login to join rooms');
                return;
            }

            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts);
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect in ${delay/1000} seconds... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                showLoading(`Connection lost. Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                
                await new Promise(resolve => setTimeout(resolve, delay));
                
                if (this.currentRoom) {
                    try {
                        await this.joinRoom(this.currentRoom, document.getElementById('videoCallRoomName').textContent);
                        // Remove success message on reconnect to avoid duplicate notifications
                    } catch (error) {
                        console.error('Reconnection failed:', error);
                        if (this.reconnectAttempts === this.maxReconnectAttempts) {
                            showError('Failed to reconnect after multiple attempts');
                            this.leaveRoom();
                        }
                    }
                }
            } else {
                showError('Disconnected from room: Connection lost');
                this.leaveRoom();
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', {
                error: error,
                readyState: this.socket.readyState
            });
        };
    }

    startHeartbeat() {
        // Clear any existing heartbeat
        this.stopHeartbeat();
        
        // Start heartbeat interval
        this.lastHeartbeat = Date.now();
        this.heartbeatTimeout = setInterval(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                try {
                    // Send heartbeat
                    this.socket.send(JSON.stringify({ type: 'heartbeat' }));
                    
                    // Check if we've received a heartbeat recently
                    const timeSinceLastHeartbeat = Date.now() - this.lastHeartbeat;
                    if (timeSinceLastHeartbeat > 45000) { // 45 seconds
                        console.warn('No heartbeat received for 45 seconds, closing connection');
                        this.socket.close(4000, 'Heartbeat timeout');
                    }
                } catch (error) {
                    console.error('Error sending heartbeat:', error);
                    this.socket.close(4000, 'Heartbeat failed');
                }
            }
        }, 15000); // Send heartbeat every 15 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatTimeout) {
            clearInterval(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }

    async handleUserJoined(userId, username) {
        // Create a new RTCPeerConnection for the user
        const peerConnection = new RTCPeerConnection(this.configuration);
        this.peerConnections[userId] = peerConnection;

        // Add local tracks to the connection
        this.localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, this.localStream);
        });

        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.send(JSON.stringify({
                    type: 'ice-candidate',
                    userId: userId,
                    candidate: event.candidate
                }));
            }
        };

        // Handle remote tracks
        peerConnection.ontrack = (event) => {
            const remoteVideo = document.createElement('video');
            remoteVideo.id = `video-${userId}`;
            remoteVideo.autoplay = true;
            remoteVideo.playsInline = true;
            remoteVideo.srcObject = event.streams[0];

            const videoContainer = document.createElement('div');
            videoContainer.id = `container-${userId}`;
            videoContainer.className = 'video-container';
            videoContainer.appendChild(remoteVideo);

            document.getElementById('videoCallRemoteVideos').appendChild(videoContainer);
        };

        // Create and send offer
        try {
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            this.socket.send(JSON.stringify({
                type: 'offer',
                userId: userId,
                offer: offer
            }));
        } catch (error) {
            console.error('Error creating offer:', error);
        }
    }

    async handleOffer(userId, offer) {
        const peerConnection = new RTCPeerConnection(this.configuration);
        this.peerConnections[userId] = peerConnection;

        // Add local tracks
        this.localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, this.localStream);
        });

        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.send(JSON.stringify({
                    type: 'ice-candidate',
                    userId: userId,
                    candidate: event.candidate
                }));
            }
        };

        // Handle remote tracks
        peerConnection.ontrack = (event) => {
            const remoteVideo = document.createElement('video');
            remoteVideo.id = `video-${userId}`;
            remoteVideo.autoplay = true;
            remoteVideo.playsInline = true;
            remoteVideo.srcObject = event.streams[0];

            const videoContainer = document.createElement('div');
            videoContainer.id = `container-${userId}`;
            videoContainer.className = 'video-container';
            videoContainer.appendChild(remoteVideo);

            document.getElementById('videoCallRemoteVideos').appendChild(videoContainer);
        };

        // Set remote description and create answer
        try {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            this.socket.send(JSON.stringify({
                type: 'answer',
                userId: userId,
                answer: answer
            }));
        } catch (error) {
            console.error('Error handling offer:', error);
        }
    }

    async handleAnswer(userId, answer) {
        try {
            const peerConnection = this.peerConnections[userId];
            if (peerConnection) {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            }
        } catch (error) {
            console.error('Error handling answer:', error);
        }
    }

    async handleIceCandidate(userId, candidate) {
        try {
            const peerConnection = this.peerConnections[userId];
            if (peerConnection) {
                await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            }
        } catch (error) {
            console.error('Error handling ICE candidate:', error);
        }
    }

    handleUserLeft(userId) {
        // Close peer connection
        if (this.peerConnections[userId]) {
            this.peerConnections[userId].close();
            delete this.peerConnections[userId];
        }

        // Remove video element
        const videoContainer = document.getElementById(`container-${userId}`);
        if (videoContainer) {
            videoContainer.remove();
        }
    }

    async leaveRoom() {
        let socket = null;
        try {
            if (this.currentRoom) {
                showLoading('Leaving room...');
                
                // First, close all peer connections
                Object.values(this.peerConnections).forEach(connection => {
                    if (connection && connection.signalingState !== 'closed') {
                        connection.close();
                    }
                });
                this.peerConnections = {};

                // Stop local stream
                if (this.localStream) {
                    this.localStream.getTracks().forEach(track => track.stop());
                    this.localStream = null;
                }

                // Stop screen sharing if active
                if (this.screenStream) {
                    this.screenStream.getTracks().forEach(track => track.stop());
                    this.screenStream = null;
                    this.isScreenSharing = false;
                }

                // Stop heartbeat before handling socket
                this.stopHeartbeat();

                // Safely handle WebSocket
                if (this.socket) {
                    socket = this.socket;
                    this.socket = null;  // Clear the reference immediately
                    
                    if (socket.readyState === WebSocket.OPEN) {
                        try {
                            socket.send(JSON.stringify({ type: 'leave-room' }));
                            await new Promise(resolve => setTimeout(resolve, 100));
                        } catch (wsError) {
                            console.warn('Error sending leave message:', wsError);
                        }
                    }
                }

                // Check if elements still exist before updating UI
                const roomsList = document.getElementById('videoCallRoomsList');
                const activeRoom = document.getElementById('videoCallActiveRoom');
                const remoteVideos = document.getElementById('videoCallRemoteVideos');

                if (roomsList && activeRoom && remoteVideos) {
                    roomsList.style.display = 'grid';
                    activeRoom.style.display = 'none';
                    remoteVideos.innerHTML = '';
                    
                    // Reset room state
                    this.currentRoom = null;
                    this.chatMessages = [];
                    this.unreadMessages = 0;

                    // Only reload rooms if component is still mounted
                    await this.loadRooms();
                    showSuccess('Left room successfully');
                }
            }
        } catch (error) {
            console.error('Error leaving room:', {
                error: error.message,
                stack: error.stack,
                roomId: this.currentRoom
            });
            // Only show error if component is still mounted
            if (document.getElementById('videoCallContainer')) {
                showError('Error leaving room: ' + (error.message || 'Failed to leave room'));
            }
        } finally {
            showLoading(false);
            
            // Final cleanup of socket if it exists
            if (socket) {
                try {
                    if (socket.readyState !== WebSocket.CLOSED) {
                        socket.close(1000, 'User left room');
                    }
                } catch (closeError) {
                    console.warn('Error closing socket in finally:', closeError);
                }
            }
            
            // Ensure all state is reset
            this.currentRoom = null;
            this.socket = null;
            this.stopHeartbeat();
            this.peerConnections = {};
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }
            if (this.screenStream) {
                this.screenStream.getTracks().forEach(track => track.stop());
                this.screenStream = null;
            }
            this.isScreenSharing = false;
        }
    }

    cleanup(isNavigating = false) {
        let socket = null;
        try {
            // Stop heartbeat first
            this.stopHeartbeat();

            // Close all peer connections
            Object.values(this.peerConnections).forEach(connection => {
                if (connection && connection.signalingState !== 'closed') {
                    connection.close();
                }
            });
            this.peerConnections = {};

            // Stop local stream if it exists
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }

            // Safely handle WebSocket
            if (this.socket) {
                socket = this.socket;
                this.socket = null;  // Clear the reference immediately
                
                if (socket.readyState === WebSocket.OPEN) {
                    try {
                        socket.send(JSON.stringify({ type: 'leave-room' }));
                    } catch (wsError) {
                        console.warn('Error sending leave message:', wsError);
                    }
                }
            }

            // Reset current room
            this.currentRoom = null;

            // Only remove the container if we're not in the middle of navigation
            if (!isNavigating) {
                const container = document.getElementById('videoCallContainer');
                if (container) {
                    container.remove();
                }
            }

            // Stop screen sharing if active
            if (this.screenStream) {
                this.screenStream.getTracks().forEach(track => track.stop());
                this.screenStream = null;
            }
            this.isScreenSharing = false;

        } catch (error) {
            console.error('Error during cleanup:', error);
        } finally {
            // Final cleanup of socket if it exists
            if (socket) {
                try {
                    if (socket.readyState !== WebSocket.CLOSED) {
                        socket.close(1000, 'Cleanup');
                    }
                } catch (closeError) {
                    console.warn('Error closing socket in cleanup finally:', closeError);
                }
            }
            
            // Ensure all state is reset
            this.currentRoom = null;
            this.socket = null;
            this.stopHeartbeat();
            this.peerConnections = {};
        }
    }

    async startScreenShare() {
        try {
            // Get screen sharing stream
            this.screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    cursor: "always"
                },
                audio: false
            });

            // Update UI
            const button = document.getElementById('videoCallToggleScreenShare');
            const desktopIcon = button.querySelector('.fa-desktop');
            const stopIcon = button.querySelector('.fa-stop');
            button.classList.add('sharing');
            desktopIcon.style.display = 'none';
            stopIcon.style.display = 'inline';

            // Add screen track to all peer connections
            const screenTrack = this.screenStream.getVideoTracks()[0];
            Object.values(this.peerConnections).forEach(async (pc) => {
                const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) {
                    await sender.replaceTrack(screenTrack);
                }
            });

            // Handle stop sharing
            screenTrack.addEventListener('ended', () => {
                this.stopScreenShare();
            });

            this.isScreenSharing = true;
            document.getElementById('videoCallLocalContainer').classList.add('screen-share');
            document.getElementById('videoCallLocalVideo').srcObject = this.screenStream;

        } catch (error) {
            if (error.name === 'NotAllowedError') {
                throw new Error('Screen sharing permission denied');
            } else {
                throw new Error('Failed to start screen sharing: ' + error.message);
            }
        }
    }

    async stopScreenShare() {
        if (!this.isScreenSharing || !this.screenStream) return;

        try {
            // Stop all screen sharing tracks
            this.screenStream.getTracks().forEach(track => track.stop());

            // Update UI
            const button = document.getElementById('videoCallToggleScreenShare');
            const desktopIcon = button.querySelector('.fa-desktop');
            const stopIcon = button.querySelector('.fa-stop');
            button.classList.remove('sharing');
            desktopIcon.style.display = 'inline';
            stopIcon.style.display = 'none';

            // Replace screen track with camera track in all peer connections
            const videoTrack = this.localStream.getVideoTracks()[0];
            Object.values(this.peerConnections).forEach(async (pc) => {
                const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) {
                    await sender.replaceTrack(videoTrack);
                }
            });

            this.isScreenSharing = false;
            document.getElementById('videoCallLocalContainer').classList.remove('screen-share');
            document.getElementById('videoCallLocalVideo').srcObject = this.localStream;
            this.screenStream = null;

        } catch (error) {
            console.error('Error stopping screen share:', error);
            throw new Error('Failed to stop screen sharing: ' + error.message);
        }
    }

    sendChatMessage() {
        const input = document.getElementById('videoCallMessageInput');
        const message = input.value.trim();
        
        if (message && this.socket && this.socket.readyState === WebSocket.OPEN) {
            const chatMessage = {
                type: 'chat',
                message: message,
                timestamp: new Date().toISOString()
            };
            
            this.socket.send(JSON.stringify(chatMessage));
            this.displayChatMessage(chatMessage, true);
            input.value = '';
        }
    }

    displayChatMessage(message, isSent = false) {
        const chatMessages = document.getElementById('videoCallChatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${isSent ? 'flex justify-end' : 'flex justify-start'}`;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        
        messageElement.innerHTML = `
            <div class="${isSent ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-900'} rounded-lg px-4 py-2 max-w-[80%]">
                ${!isSent ? `<div class="text-xs text-gray-600 font-medium mb-1">${message.sender || 'Anonymous'}</div>` : ''}
                <div class="break-words">${this.escapeHtml(message.message)}</div>
                <div class="text-xs ${isSent ? 'text-white/80' : 'text-gray-500'} mt-1">${timestamp}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Update unread count if chat is collapsed
        if (!isSent && document.querySelector('.chat-section').classList.contains('collapsed')) {
            this.unreadMessages++;
            this.updateUnreadBadge();
        }
    }

    updateUnreadBadge() {
        const toggleChat = document.getElementById('videoCallToggleChat');
        const existingBadge = toggleChat.querySelector('.unread-badge');
        
        if (this.unreadMessages > 0) {
            if (existingBadge) {
                existingBadge.textContent = this.unreadMessages;
            } else {
                const badge = document.createElement('span');
                badge.className = 'unread-badge absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full min-w-[20px] text-center';
                badge.textContent = this.unreadMessages;
                toggleChat.appendChild(badge);
            }
        } else if (existingBadge) {
            existingBadge.remove();
        }
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // If less than 24 hours ago, show relative time
        if (diff < 24 * 60 * 60 * 1000) {
            const hours = Math.floor(diff / (60 * 60 * 1000));
            if (hours < 1) {
                const minutes = Math.floor(diff / (60 * 1000));
                return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
            }
            return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        }
        
        // Otherwise show the date
        return date.toLocaleDateString(undefined, { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    startTranscription() {
        if (!this.recognition) {
            showError('Speech recognition is not supported in your browser');
            return;
        }

        const transcriptionArea = document.getElementById('transcriptionArea');
        const toggleTranscriptionBtn = document.getElementById('videoCallToggleTranscription');
        
        if (transcriptionArea && toggleTranscriptionBtn) {
            transcriptionArea.classList.remove('hidden');
            toggleTranscriptionBtn.classList.add('text-primary-600');
            this.isTranscribing = true;
            this.recognition.start();
        }
    }

    stopTranscription() {
        if (!this.recognition) return;

        const transcriptionArea = document.getElementById('transcriptionArea');
        const toggleTranscriptionBtn = document.getElementById('videoCallToggleTranscription');
        
        if (transcriptionArea && toggleTranscriptionBtn) {
            transcriptionArea.classList.add('hidden');
            toggleTranscriptionBtn.classList.remove('text-primary-600');
            this.isTranscribing = false;
            this.recognition.stop();
        }
    }

    async summarizeTranscription() {
        try {
            if (this.transcriptionHistory.length === 0) {
                showError('No transcription to summarize');
                return;
            }

            const transcriptionText = this.transcriptionHistory.map(t => t.text).join(' ');
            showLoading('Generating summary...');

            const data = await video.summarizeTranscription(transcriptionText);
            const summaryArea = document.getElementById('transcriptionSummary');
            const summaryText = document.getElementById('summaryText');
            
            if (summaryArea && summaryText) {
                summaryArea.classList.remove('hidden');
                summaryText.textContent = data.summary;
                summaryArea.scrollIntoView({ behavior: 'smooth' });
                showSuccess('Summary generated successfully');
            }
        } catch (error) {
            console.error('Error generating summary:', error);
            showError('Failed to generate summary. Please try again.');
        } finally {
            showLoading(false);
        }
    }

    clearTranscription() {
        this.transcriptionHistory = [];
        const transcriptionText = document.getElementById('transcriptionText');
        const summaryArea = document.getElementById('transcriptionSummary');
        
        if (transcriptionText) {
            transcriptionText.innerHTML = '';
        }
        
        if (summaryArea) {
            summaryArea.classList.add('hidden');
        }
    }
}

// Create and export a singleton instance
export const videoCall = new VideoCall(); 