import './styles/main.css';
import { auth } from './utils/api';
import { documents } from './utils/document-api';
import { search } from './utils/search-api';
import { showLoading, showError, showSuccess, formatDate } from './utils/ui';
import { marked } from 'marked';
import { loadSearchInterface } from './components/search';
import { loadYouTubeInterface } from './components/youtube';
import { loadDocumentsInterface } from './components/documents';
import { loadLoginForm, loadRegisterForm } from './components/auth';
import { loadPhotosInterface } from './components/photos';
import { videoCall, loadVideoCallInterface } from './components/video_call.js';
import { loadNewsInterface } from './components/news.js';
import { loadDealsInterface } from './components/deals.js';
import { loadVoiceMemoInterface } from './components/voice_memos.js';
import { loadHealthCompanionInterface } from './components/health_companion.js';
import { loadTravelInterface } from './components/travel.js';
import { loadWeatherInterface } from './components/weather.js';

// Feature definitions
const features = [
    {
        id: 'search',
        title: 'AI-Powered Search',
        icon: 'fa-magnifying-glass',
        description: 'Get intelligent answers with citations from reliable sources'
    },
    {
        id: 'youtube',
        title: 'YouTube Summaries',
        icon: 'fa-youtube',
        description: 'Get quick summaries of YouTube videos'
    },
    {
        id: 'documents',
        title: 'Document Manager',
        icon: 'fa-file-lines',
        description: 'Store and manage your documents securely'
    },
    {
        id: 'photos',
        title: 'Photo Gallery',
        icon: 'fa-images',
        description: 'Organize and share your photos'
    },
    {
        id: 'video-call',
        title: 'Video Calls',
        icon: 'fa-video',
        description: 'Make video calls and collaborate with others in real-time'
    },
    {
        id: 'news',
        title: 'News Feed',
        icon: 'fa-newspaper',
        description: 'Stay updated with personalized news'
    },
    {
        id: 'deals',
        title: 'Smart Deals',
        icon: 'fa-tags',
        description: 'Find the best deals and discounts'
    },
    {
        id: 'voice-memos',
        title: 'Voice Memos',
        icon: 'fa-microphone',
        description: 'Record and manage voice memos'
    },
    {
        id: 'health',
        title: 'Health Companion',
        icon: 'fa-heart',
        description: 'Track your health and fitness goals'
    },
    {
        id: 'travel',
        title: 'Travel Planner',
        icon: 'fa-plane',
        description: 'Plan and manage your trips'
    },
    {
        id: 'weather',
        title: 'Weather',
        icon: 'fa-cloud',
        description: 'Track weather conditions and forecasts'
    }
];

// Authentication utilities
const protectedFeatures = ['search', 'youtube', 'documents', 'photos', 'news', 'deals', 'voice-memos', 'health', 'travel', 'weather'];

async function checkAuthStatus() {
    const token = localStorage.getItem('token');
    if (!token) {
        return false;
    }
    try {
        // Verify token is still valid by getting user details
        const response = await auth.verify();
        if (response.valid && response.user) {
            // Update stored user ID if needed
            localStorage.setItem('userId', response.user.id.toString());
            return true;
        }
        return false;
    } catch (error) {
        console.error('Auth verification error:', error);
        handleAuthError();
        return false;
    }
}

