import { photos } from '../utils/photos-api';
import { showLoading, showError, showSuccess } from '../utils/ui';
import { loadMainContent } from '../main';

export function loadPhotosInterface() {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-3xl font-bold text-gray-900">Photo Gallery</h1>
                <div class="flex items-center space-x-4">
                    <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                        <i class="fas fa-arrow-left mr-2"></i>
                        Back to Home
                    </button>
                    <button id="uploadPhotoBtn" class="bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 px-4 rounded">
                        Upload Photos
                    </button>
                </div>
            </div>
            
            <!-- Upload Modal -->
            <div id="uploadModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-40">
                <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 w-full max-w-md">
                    <h3 class="text-lg font-semibold mb-4">Upload Photos</h3>
                    <div id="dropZone" class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 transition-colors">
                        <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
                        <p class="text-gray-600">Drag and drop photos here or click to select</p>
                        <input type="file" id="photoInput" class="hidden" accept="image/*" multiple>
                    </div>
                    <div id="uploadPreview" class="hidden mt-4">
                        <div id="selectedPhotos" class="grid grid-cols-3 gap-2 mb-4">
                            <!-- Selected photos preview -->
                        </div>
                    </div>
                    <div class="flex justify-end space-x-4 mt-6">
                        <button id="cancelUploadBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
                        <button id="uploadBtn" class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md">Upload</button>
                    </div>
                </div>
            </div>

            <!-- Photo Grid -->
            <div id="photoGrid" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <!-- Photos will be loaded here -->
            </div>

            <!-- Photo Preview Modal -->
            <div id="previewModal" class="fixed inset-0 bg-black bg-opacity-90 hidden z-50">
                <div class="absolute inset-0 flex items-center justify-center">
                    <button id="prevPhotoBtn" class="absolute left-4 text-white text-4xl hover:text-primary-400">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <img id="previewImage" src="" alt="" class="max-h-[90vh] max-w-[90vw] object-contain">
                    <button id="nextPhotoBtn" class="absolute right-4 text-white text-4xl hover:text-primary-400">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <button id="closePreviewBtn" class="absolute top-4 right-4 text-white text-2xl hover:text-primary-400">
                        <i class="fas fa-times"></i>
                    </button>
                    <div class="absolute top-4 right-16 flex space-x-4">
                        <button id="generateTitleBtn" class="text-white text-2xl hover:text-primary-400" title="Generate AI Title">
                            <i class="fas fa-robot"></i>
                        </button>
                        <button id="deletePhotoBtn" class="text-white text-2xl hover:text-red-400" title="Delete Photo">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    <div class="absolute bottom-4 left-0 right-0 text-white text-center bg-black bg-opacity-50 py-2">
                        <p id="photoInfo" class="text-sm"></p>
                        <p id="generatedTitle" class="text-sm italic mt-1 hidden"></p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Initialize event listeners
    initializeEventListeners();
    // Load initial photos
    loadPhotos();
}

function initializeEventListeners() {
    const uploadPhotoBtn = document.getElementById('uploadPhotoBtn');
    const uploadModal = document.getElementById('uploadModal');
    const dropZone = document.getElementById('dropZone');
    const photoInput = document.getElementById('photoInput');
    const cancelUploadBtn = document.getElementById('cancelUploadBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const backButton = document.getElementById('backButton');

    // Back button handler
    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    // Upload handlers
    uploadPhotoBtn.addEventListener('click', () => {
        uploadModal.classList.remove('hidden');
        resetUpload();
    });

    cancelUploadBtn.addEventListener('click', () => {
        uploadModal.classList.add('hidden');
        resetUpload();
    });

    dropZone.addEventListener('click', () => photoInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-primary-500');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-primary-500');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary-500');
        handlePhotoSelect(e.dataTransfer.files);
    });

    photoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handlePhotoSelect(e.target.files);
        }
    });

    uploadBtn.addEventListener('click', handlePhotoUpload);

    // Preview handlers
    const previewModal = document.getElementById('previewModal');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    const prevPhotoBtn = document.getElementById('prevPhotoBtn');
    const nextPhotoBtn = document.getElementById('nextPhotoBtn');
    const deletePhotoBtn = document.getElementById('deletePhotoBtn');
    const generateTitleBtn = document.getElementById('generateTitleBtn');

    closePreviewBtn.addEventListener('click', () => {
        previewModal.classList.add('hidden');
    });

    prevPhotoBtn.addEventListener('click', showPreviousPhoto);
    nextPhotoBtn.addEventListener('click', showNextPhoto);

    deletePhotoBtn.addEventListener('click', async () => {
        if (confirm('Are you sure you want to delete this photo?')) {
            await handlePhotoDelete();
        }
    });

    generateTitleBtn.addEventListener('click', async () => {
        await handleTitleGeneration();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (previewModal.classList.contains('hidden')) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                showPreviousPhoto();
                break;
            case 'ArrowRight':
                showNextPhoto();
                break;
            case 'Escape':
                previewModal.classList.add('hidden');
                break;
        }
    });
}

