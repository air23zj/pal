import { showLoading, showError, showSuccess } from '../utils/ui';
import { voiceMemos } from '../utils/voice-memos-api';

export async function loadVoiceMemoInterface() {
    // Check authentication
    const token = localStorage.getItem('token');
    if (!token) {
        const mainContent = document.getElementById('mainContent');
        mainContent.innerHTML = `
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div class="text-center">
                    <p class="text-red-500 mb-4">Please log in to use Voice Memos</p>
                    <button id="loginButton" class="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors">
                        Go to Login
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('loginButton').addEventListener('click', async () => {
            history.pushState(null, '', '/login');
            const { loadLoginForm } = await import('./auth.js');
            loadLoginForm();
        });
        return;
    }

    let mediaRecorder = null;
    let audioChunks = [];
    let timerInterval = null;
    let startTime = null;
    let recordings = [];

    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-gray-900">Voice Memos</h2>
                <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>
                    Back to Home
                </button>
            </div>

            <!-- Recording Interface -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <div class="flex items-center justify-center space-x-4">
                    <button id="recordButton" class="flex items-center justify-center w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors">
                        <i class="fas fa-microphone text-white text-2xl"></i>
                    </button>
                    <div id="recordingStatus" class="text-gray-600">
                        Click to start recording
                    </div>
                    <div id="recordingTimer" class="hidden font-mono text-lg">
                        00:00
                    </div>
                </div>
            </div>

            <!-- Recordings List -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Your Recordings</h3>
                <div id="recordingsList" class="space-y-4">
                    <!-- Recordings will be dynamically inserted here -->
                </div>
            </div>
        </div>
    `;

    // Initialize back button
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', async () => {
        history.pushState(null, '', '/');
        const { loadMainContent } = await import('../main.js');
        loadMainContent();
    });

    // Initialize recording functionality
    const recordButton = document.getElementById('recordButton');
    const recordingStatus = document.getElementById('recordingStatus');
    const timerDisplay = document.getElementById('recordingTimer');

    // Load existing recordings
    await loadRecordings();

    // Add record button click handler
    recordButton.addEventListener('click', async () => {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: mimeType,
                    audioBitsPerSecond: 128000
                });
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: mimeType });
                    const duration = getDuration(startTime);
                    
                    try {
                        // Create FormData and append the audio blob and duration
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recording.webm');
                        formData.append('duration', duration);
                        
                        await voiceMemos.createMemo(formData);
                        await loadRecordings();
                        showSuccess('Recording saved successfully');
                    } catch (error) {
                        console.error('Error saving recording:', error);
                        showError('Failed to save recording');
                    }
                };

                mediaRecorder.start(1000);
                startTime = Date.now();
                updateRecordingUI(true);
                startTimer();
            } catch (error) {
                console.error('Error accessing microphone:', error);
                showError('Could not access microphone. Please ensure you have granted permission.');
            }
        } else {
            stopRecording();
        }
    });

    async function loadRecordings() {
        try {
            recordings = await voiceMemos.getMemos();
            await displayRecordings();
        } catch (error) {
            console.error('Error loading recordings:', error);
            showError('Failed to load recordings');
        }
    }

    function updateRecordingUI(isRecording) {
        const icon = recordButton.querySelector('i');
        if (isRecording) {
            recordButton.classList.remove('bg-red-500', 'hover:bg-red-600');
            recordButton.classList.add('bg-gray-500', 'hover:bg-gray-600');
            icon.classList.remove('fa-microphone');
            icon.classList.add('fa-stop');
            recordingStatus.textContent = 'Recording...';
            timerDisplay.classList.remove('hidden');
        } else {
            recordButton.classList.remove('bg-gray-500', 'hover:bg-gray-600');
            recordButton.classList.add('bg-red-500', 'hover:bg-red-600');
            icon.classList.remove('fa-stop');
            icon.classList.add('fa-microphone');
            recordingStatus.textContent = 'Click to start recording';
            timerDisplay.classList.add('hidden');
        }
    }

    function startTimer() {
        timerInterval = setInterval(() => {
            const duration = getDuration(startTime);
            document.getElementById('recordingTimer').textContent = duration;
        }, 1000);
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            clearInterval(timerInterval);
            updateRecordingUI(false);
        }
    }

    function getDuration(startTime) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        return `${minutes}:${seconds}`;
    }

    async function displayRecordings() {
        const recordingsList = document.getElementById('recordingsList');
        if (recordings.length === 0) {
            recordingsList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    No recordings yet. Click the microphone button to start recording.
                </div>
            `;
            return;
        }

        recordingsList.innerHTML = recordings
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .map(recording => `
                <div class="bg-gray-50 rounded-lg overflow-hidden">
                    <div class="flex items-center justify-between p-4">
                        <div class="flex items-center space-x-4">
                            <button class="play-button" data-id="${recording.id}">
                                <i class="fas fa-play text-primary-600 hover:text-primary-700"></i>
                            </button>
                            <div>
                                <div class="text-sm text-gray-600">
                                    ${new Date(recording.created_at).toLocaleString()}
                                </div>
                                <div class="text-xs text-gray-500">
                                    Duration: ${recording.duration}
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-3">
                            ${!recording.transcription ? `
                                <button class="transcribe-button text-primary-600 hover:text-primary-700" data-id="${recording.id}">
                                    <i class="fas fa-closed-captioning"></i>
                                </button>
                            ` : `
                                <button class="toggle-transcription-button text-primary-600 hover:text-primary-700" data-id="${recording.id}">
                                    <i class="fas fa-chevron-down"></i>
                                </button>
                            `}
                            <button class="delete-button text-red-600 hover:text-red-700" data-id="${recording.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    ${recording.transcription ? `
                        <div class="transcription-content hidden border-t border-gray-200 p-4" data-id="${recording.id}">
                            <div class="space-y-4">
                                <div>
                                    <h4 class="font-medium text-sm text-gray-700 mb-2">Transcription:</h4>
                                    <div class="transcription-text bg-white p-3 rounded text-sm text-gray-600">
                                        ${recording.transcription}
                                    </div>
                                </div>
                                <div>
                                    <h4 class="font-medium text-sm text-gray-700 mb-2">Summary:</h4>
                                    <div class="summary-text bg-white p-3 rounded text-sm text-gray-600">
                                        ${recording.summary || 'No summary available'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `).join('');

        // Add event listeners for play buttons
        document.querySelectorAll('.play-button').forEach(button => {
            button.addEventListener('click', async () => {
                const recording = recordings.find(r => r.id === parseInt(button.dataset.id));
                if (recording) {
                    try {
                        const audioData = await voiceMemos.getMemoAudio(recording.id);
                        // Create a blob from the audio data
                        const blob = new Blob([audioData], { type: 'audio/webm' });
                        const audioUrl = URL.createObjectURL(blob);
                        const audio = new Audio(audioUrl);
                        
                        // Clean up the object URL when done
                        audio.addEventListener('ended', () => {
                            URL.revokeObjectURL(audioUrl);
                        });
                        
                        audio.play().catch(error => {
                            console.error('Error playing audio:', error);
                            showError('Failed to play recording');
                        });
                    } catch (error) {
                        console.error('Error getting audio URL:', error);
                        showError('Failed to play recording');
                    }
                }
            });
        });

        // Add event listeners for delete buttons
        document.querySelectorAll('.delete-button').forEach(button => {
            button.addEventListener('click', async () => {
                const id = parseInt(button.dataset.id);
                try {
                    await voiceMemos.deleteMemo(id);
                    recordings = recordings.filter(r => r.id !== id);
                    await displayRecordings();
                    showSuccess('Recording deleted');
                } catch (error) {
                    console.error('Error deleting recording:', error);
                    showError('Failed to delete recording');
                }
            });
        });

        // Add event listeners for transcribe buttons
        document.querySelectorAll('.transcribe-button').forEach(button => {
            button.addEventListener('click', async () => {
                const id = parseInt(button.dataset.id);
                const recording = recordings.find(r => r.id === id);
                if (recording) {
                    button.disabled = true;
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                    try {
                        const result = await voiceMemos.transcribeMemo(id);
                        recording.transcription = result.transcription;
                        recording.summary = result.summary;
                        await displayRecordings();
                        showSuccess('Transcription complete');
                    } catch (error) {
                        console.error('Transcription error:', error);
                        button.disabled = false;
                        button.innerHTML = '<i class="fas fa-closed-captioning"></i>';
                        showError('Failed to transcribe recording');
                    }
                }
            });
        });

        // Add event listeners for toggle buttons
        document.querySelectorAll('.toggle-transcription-button').forEach(button => {
            button.addEventListener('click', () => {
                const id = button.dataset.id;
                const content = document.querySelector(`.transcription-content[data-id="${id}"]`);
                const icon = button.querySelector('i');
                
                if (content.classList.contains('hidden')) {
                    content.classList.remove('hidden');
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    content.classList.add('hidden');
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            });
        });
    }
} 