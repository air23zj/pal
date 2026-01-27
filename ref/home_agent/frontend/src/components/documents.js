import { documents } from '../utils/document-api';
import { showLoading, showError, showSuccess, formatDate } from '../utils/ui';
import { loadLoginForm } from './auth';
import { loadMainContent } from '../main.js';

export function loadDocumentsInterface() {
    // Check authentication first
    const token = localStorage.getItem('token');
    console.log('Current auth token:', token);
    
    if (!token) {
        console.log('No auth token found, redirecting to login...');
        history.pushState(null, '', '/login');
        loadLoginForm();
        return;
    }

    console.log('Initializing documents interface...');
    const documentsContent = document.getElementById('mainContent');
    if (!documentsContent) {
        console.error('documentsContent element not found');
        return;
    }
    documentsContent.innerHTML = `
        <div class="max-w-6xl mx-auto">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center justify-between w-full">
                    <h2 class="text-2xl font-bold text-gray-900">My Documents</h2>
                    <div class="flex items-center gap-4">
                        <button id="backButton" class="flex items-center text-gray-600 hover:text-gray-800">
                            <i class="fas fa-arrow-left mr-2"></i>
                            Back to Home
                        </button>
                        <button id="newDocumentBtn" class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
                            New Document
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="documentsGrid">
                <!-- Documents will be inserted here -->
            </div>

            <!-- File Upload Section -->
            <div class="mt-8 bg-white rounded-lg shadow-sm p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-semibold">Shared Files</h3>
                    <button id="uploadFileBtn" class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
                        Upload File
                    </button>
                </div>
                <div id="filesGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Files will be inserted here -->
                </div>
            </div>

            <!-- File Upload Modal -->
            <div id="fileModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <div class="bg-white rounded-lg p-6 w-full max-w-md">
                    <h3 class="text-xl font-semibold mb-4">Upload File</h3>
                    <div class="mb-4">
                        <input type="file" id="fileInput" class="hidden">
                        <div id="dropZone" class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500">
                            <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-2"></i>
                            <p class="text-gray-600">Drag and drop a file here, or click to select</p>
                            <p class="text-sm text-gray-500 mt-1">Maximum file size: 10MB</p>
                        </div>
                        <div id="filePreview" class="hidden mt-4">
                            <div class="flex items-center justify-between bg-gray-50 p-3 rounded">
                                <div class="flex items-center">
                                    <i class="fas fa-file text-gray-400 mr-2"></i>
                                    <span id="fileName" class="text-sm text-gray-600"></span>
                                </div>
                                <button id="removeFileBtn" class="text-red-500 hover:text-red-600">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end gap-4">
                        <button id="cancelFileBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">
                            Cancel
                        </button>
                        <button id="uploadBtn" class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
                            Upload
                        </button>
                    </div>
                </div>
            </div>

            <!-- New/Edit Document Modal -->
            <div id="documentModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <div class="bg-white rounded-lg p-6 w-full max-w-2xl">
                    <h3 class="text-xl font-semibold mb-4" id="modalTitle">New Document</h3>
                    <input type="text" id="documentTitle" placeholder="Document Title" 
                        class="w-full px-4 py-2 rounded-lg border mb-4">
                    <textarea id="documentContent" rows="10" placeholder="Document Content" 
                        class="w-full px-4 py-2 rounded-lg border mb-4"></textarea>
                    <div class="flex justify-end gap-4">
                        <button id="cancelDocumentBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">
                            Cancel
                        </button>
                        <button id="saveDocumentBtn" class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
                            Save
                        </button>
                    </div>
                </div>
            </div>

            <!-- Share Document Modal -->
            <div id="shareModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <div class="bg-white rounded-lg p-6 w-full max-w-md">
                    <h3 class="text-xl font-semibold mb-4">Share Document</h3>
                    <input type="text" id="shareUsername" placeholder="Enter username" 
                        class="w-full px-4 py-2 rounded-lg border mb-4">
                    <div class="flex justify-end gap-4">
                        <button id="cancelShareBtn" class="px-4 py-2 text-gray-600 hover:text-gray-800">
                            Cancel
                        </button>
                        <button id="confirmShareBtn" class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700">
                            Share
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add event listeners
    const newDocumentBtn = document.getElementById('newDocumentBtn');
    const documentModal = document.getElementById('documentModal');
    const cancelDocumentBtn = document.getElementById('cancelDocumentBtn');
    const saveDocumentBtn = document.getElementById('saveDocumentBtn');
    const shareModal = document.getElementById('shareModal');
    const cancelShareBtn = document.getElementById('cancelShareBtn');
    const confirmShareBtn = document.getElementById('confirmShareBtn');
    const backButton = document.getElementById('backButton');

    // File Upload Event Listeners
    const uploadFileBtn = document.getElementById('uploadFileBtn');
    const fileModal = document.getElementById('fileModal');
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const cancelFileBtn = document.getElementById('cancelFileBtn');
    const uploadBtn = document.getElementById('uploadBtn');

    // File Upload Handlers
    uploadFileBtn.addEventListener('click', () => {
        fileModal.classList.remove('hidden');
        resetFileUpload();
    });

    cancelFileBtn.addEventListener('click', () => {
        fileModal.classList.add('hidden');
        resetFileUpload();
    });

    dropZone.addEventListener('click', () => fileInput.click());

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
        handleFileSelect(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    removeFileBtn.addEventListener('click', resetFileUpload);

    uploadBtn.addEventListener('click', handleFileUpload);

    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    newDocumentBtn.addEventListener('click', () => {
        document.getElementById('modalTitle').textContent = 'New Document';
        document.getElementById('documentTitle').value = '';
        document.getElementById('documentContent').value = '';
        saveDocumentBtn.onclick = handleSaveDocument;
        documentModal.classList.remove('hidden');
    });

    cancelDocumentBtn.addEventListener('click', () => documentModal.classList.add('hidden'));
    cancelShareBtn.addEventListener('click', () => shareModal.classList.add('hidden'));

    // Load initial documents
    loadDocuments();
    
    // Load initial files
    loadFiles();
}

async function loadDocuments() {
    console.log('Loading documents...');
    showLoading(true);
    try {
        console.log('Making API request to list documents...');
        const documentsList = await documents.list();
        console.log('Documents received:', documentsList);
        displayDocuments(documentsList);
    } catch (error) {
        console.error('Load documents error:', error);
        console.error('Error details:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        
        if (error.response?.status === 401) {
            // Unauthorized - redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            history.pushState(null, '', '/login');
            loadLoginForm();
            showError('Please login to view your documents');
        } else {
            showError('Failed to load documents');
        }
    } finally {
        showLoading(false);
    }
}

function displayDocuments(documentsList) {
    console.log('Displaying documents:', documentsList);
    
    const grid = document.getElementById('documentsGrid');
    if (!grid) {
        console.error('Documents grid element not found');
        return;
    }

    if (!Array.isArray(documentsList)) {
        console.error('Invalid documents list:', documentsList);
        grid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">Error loading documents. Please try again.</p>
            </div>
        `;
        return;
    }

    if (documentsList.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">No documents yet. Click "New Document" to create one.</p>
            </div>
        `;
        return;
    }

    const currentUserId = parseInt(localStorage.getItem('userId'));

    try {
        grid.innerHTML = documentsList.map(doc => {
            const isShared = doc.owner_id !== currentUserId;
            return `
                <div class="bg-white rounded-lg shadow-sm p-6 ${isShared ? 'border-l-4 border-primary-500' : ''}">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="font-semibold text-lg text-gray-900 cursor-pointer hover:text-primary-600" 
                                onclick="window.previewDocument(${doc.id})">${doc.title || 'Untitled'}</h3>
                            ${isShared ? '<span class="text-xs text-primary-600 ml-2">Shared with you</span>' : ''}
                        </div>
                        <div class="flex gap-2">
                            ${!isShared ? `
                                <button onclick="window.editDocument(${doc.id})" class="text-gray-600 hover:text-primary-600">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button onclick="window.deleteDocument(${doc.id})" class="text-gray-600 hover:text-red-600">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    <p class="text-gray-600 text-sm mb-4 cursor-pointer hover:text-gray-900" 
                       onclick="window.previewDocument(${doc.id})">${doc.content ? doc.content.substring(0, 150) + (doc.content.length > 150 ? '...' : '') : 'No content'}</p>
                    <div class="flex justify-between items-center text-sm text-gray-500">
                        <span>Updated: ${formatDate(doc.updated_at)}</span>
                        <div class="flex gap-2">
                            <button onclick="window.summarizeDocument(${doc.id})" class="text-primary-600 hover:text-primary-700">
                                <i class="fas fa-robot"></i> Summarize
                            </button>
                            ${!isShared ? `
                                <button onclick="window.shareDocument(${doc.id})" class="text-primary-600 hover:text-primary-700">
                                    <i class="fas fa-share-alt"></i> Share
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Add preview modal to the page if it doesn't exist
        if (!document.getElementById('previewModal')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div id="previewModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                    <div class="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-xl font-semibold" id="previewTitle"></h3>
                            <button id="closePreviewBtn" class="text-gray-600 hover:text-gray-800">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div id="previewContent" class="prose max-w-none"></div>
                        <div id="summarizeResult" class="mt-4 p-4 bg-gray-50 rounded-lg hidden">
                            <h4 class="font-semibold mb-2">AI Summary</h4>
                            <div id="summaryContent"></div>
                        </div>
                    </div>
                </div>
            `);

            // Add event listener for closing preview
            document.getElementById('closePreviewBtn').addEventListener('click', () => {
                document.getElementById('previewModal').classList.add('hidden');
            });
        }
    } catch (error) {
        console.error('Error displaying documents:', error);
        grid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">Error displaying documents. Please try again.</p>
            </div>
        `;
    }
}

async function handleSaveDocument() {
    const titleInput = document.getElementById('documentTitle');
    const contentInput = document.getElementById('documentContent');
    const documentModal = document.getElementById('documentModal');
    
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();

    if (!title || !content) {
        showError('Please fill in both title and content');
        return;
    }

    showLoading(true);
    try {
        await documents.create({ title, content });
        showSuccess('Document created successfully');
        documentModal.classList.add('hidden');
        await loadDocuments(); // Refresh the documents list
    } catch (error) {
        console.error('Create document error:', error);
        showError('Failed to create document: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
}

// Export functions that need to be globally available
window.editDocument = async (id) => {
    // Prevent event bubbling
    event?.stopPropagation();
    
    showLoading(true);
    try {
        console.log('Fetching document for editing:', id);
        
        // Get the document directly from the list we already have
        const documentsList = await documents.list();
        console.log('Documents list:', documentsList);
        
        const docToEdit = documentsList.find(doc => doc.id === id);
        if (!docToEdit) {
            console.error('Document not found in list:', id);
            showError('Document not found');
            return;
        }
        
        console.log('Found document:', docToEdit);

        // Update modal with document data
        const modalTitle = document.getElementById('modalTitle');
        const titleInput = document.getElementById('documentTitle');
        const contentInput = document.getElementById('documentContent');
        const saveBtn = document.getElementById('saveDocumentBtn');
        const documentModal = document.getElementById('documentModal');

        modalTitle.textContent = 'Edit Document';
        titleInput.value = docToEdit.title || '';
        contentInput.value = docToEdit.content || '';
        saveBtn.dataset.documentId = id;
        
        // Update the save handler
        saveBtn.onclick = async () => {
            const updatedTitle = titleInput.value.trim();
            const updatedContent = contentInput.value.trim();
            
            if (!updatedTitle || !updatedContent) {
                showError('Please fill in both title and content');
                return;
            }
            
            showLoading(true);
            try {
                await documents.update(id, {
                    title: updatedTitle,
                    content: updatedContent
                });
                showSuccess('Document updated successfully');
                documentModal.classList.add('hidden');
                await loadDocuments(); // Refresh the documents list
            } catch (error) {
                console.error('Update error:', error);
                showError('Failed to update document: ' + (error.response?.data?.detail || error.message));
            } finally {
                showLoading(false);
            }
        };
        
        // Show the modal
        documentModal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Edit document error:', error);
        console.error('Error details:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        showError('Failed to load document: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
};

window.deleteDocument = async (id) => {
    // Prevent event bubbling to parent elements
    event?.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
        return;
    }
    
    showLoading(true);
    try {
        console.log('Attempting to delete document:', id);
        await documents.delete(id);
        console.log('Document deleted successfully');
        showSuccess('Document deleted successfully');
        
        // Close preview modal if it's open
        const previewModal = document.getElementById('previewModal');
        if (!previewModal.classList.contains('hidden')) {
            previewModal.classList.add('hidden');
        }
        
        // Reload the documents list
        await loadDocuments();
    } catch (error) {
        console.error('Delete document error:', error);
        console.error('Error details:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        
        let errorMessage = 'Failed to delete document';
        if (error.response?.data?.detail) {
            errorMessage += `: ${error.response.data.detail}`;
        }
        showError(errorMessage);
    } finally {
        showLoading(false);
    }
};

window.shareDocument = async (id) => {
    // Prevent event bubbling
    event?.stopPropagation();
    
    const shareModal = document.getElementById('shareModal');
    const confirmShareBtn = document.getElementById('confirmShareBtn');
    const usernameInput = document.getElementById('shareUsername');
    
    if (!shareModal || !confirmShareBtn || !usernameInput) {
        console.error('Share modal elements not found');
        showError('Error initializing share dialog');
        return;
    }
    
    // Reset the input and show modal
    usernameInput.value = '';
    shareModal.classList.remove('hidden');
    
    // Remove any existing click handlers
    confirmShareBtn.onclick = null;
    
    // Add new click handler
    confirmShareBtn.onclick = async () => {
        const username = usernameInput.value.trim();
        if (!username) {
            showError('Please enter a username');
            return;
        }
        
        showLoading(true);
        try {
            console.log('Sharing document:', id, 'with user:', username);
            const response = await documents.share(id, { username });
            console.log('Share response:', response);
            
            showSuccess('Document shared successfully');
            shareModal.classList.add('hidden');
            
            // Refresh the documents list to update any UI changes
            await loadDocuments();
        } catch (error) {
            console.error('Share error:', error);
            console.error('Error details:', {
                message: error.message,
                response: error.response?.data,
                status: error.response?.status
            });
            
            let errorMessage = 'Failed to share document';
            if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message;
            }
            showError(errorMessage);
        } finally {
            showLoading(false);
        }
    };
};

// Add preview functionality
window.previewDocument = async (id) => {
    try {
        console.log('Previewing document:', id);
        
        // Get the document from the list
        const documentsList = await documents.list();
        const docToPreview = documentsList.find(doc => doc.id === id);
        if (!docToPreview) {
            console.error('Document not found:', id);
            showError('Document not found');
            return;
        }
        
        // Ensure the preview modal exists
        let previewModal = document.getElementById('previewModal');
        if (!previewModal) {
            console.log('Creating preview modal...');
            document.body.insertAdjacentHTML('beforeend', `
                <div id="previewModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                    <div class="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-xl font-semibold" id="previewTitle"></h3>
                            <button id="closePreviewBtn" class="text-gray-600 hover:text-gray-800">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div id="previewContent" class="prose max-w-none"></div>
                        <div id="summarizeResult" class="mt-4 p-4 bg-gray-50 rounded-lg hidden">
                            <h4 class="font-semibold mb-2">AI Summary</h4>
                            <div id="summaryContent"></div>
                        </div>
                    </div>
                </div>
            `);
            
            // Add event listener for closing preview
            document.getElementById('closePreviewBtn').addEventListener('click', () => {
                document.getElementById('previewModal').classList.add('hidden');
            });
            
            previewModal = document.getElementById('previewModal');
        }

        // Update modal content
        const previewTitle = document.getElementById('previewTitle');
        const previewContent = document.getElementById('previewContent');
        const summarizeResult = document.getElementById('summarizeResult');

        if (!previewTitle || !previewContent || !summarizeResult) {
            console.error('Preview modal elements not found');
            showError('Error displaying preview');
            return;
        }

        previewTitle.textContent = docToPreview.title || 'Untitled';
        previewContent.innerHTML = docToPreview.content || 'No content';
        summarizeResult.classList.add('hidden');
        
        // Show the modal
        previewModal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Preview error:', error);
        showError('Failed to load document: ' + (error.response?.data?.detail || error.message));
    }
};

// Add summarize functionality
window.summarizeDocument = async (id) => {
    const summarizeResult = document.getElementById('summarizeResult');
    const summaryContent = document.getElementById('summaryContent');
    
    // If the preview modal isn't open, open it first
    const previewModal = document.getElementById('previewModal');
    if (previewModal.classList.contains('hidden')) {
        await window.previewDocument(id);
    }
    
    // Show loading state in the summary section
    summarizeResult.classList.remove('hidden');
    summaryContent.innerHTML = `
        <div class="flex items-center justify-center py-4">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            <span class="ml-2 text-gray-600">Generating summary...</span>
        </div>
    `;
    
    try {
        console.log('Requesting summary for document:', id);
        const response = await documents.summarize(id);
        console.log('Summary received:', response);
        
        if (response && response.summary) {
            summaryContent.innerHTML = `
                <div class="prose">
                    ${response.summary}
                </div>
            `;
        } else {
            throw new Error('Invalid summary response');
        }
    } catch (error) {
        console.error('Summarize error:', error);
        summaryContent.innerHTML = `
            <div class="text-red-500">
                <p>Failed to generate summary: ${error.response?.data?.detail || error.message}</p>
                <button onclick="window.summarizeDocument(${id})" class="mt-2 text-primary-600 hover:text-primary-700">
                    Try Again
                </button>
            </div>
        `;
    }
};

// File Upload Functions
function handleFileSelect(file) {
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showError('File size exceeds 10MB limit');
        return;
    }

    fileName.textContent = file.name;
    filePreview.classList.remove('hidden');
    dropZone.classList.add('hidden');
    fileInput.files = new DataTransfer().files;
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
}

function resetFileUpload() {
    fileInput.value = '';
    filePreview.classList.add('hidden');
    dropZone.classList.remove('hidden');
    fileName.textContent = '';
}

async function handleFileUpload() {
    const file = fileInput.files[0];
    if (!file) {
        showError('Please select a file to upload');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showLoading(true);
    try {
        const response = await documents.uploadFile(formData);
        showSuccess('File uploaded successfully');
        fileModal.classList.add('hidden');
        resetFileUpload();
        await loadFiles(); // Refresh the files list
    } catch (error) {
        console.error('File upload error:', error);
        showError('Failed to upload file: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
}

async function loadFiles() {
    showLoading(true);
    try {
        const filesList = await documents.listFiles();
        displayFiles(filesList);
    } catch (error) {
        console.error('Load files error:', error);
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            history.pushState(null, '', '/login');
            loadLoginForm();
            showError('Please login to view your files');
        } else {
            showError('Failed to load files');
        }
    } finally {
        showLoading(false);
    }
}

function displayFiles(filesList) {
    const filesGrid = document.getElementById('filesGrid');
    
    if (!Array.isArray(filesList)) {
        filesGrid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">Error loading files. Please try again.</p>
            </div>
        `;
        return;
    }

    if (filesList.length === 0) {
        filesGrid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">No files uploaded yet. Click "Upload File" to share a file.</p>
            </div>
        `;
        return;
    }

    const currentUserId = parseInt(localStorage.getItem('userId'));

    filesGrid.innerHTML = filesList.map(file => {
        const isOwner = file.owner_id === currentUserId;
        const fileIcon = getFileIcon(file.name);
        return `
            <div class="bg-white rounded-lg shadow-sm p-4 ${isOwner ? '' : 'border-l-4 border-primary-500'}">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex items-center">
                        <i class="${fileIcon} text-2xl text-gray-400 mr-3"></i>
                        <div>
                            <h4 class="font-medium text-gray-900">${file.name}</h4>
                            <p class="text-sm text-gray-500">${formatFileSize(file.size)}</p>
                        </div>
                    </div>
                    ${isOwner ? `
                        <button onclick="window.deleteFile(${file.id})" class="text-gray-600 hover:text-red-600">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
                <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-500">Uploaded: ${formatDate(file.created_at)}</span>
                    <div class="flex gap-2">
                        <button onclick="window.downloadFile(${file.id}, '${file.name}')" class="text-primary-600 hover:text-primary-700">
                            <i class="fas fa-download"></i> Download
                        </button>
                        ${isOwner ? `
                            <button onclick="window.shareFile(${file.id})" class="text-primary-600 hover:text-primary-700">
                                <i class="fas fa-share-alt"></i> Share
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function getFileIcon(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    const iconMap = {
        pdf: 'fas fa-file-pdf',
        doc: 'fas fa-file-word',
        docx: 'fas fa-file-word',
        xls: 'fas fa-file-excel',
        xlsx: 'fas fa-file-excel',
        ppt: 'fas fa-file-powerpoint',
        pptx: 'fas fa-file-powerpoint',
        jpg: 'fas fa-file-image',
        jpeg: 'fas fa-file-image',
        png: 'fas fa-file-image',
        gif: 'fas fa-file-image',
        zip: 'fas fa-file-archive',
        rar: 'fas fa-file-archive',
        txt: 'fas fa-file-alt',
    };
    return iconMap[extension] || 'fas fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Add file management functions to window object
window.deleteFile = async (id) => {
    event?.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
        return;
    }
    
    showLoading(true);
    try {
        await documents.deleteFile(id);
        showSuccess('File deleted successfully');
        await loadFiles();
    } catch (error) {
        console.error('Delete file error:', error);
        showError('Failed to delete file: ' + (error.response?.data?.detail || error.message));
    } finally {
        showLoading(false);
    }
};

window.shareFile = async (id) => {
    event?.stopPropagation();
    
    const shareModal = document.getElementById('shareModal');
    const confirmShareBtn = document.getElementById('confirmShareBtn');
    const usernameInput = document.getElementById('shareUsername');
    
    usernameInput.value = '';
    shareModal.classList.remove('hidden');
    
    confirmShareBtn.onclick = async () => {
        const username = usernameInput.value.trim();
        if (!username) {
            showError('Please enter a username');
            return;
        }
        
        showLoading(true);
        try {
            await documents.shareFile(id, { username });
            showSuccess('File shared successfully');
            shareModal.classList.add('hidden');
            await loadFiles();
        } catch (error) {
            console.error('Share file error:', error);
            showError('Failed to share file: ' + (error.response?.data?.detail || error.message));
        } finally {
            showLoading(false);
        }
    };
};

// Add download function to window object
window.downloadFile = async (id, fileName) => {
    showLoading(true);
    try {
        const token = localStorage.getItem('token');
        console.log('Attempting to download file:', id);
        console.log('Authorization token present:', !!token);
        
        const response = await fetch(`http://localhost:8000/files/${id}/download`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Download response error:', {
                status: response.status,
                statusText: response.statusText,
                error: errorText
            });
            throw new Error(`Failed to download file: ${response.status} ${response.statusText}`);
        }

        const contentType = response.headers.get('content-type');
        console.log('Response content type:', contentType);

        const blob = await response.blob();
        console.log('Blob size:', blob.size);
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showSuccess('File downloaded successfully');
    } catch (error) {
        console.error('Download file error:', error);
        showError(error.message || 'Failed to download file');
    } finally {
        showLoading(false);
    }
};