function handleAuthError() {
    localStorage.removeItem('token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
    showError('Please login to continue');
    history.pushState(null, '', '/login');
    handleNavigation();
}

async function requireAuth(callback) {
    if (await checkAuthStatus()) {
        return callback();
    }
    handleAuthError();
}

// Initialize features
function initializeFeatures() {
    // Add data-feature attributes to feature buttons if they exist
    document.querySelectorAll('[data-feature]').forEach(button => {
        const feature = button.dataset.feature;
        if (features.find(f => f.id === feature)) {
            button.addEventListener('click', handleFeatureClick);
        }
    });
}

// Handle feature clicks with auth check
async function handleFeatureClick(e) {
    const feature = e.target.closest('[data-feature]').dataset.feature;
    
    if (protectedFeatures.includes(feature)) {
        requireAuth(() => {
            switch (feature) {
                case 'search':
                    history.pushState(null, '', '/search');
                    loadSearchInterface();
                    break;
                case 'youtube':
                    history.pushState(null, '', '/youtube');
                    loadYouTubeInterface();
                    break;
                case 'documents':
                    history.pushState(null, '', '/documents');
                    loadDocumentsInterface();
                    break;
                case 'photos':
                    history.pushState(null, '', '/photos');
                    loadPhotosInterface();
                    break;
                case 'news':
                    history.pushState(null, '', '/news');
                    loadNewsInterface();
                    break;
                case 'deals':
                    history.pushState(null, '', '/deals');
                    loadDealsInterface();
                    break;
                case 'voice-memos':
                    history.pushState(null, '', '/voice-memos');
                    loadVoiceMemoInterface();
                    break;
                case 'health':
                    history.pushState(null, '', '/health');
                    loadHealthCompanionInterface();
                    break;
                case 'travel':
                    history.pushState(null, '', '/travel');
                    loadTravelInterface();
                    break;
                case 'weather':
                    history.pushState(null, '', '/weather');
                    loadWeatherInterface();
                    break;
            }
        });
    } else {
        // Handle non-protected features here if any
        switch (feature) {
            // Add cases for public features
        }
    }
}

// Initialize auth state
function initializeAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const authButtons = document.getElementById('authButtons');
    const logoutBtn = document.getElementById('logoutBtn');
    const welcomeMessage = document.getElementById('welcomeMessage');

    if (token && username) {
        // Verify token on initialization
        checkAuthStatus().then(isValid => {
            if (!isValid) {
                handleAuthError();
                return;
            }
            // Hide auth buttons
            if (authButtons) authButtons.style.display = 'none';
            // Show logout button
            if (logoutBtn) logoutBtn.style.display = 'inline-flex';
            // Update welcome message
            if (welcomeMessage) welcomeMessage.textContent = `Welcome back, ${username}!`;
        });
    } else {
        // Show auth buttons
        if (authButtons) authButtons.style.display = 'flex';
        // Hide logout button
        if (logoutBtn) logoutBtn.style.display = 'none';
        // Reset welcome message
        if (welcomeMessage) welcomeMessage.textContent = 'Welcome to Clarity!';
    }
}

// Handle navigation with auth check
async function handleNavigation() {
    const path = window.location.pathname;
    
    // First, ensure we have the basic structure
    if (!document.getElementById('app')) {
        document.body.innerHTML = '<div id="app"><div id="mainContent"></div></div>';
    }

    // Protected routes that need authentication
    const protectedRoutes = {
        '/search': loadSearchInterface,
        '/youtube': loadYouTubeInterface,
        '/documents': loadDocumentsInterface,
        '/photos': loadPhotosInterface,
        '/video-call': loadVideoCallInterface,
        '/news': loadNewsInterface,
        '/deals': loadDealsInterface,
        '/voice-memos': loadVoiceMemoInterface,
        '/health': loadHealthCompanionInterface,
        '/travel': loadTravelInterface,
        '/weather': loadWeatherInterface
    };

    // Public routes that don't need authentication
    const publicRoutes = {
        '/login': loadLoginForm,
        '/register': loadRegisterForm,
        '/': loadMainContent
    };

    if (path in protectedRoutes) {
        requireAuth(() => protectedRoutes[path]());
    } else if (path in publicRoutes) {
        publicRoutes[path]();
    } else {
        // Handle 404 or redirect to home
        history.pushState(null, '', '/');
        loadMainContent();
    }
}

