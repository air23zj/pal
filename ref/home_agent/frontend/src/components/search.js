import { marked } from 'marked';
import { search } from '../utils/search-api';
import { loadMainContent } from '../main.js';
import { showLoading, showError } from '../utils/ui';

export function loadSearchInterface() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-3xl mx-auto">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold">AI-Powered Search</h2>
                <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>
                    Back to Home
                </button>
            </div>
            <div class="mb-8">
                <input type="text" id="searchInput" 
                    class="w-full px-4 py-3 rounded-lg border focus:ring-2 focus:ring-primary-500 focus:border-primary-500" 
                    placeholder="Ask me anything...">
                <button id="searchButton" 
                    class="mt-4 w-full bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors">
                    Search
                </button>
            </div>
            <div id="resultsContainer" class="hidden space-y-8">
                <div class="prose bg-white p-6 rounded-lg shadow-sm max-w-none"></div>
                <div class="mt-4">
                    <h3 class="text-lg font-semibold mb-4">Sources</h3>
                    <div id="sourcesContainer" class="space-y-4"></div>
                </div>
                <div class="mt-4">
                    <h3 class="text-lg font-semibold mb-4">Related Questions</h3>
                    <div id="relatedContainer" class="space-y-2"></div>
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

    // Add event listeners
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const backButton = document.getElementById('backButton');

    searchButton.addEventListener('click', () => performSearch(searchInput.value));
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });

    // Add back button functionality
    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });
}

async function performSearch(query) {
    if (!query.trim()) {
        showError('Please enter a search query');
        return;
    }

    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorContainer = document.getElementById('errorContainer');
    const resultsContainer = document.getElementById('resultsContainer');
    
    try {
        loadingIndicator.classList.remove('hidden');
        errorContainer.classList.add('hidden');
        resultsContainer.classList.add('hidden');

        console.log('Performing search:', query);
        const response = await search.search(query);
        const result = response.data;
        console.log('Search result:', result);
        
        if (!result || (!result.answer && !result.sources)) {
            throw new Error('Invalid response from server');
        }

        displayResults(result.answer, result.sources, result.related_questions);
    } catch (error) {
        console.error('Search error:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        errorContainer.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = 
            error.response?.data?.detail || error.message || 'Failed to perform search. Please try again.';
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

function displayResults(answer, sources, relatedQuestions) {
    const resultsContainer = document.getElementById('resultsContainer');
    const sourcesContainer = document.getElementById('sourcesContainer');
    const relatedContainer = document.getElementById('relatedContainer');
    
    // Process answer text to add clickable citations
    let processedAnswer = answer;
    sources.forEach((source, index) => {
        const citationNumber = index + 1;
        // Handle both citation formats: [Citation: 1] and [1]
        const citationRegexes = [
            new RegExp(`\\[Citation: ${citationNumber}\\]`, 'g'),
            new RegExp(`\\[${citationNumber}\\]`, 'g')
        ];
        citationRegexes.forEach(regex => {
            processedAnswer = processedAnswer.replace(
                regex,
                `<a href="javascript:void(0)" class="citation-link text-primary-600 hover:text-primary-700 hover:underline cursor-pointer" data-source-id="source-${citationNumber}">[${citationNumber}]</a>`
            );
        });
    });

    // Display processed answer with marked
    const markedAnswer = marked.parse(processedAnswer);
    resultsContainer.querySelector('.prose').innerHTML = markedAnswer;
    
    // Display sources with IDs for linking
    sourcesContainer.innerHTML = sources.map((source, index) => `
        <div id="source-${index + 1}" class="bg-white p-4 rounded-lg shadow-sm scroll-mt-8">
            <div class="flex justify-between items-start">
                <h4 class="font-medium text-primary-600">${source.title}</h4>
                <span class="text-sm text-gray-500">[${index + 1}]</span>
            </div>
            <p class="text-sm text-gray-600 mt-1">${source.snippet}</p>
            <a href="${source.url}" target="_blank" class="text-sm text-primary-500 hover:text-primary-600 hover:underline mt-2 inline-block">
                Read more →
            </a>
        </div>
    `).join('');
    
    // Display related questions
    if (relatedQuestions && relatedQuestions.length > 0) {
        // Clean up related questions by removing numbering
        const cleanedQuestions = relatedQuestions.map(question => 
            question.replace(/^\s*(?:\d+[\.\)\]]|\[\d+\])\s*/, '').trim()
        );

        relatedContainer.innerHTML = cleanedQuestions.map(question => `
            <button class="text-left w-full p-2 rounded hover:bg-gray-50 text-primary-600 hover:text-primary-700">
                ${question}
            </button>
        `).join('');
        
        // Add click handlers for related questions
        relatedContainer.querySelectorAll('button').forEach((button, index) => {
            button.addEventListener('click', () => {
                const searchInput = document.getElementById('searchInput');
                searchInput.value = cleanedQuestions[index];
                performSearch(cleanedQuestions[index]);
            });
        });
    }
    
    // Add click handlers for citation links
    resultsContainer.querySelectorAll('.citation-link').forEach(link => {
        link.onclick = function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-source-id');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
                // Add a brief highlight effect
                targetElement.classList.add('bg-primary-50');
                setTimeout(() => {
                    targetElement.classList.remove('bg-primary-50');
                }, 1000);
            }
        };
    });
    
    resultsContainer.classList.remove('hidden');
}
