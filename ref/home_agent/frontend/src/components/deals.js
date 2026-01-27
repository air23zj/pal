import { deals } from '../utils/deals-api';
import { showLoading, showError } from '../utils/ui';
import { loadMainContent } from '../main.js';

export function loadDealsInterface() {
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) return;

    mainContent.innerHTML = `
        <div class="max-w-6xl mx-auto px-4 py-6">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-gray-900">Deals & Discounts</h2>
                <button id="backButton" class="text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>Back to Home
                </button>
            </div>
            
            <div id="dealsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Deals will be dynamically inserted here -->
            </div>
            
            <div id="loadingIndicator" class="hidden">
                <div class="flex justify-center items-center py-8">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
            </div>
        </div>
    `;

    // Add event listeners
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    // Load deals
    loadDeals();
}

async function loadDeals() {
    const dealsGrid = document.getElementById('dealsGrid');
    const loadingIndicator = document.getElementById('loadingIndicator');

    try {
        loadingIndicator.classList.remove('hidden');
        const dealsData = await deals.getRecommendations();
        
        if (dealsData.length === 0) {
            dealsGrid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <p class="text-gray-500">No deals available at the moment. Please try again later.</p>
                </div>
            `;
            return;
        }
        
        dealsGrid.innerHTML = dealsData.map(deal => {
            const safeUrl = deal.url ? encodeURI(deal.url) : '#';
            const safeTitle = deal.title ? deal.title.replace(/"/g, '&quot;') : 'Unknown Product';
            const safeSummary = deal.summary ? deal.summary.replace(/"/g, '&quot;') : 'No description available';
            
            return `
                <div class="deal-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                    <div class="aspect-w-16 aspect-h-9">
                        <img src="${deal.image_url}" alt="${safeTitle}" 
                             class="object-cover w-full h-48"
                             onerror="this.onerror=null; this.src='https://via.placeholder.com/400x300?text=No+Image';">
                    </div>
                    <div class="p-4">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">${safeTitle}</h3>
                        <p class="text-2xl font-bold text-primary-600 mb-2">${deal.price}</p>
                        <div class="text-gray-600 text-sm mb-4">
                            <p class="description">${safeSummary}</p>
                            <div class="summary mt-2 hidden">
                                <hr class="my-2">
                                <p class="text-sm italic"></p>
                            </div>
                        </div>
                        <div class="flex justify-between items-center mt-4">
                            <a href="${safeUrl}" 
                               target="_blank" 
                               rel="noopener noreferrer" 
                               class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
                                View Deal
                            </a>
                            <button class="summarize-btn text-primary-600 hover:text-primary-700 px-3 py-1 rounded-md hover:bg-primary-50 transition-colors"
                                    onclick="summarizeDeal(this, '${safeSummary}')">
                                <i class="fas fa-robot mr-1"></i>
                                Summarize
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading deals:', error);
        dealsGrid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-red-500">Failed to load deals</p>
                <p class="text-gray-500 text-sm mt-2">${error.message}</p>
            </div>
        `;
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

// Add summarize functionality
window.summarizeDeal = async (button, description) => {
    const card = button.closest('.deal-card');
    const summaryDiv = card.querySelector('.summary');
    const descriptionDiv = card.querySelector('.description');
    
    // If summary is already shown, just toggle visibility
    if (!summaryDiv.classList.contains('hidden')) {
        summaryDiv.classList.add('hidden');
        button.innerHTML = '<i class="fas fa-robot mr-1"></i> Summarize';
        return;
    }
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Generating...';
        const response = await deals.summarizeDeal(description);
        
        if (response && response.summary) {
            summaryDiv.querySelector('p').textContent = response.summary;
            summaryDiv.classList.remove('hidden');
            button.innerHTML = '<i class="fas fa-chevron-up mr-1"></i> Hide Summary';
        } else {
            throw new Error('Invalid summary response');
        }
    } catch (error) {
        console.error('Error generating summary:', error);
        showError('Failed to generate summary');
        button.innerHTML = '<i class="fas fa-robot mr-1"></i> Summarize';
    }
}; 