// Initialize app
function initializeApp() {
    // Initialize auth first
    const token = localStorage.getItem('token');
    if (!token && window.location.pathname !== '/register') {
        loadLoginForm();
        return;
    }
    
    // Ensure we have the basic structure
    if (!document.getElementById('app')) {
        document.body.innerHTML = '<div id="app"><div id="mainContent"></div></div>';
    }
    
    // Add event listeners
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await auth.logout();
            window.location.href = '/';
        });
    }

    // Handle auth navigation
    document.querySelectorAll('#authButtons a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const path = e.target.getAttribute('href');
            history.pushState(null, '', path);
            handleNavigation();
        });
    });

    // Initialize features and handle navigation
    initializeFeatures();
    handleNavigation();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Handle browser back/forward
window.addEventListener('popstate', handleNavigation);

export async function loadMainContent() {
    const token = localStorage.getItem('token');
    if (!token) {
        loadLoginForm();
        return;
    }

    // Ensure we have the mainContent container
    let mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        const app = document.getElementById('app') || document.createElement('div');
        app.id = 'app';
        mainContent = document.createElement('div');
        mainContent.id = 'mainContent';
        app.appendChild(mainContent);
        if (!document.getElementById('app')) {
            document.body.appendChild(app);
        }
    }

    mainContent.innerHTML = `
        <div class="max-w-6xl mx-auto px-4 py-8">
            <div class="text-center mb-12">
                <h1 class="text-4xl font-bold text-gray-900 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-primary-800">
                    Clarity AI
                </h1>
                <p class="text-xl text-gray-600">Your intelligent personal companion and assistant for everything you need.</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                ${features.map(feature => `
                    <div class="feature-card bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer" data-feature="${feature.id}">
                        <div class="text-primary-600 mb-6">
                            <i class="fas ${feature.icon} text-4xl"></i>
                        </div>
                        <h3 class="text-xl font-semibold mb-3 text-gray-800">${feature.title}</h3>
                        <p class="text-gray-600">${feature.description}</p>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    // Add click handlers for feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('click', (e) => {
            const feature = card.dataset.feature;
            if (!localStorage.getItem('token') && feature !== 'search') {
                showError('Please login to use this feature');
                history.pushState(null, '', '/login');
                handleNavigation();
                return;
            }
            history.pushState(null, '', `/${feature}`);
            handleNavigation();
        });
    });
}

export async function loadHomeContent() {
    const container = document.createElement('div');
    container.id = 'homeContainer';
    container.innerHTML = `
        <h1>Welcome to Clarity</h1>
        <div id="menu"></div>
    `;
    document.getElementById('app').innerHTML = '';
    document.getElementById('app').appendChild(container);

    const menu = document.getElementById('menu');
    
    // Add menu items for each feature
    const menuItems = [
        { path: '/search', text: 'Search' },
        { path: '/youtube', text: 'YouTube' },
        { path: '/documents', text: 'Documents' },
        { path: '/photos', text: 'Photos' },
        { path: '/video-call', text: 'Video Call' },
        { path: '/news', text: 'News' },
        { path: '/deals', text: 'Deals' },
        { path: '/voice-memos', text: 'Voice Memos' }
    ];

    menuItems.forEach(item => {
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = item.text;
        link.onclick = (e) => {
            e.preventDefault();
            window.history.pushState({}, '', item.path);
            loadMainContent();
        };
        menu.appendChild(link);
    });

    // Add logout button
    const logoutButton = document.createElement('button');
    logoutButton.textContent = 'Logout';
    logoutButton.onclick = async () => {
        await auth.logout();
        window.history.pushState({}, '', '/login');
        loadMainContent();
    };
    menu.appendChild(logoutButton);

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        #homeContainer {
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        
        #menu {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        
        #menu a {
            color: #007bff;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        
        #menu a:hover {
            background-color: #f0f0f0;
        }
        
        #menu button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #dc3545;
            color: white;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        #menu button:hover {
            background-color: #c82333;
        }
    `;
    document.head.appendChild(style);
}