function handlePhotoSelect(files) {
    const selectedPhotos = document.getElementById('selectedPhotos');
    const uploadPreview = document.getElementById('uploadPreview');
    
    selectedPhotos.innerHTML = '';
    Array.from(files).forEach((file, index) => {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                selectedPhotos.innerHTML += `
                    <div class="relative">
                        <img src="${e.target.result}" alt="Preview" class="w-full h-24 object-cover rounded">
                        <button onclick="removeSelectedPhoto(${index})" class="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center">
                            <i class="fas fa-times text-xs"></i>
                        </button>
                    </div>
                `;
            };
            reader.readAsDataURL(file);
        }
    });
    
    uploadPreview.classList.remove('hidden');
}

function resetUpload() {
    const photoInput = document.getElementById('photoInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const selectedPhotos = document.getElementById('selectedPhotos');
    
    photoInput.value = '';
    uploadPreview.classList.add('hidden');
    selectedPhotos.innerHTML = '';
}

async function handlePhotoUpload() {
    const files = document.getElementById('photoInput').files;
    if (files.length === 0) {
        showError('Please select photos to upload');
        return;
    }

    showLoading(true);
    try {
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            await photos.upload(formData);
        }
        
        showSuccess('Photos uploaded successfully');
        document.getElementById('uploadModal').classList.add('hidden');
        resetUpload();
        await loadPhotos();
    } catch (error) {
        console.error('Photo upload error:', error);
        showError('Failed to upload photos: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
}

async function loadPhotos() {
    showLoading(true);
    try {
        const photosList = await photos.list();
        const photoGrid = document.getElementById('photoGrid');
        
        if (!photosList || photosList.length === 0) {
            photoGrid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <p class="text-gray-500">No photos yet. Click "Upload Photos" to add some.</p>
                </div>
            `;
            return;
        }

        // First, create the grid with loading placeholders
        photoGrid.innerHTML = photosList.map((photo, index) => `
            <div class="group relative cursor-pointer aspect-square" onclick="showPhotoPreview(${index})">
                <div class="w-full h-full overflow-hidden rounded-lg">
                    <img src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><path d='M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2z'/><circle cx='8.5' cy='8.5' r='1.5'/><path d='m21 15-5-5L5 21'/></svg>" 
                         alt="${photo.name}"
                         data-photo-id="${photo.id}"
                         class="w-full h-full object-cover transform transition-transform group-hover:scale-105">
                </div>
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity">
                    <div class="absolute bottom-0 left-0 right-0 p-2 text-white transform translate-y-full group-hover:translate-y-0 transition-transform">
                        <p class="text-sm font-medium truncate">${photo.name}</p>
                    </div>
                </div>
            </div>
        `).join('');

        // Then load each image with authentication
        const images = photoGrid.querySelectorAll('img[data-photo-id]');
        for (const img of images) {
            try {
                const photoId = img.dataset.photoId;
                const imageUrl = await photos.getContent(photoId);
                img.src = imageUrl;
            } catch (error) {
                console.error('Error loading image:', error);
                // Keep the placeholder SVG if loading fails
            }
        }

        // Store photos list for preview navigation
        window.photosList = photosList;
    } catch (error) {
        console.error('Load photos error:', error);
        showError('Failed to load photos');
    } finally {
        showLoading(false);
    }
}

window.showPhotoPreview = async (index) => {
    const photo = window.photosList[index];
    const previewModal = document.getElementById('previewModal');
    const previewImage = document.getElementById('previewImage');
    const photoInfo = document.getElementById('photoInfo');
    const generatedTitle = document.getElementById('generatedTitle');

    try {
        const imageUrl = await photos.getContent(photo.id);
        previewImage.src = imageUrl;
        previewImage.alt = photo.name;
        
        // Display photo info
        photoInfo.textContent = `${photo.name} (${formatFileSize(photo.size)})`;
        generatedTitle.classList.add('hidden');

        previewModal.classList.remove('hidden');
        window.currentPhotoIndex = index;
    } catch (error) {
        console.error('Error loading preview:', error);
        showError('Failed to load photo preview');
    }
};

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showPreviousPhoto() {
    if (window.currentPhotoIndex > 0) {
        showPhotoPreview(window.currentPhotoIndex - 1);
    }
}

function showNextPhoto() {
    if (window.currentPhotoIndex < window.photosList.length - 1) {
        showPhotoPreview(window.currentPhotoIndex + 1);
    }
}

window.removeSelectedPhoto = (index) => {
    const photoInput = document.getElementById('photoInput');
    const dt = new DataTransfer();
    
    Array.from(photoInput.files).forEach((file, i) => {
        if (i !== index) dt.items.add(file);
    });
    
    photoInput.files = dt.files;
    handlePhotoSelect(photoInput.files);
};

async function handlePhotoDelete() {
    const photo = window.photosList[window.currentPhotoIndex];
    showLoading(true);
    try {
        await photos.delete(photo.id);
        showSuccess('Photo deleted successfully');
        document.getElementById('previewModal').classList.add('hidden');
        await loadPhotos(); // Refresh the photos list
    } catch (error) {
        console.error('Delete photo error:', error);
        showError('Failed to delete photo: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
}

async function handleTitleGeneration() {
    const photo = window.photosList[window.currentPhotoIndex];
    const generatedTitle = document.getElementById('generatedTitle');
    showLoading(true);
    try {
        const result = await photos.generateSubtitle(photo.id);
        generatedTitle.textContent = result.subtitle;
        generatedTitle.classList.remove('hidden');
    } catch (error) {
        console.error('Generate title error:', error);
        showError('Failed to generate title: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
} 