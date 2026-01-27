import { news } from '../utils/news-api';
import { loadMainContent } from '../main.js';
import { showLoading, showError } from '../utils/ui';

const PAGE_SIZE = 12; // Number of news items per page
let currentPage = 1;
let isLoading = false;
let hasMoreItems = true;

export function loadNewsInterface() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold">News Feed</h2>
                <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>
                    Back to Home
                </button>
            </div>
            <div id="newsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- News items will be populated here -->
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
            <div id="loadMoreContainer" class="flex justify-center mt-8 mb-8 hidden">
                <button id="loadMoreButton" class="bg-primary-600 text-white px-6 py-2 rounded-md hover:bg-primary-700">
                    Load More
                </button>
            </div>
        </div>
    `;

    // Add back button functionality
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    // Add scroll listener for infinite scroll
    window.addEventListener('scroll', handleScroll);

    // Add load more button functionality
    const loadMoreButton = document.getElementById('loadMoreButton');
    loadMoreButton.addEventListener('click', () => {
        if (!isLoading && hasMoreItems) {
            loadNews();
        }
    });

    // Reset state and load initial news
    currentPage = 1;
    hasMoreItems = true;
    loadNews();
}

function handleScroll() {
    const scrollPosition = window.innerHeight + window.scrollY;
    const bodyHeight = document.body.offsetHeight;
    const scrollThreshold = bodyHeight - 1000; // Load more when 1000px from bottom

    if (scrollPosition > scrollThreshold && !isLoading && hasMoreItems) {
        loadNews();
    }
}

async function loadNews() {
    if (isLoading) return;
    
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorContainer = document.getElementById('errorContainer');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    
    try {
        isLoading = true;
        loadingIndicator.classList.remove('hidden');
        errorContainer.classList.add('hidden');

        const newsData = await news.getRecommendations(currentPage, PAGE_SIZE);
        
        if (!Array.isArray(newsData)) {
            throw new Error('Invalid response format from server');
        }
        
        if (newsData.length < PAGE_SIZE) {
            hasMoreItems = false;
            loadMoreContainer.classList.add('hidden');
        } else {
            loadMoreContainer.classList.remove('hidden');
        }

        if (currentPage === 1) {
            displayNews(newsData);
        } else {
            appendNews(newsData);
        }
        
        currentPage++;
    } catch (error) {
        console.error('News loading error:', error);
        errorContainer.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = 
            error.response?.data?.detail || error.message || 'Failed to load news. Please try again.';
    } finally {
        isLoading = false;
        loadingIndicator.classList.add('hidden');
    }
}

function createNewsCard(item) {
    // Skip items with invalid or removed content
    if (!item.title || item.title.includes('[Removed]') || !item.url) {
        return '';
    }

    return `
        <div class="bg-white rounded-lg shadow-sm overflow-hidden">
            <div class="aspect-w-16 aspect-h-9 relative">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E"
                    data-src="${item.image_url || '/placeholder-news.jpg'}" 
                    alt="${item.title}"
                    class="w-full h-48 object-cover lazy-image"
                    loading="lazy"
                    onerror="this.onerror=null; this.src='/placeholder-news.jpg';">
                <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            </div>
            <div class="p-4">
                <h3 class="font-semibold text-lg mb-2 line-clamp-2">${item.title}</h3>
                <div class="flex justify-between items-center mt-4">
                    <button class="text-primary-600 hover:text-primary-700 text-sm font-medium"
                            onclick="window.open('${item.url}', '_blank')">
                        Read More
                    </button>
                    <button class="text-gray-600 hover:text-gray-700 text-sm font-medium summary-button"
                            data-article-id="${item.id}">
                        Show Summary
                    </button>
                </div>
                <div class="summary-content hidden mt-4 text-sm text-gray-600" id="summary-${item.id}">
                    ${item.summary && !item.summary.includes('[Removed]') ? item.summary : 'Summary not available'}
                </div>
            </div>
        </div>
    `;
}

function displayNews(newsItems) {
    const newsGrid = document.getElementById('newsGrid');
    // Filter out invalid items and join valid ones
    newsGrid.innerHTML = newsItems
        .map(createNewsCard)
        .filter(card => card !== '')  // Remove empty strings (invalid items)
        .join('');
    initializeLazyLoading();
    addSummaryHandlers();
}

function appendNews(newsItems) {
    const newsGrid = document.getElementById('newsGrid');
    const fragment = document.createDocumentFragment();
    const tempContainer = document.createElement('div');
    
    // Filter out invalid items and join valid ones
    tempContainer.innerHTML = newsItems
        .map(createNewsCard)
        .filter(card => card !== '')  // Remove empty strings (invalid items)
        .join('');
    
    while (tempContainer.firstChild) {
        fragment.appendChild(tempContainer.firstChild);
    }
    
    newsGrid.appendChild(fragment);
    initializeLazyLoading();
    addSummaryHandlers();
}

function initializeLazyLoading() {
    const lazyImages = document.querySelectorAll('.lazy-image');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy-image');
                observer.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => imageObserver.observe(img));
}

function addSummaryHandlers() {
    document.querySelectorAll('.summary-button').forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.getAttribute('data-article-id');
            const summaryDiv = document.getElementById(`summary-${articleId}`);
            const isHidden = summaryDiv.classList.contains('hidden');
            
            summaryDiv.classList.toggle('hidden');
            this.textContent = isHidden ? 'Hide Summary' : 'Show Summary';
        });
    });
}

// Cleanup function to remove scroll listener when component unmounts
export function cleanupNewsInterface() {
    window.removeEventListener('scroll', handleScroll);
} 