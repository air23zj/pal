import { search } from '../utils/search-api';
import { showLoading, showError } from '../utils/ui';
import { marked } from 'marked';
import { loadMainContent } from '../main.js';

let player = null;

function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : false;
}

export function loadYouTubeInterface() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold">YouTube Video Summaries</h2>
                <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>
                    Back to Home
                </button>
            </div>
            <div class="mb-8">
                <input type="text" id="youtubeInput" 
                    class="w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-primary-500 focus:border-primary-500" 
                    placeholder="Paste YouTube URL here...">
                <button id="summarizeButton" 
                    class="mt-4 w-full bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors">
                    Generate Summary
                </button>
            </div>
            <div class="flex flex-col lg:flex-row gap-8">
                <div id="videoContainer" class="hidden lg:w-[45%]">
                    <div class="sticky top-4">
                        <div class="aspect-w-16 aspect-h-9">
                            <div id="youtubePlayer" class="w-full h-full rounded-lg shadow-lg"></div>
                        </div>
                    </div>
                </div>
                <div id="summaryContainer" class="hidden lg:flex-1">
                    <div class="prose bg-white p-6 rounded-lg shadow-sm max-w-none">
                        <h3 class="text-xl font-semibold mb-4">Video Summary</h3>
                        <div class="summary-content"></div>
                    </div>
                </div>
            </div>
            <div id="loadingIndicator" class="hidden">
                <div class="flex justify-center items-center py-8">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
            </div>
            <div id="errorContainer" class="hidden">
                <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-red-700" id="errorMessage"></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Load YouTube IFrame API
    if (!window.YT) {
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }

    // Add event listeners
    const youtubeInput = document.getElementById('youtubeInput');
    const summarizeButton = document.getElementById('summarizeButton');
    const backButton = document.getElementById('backButton');

    summarizeButton.addEventListener('click', () => summarizeVideo(youtubeInput.value));
    youtubeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            summarizeVideo(youtubeInput.value);
        }
    });

    // Add back button functionality
    backButton.addEventListener('click', () => {
        if (player) {
            player.destroy();
            player = null;
        }
        history.pushState(null, '', '/');
        loadMainContent();
    });
}

function createPlayer(videoId) {
    if (player) {
        player.destroy();
    }

    const playerConfig = {
        height: '100%',
        width: '100%',
        videoId: videoId,
        playerVars: {
            playsinline: 1,
            enablejsapi: 1,
            origin: window.location.origin,
            rel: 0
        },
        events: {
            onReady: onPlayerReady,
            onError: (e) => console.error('Player error:', e)
        }
    };

    // Check if YouTube API is ready
    if (window.YT && window.YT.Player) {
        player = new window.YT.Player('youtubePlayer', playerConfig);
    } else {
        // If API is not ready, wait for it
        window.onYouTubeIframeAPIReady = function() {
            player = new window.YT.Player('youtubePlayer', playerConfig);
        };
    }
}

function onPlayerReady(event) {
    console.log('Player ready');
}

function convertTimestampToSeconds(timestamp) {
    const parts = timestamp.split(':').map(Number);
    if (parts.length === 2) {
        return parts[0] * 60 + parts[1];
    }
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
}

async function summarizeVideo(url) {
    if (!url.trim()) {
        showError('Please enter a YouTube URL');
        return;
    }

    const videoId = extractVideoId(url);
    if (!videoId) {
        showError('Invalid YouTube URL');
        return;
    }

    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorContainer = document.getElementById('errorContainer');
    const summaryContainer = document.getElementById('summaryContainer');
    const videoContainer = document.getElementById('videoContainer');
    
    try {
        loadingIndicator.classList.remove('hidden');
        errorContainer.classList.add('hidden');
        summaryContainer.classList.add('hidden');
        videoContainer.classList.add('hidden');

        // Create YouTube player
        videoContainer.classList.remove('hidden');
        createPlayer(videoId);

        const response = await search.youtube(url);
        const result = response.data;
        
        if (!result || !result.summary) {
            throw new Error('Invalid response from server');
        }

        displaySummary(result, videoId);
    } catch (error) {
        console.error('YouTube summary error:', error);
        errorContainer.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = 
            error.response?.data?.detail || error.message || 'Failed to generate summary. Please try again.';
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

function displaySummary(result, videoId) {
    const summaryContainer = document.getElementById('summaryContainer');
    const summaryContent = summaryContainer.querySelector('.summary-content');
    
    // Convert the summary to HTML using marked
    const summaryHtml = marked.parse(result.summary);

    // Add click handlers for timestamps, including ranges
    const processedHtml = summaryHtml.replace(
        /\[(\d{2}:\d{2}(?::\d{2})?(?:-\d{2}:\d{2}(?::\d{2})?)?)\]/g,
        (match, timestamp) => {
            // Handle timestamp ranges
            const timestamps = timestamp.split('-');
            const startTime = convertTimestampToSeconds(timestamps[0]);
            // For ranges, we store both start and end times, but only jump to start time on click
            const timeData = timestamps.length > 1 ? 
                `data-time="${startTime}" data-end-time="${convertTimestampToSeconds(timestamps[1])}"` :
                `data-time="${startTime}"`;
            return `<a href="javascript:void(0)" class="timestamp text-primary-600 hover:text-primary-700 hover:underline cursor-pointer" ${timeData}>[${timestamp}]</a>`;
        }
    );
    
    summaryContent.innerHTML = processedHtml;
    
    // Add click handlers for timestamps
    const timestamps = summaryContent.getElementsByClassName('timestamp');
    Array.from(timestamps).forEach(link => {
        link.onclick = function(e) {
            e.preventDefault();
            const seconds = parseInt(this.getAttribute('data-time'));
            if (player && typeof player.seekTo === 'function') {
                player.seekTo(seconds);
                player.playVideo();
            }
        };
    });
    
    summaryContainer.classList.remove('hidden');
    document.getElementById('videoContainer').classList.remove('hidden');
}
