import { auth } from '../utils/api.js';
import { showLoading, showError, showSuccess } from '../utils/ui';

export function loadLoginForm() {
    console.log('Loading login form...');
    const content = document.getElementById('mainContent');
    content.innerHTML = `
        <div class="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
            <h2 class="text-2xl font-bold text-center mb-6">Login to Clarity</h2>
            <form id="loginForm" class="space-y-4">
                <div>
                    <label for="username" class="block text-gray-700 text-sm font-bold mb-2">Username</label>
                    <input type="text" id="username" name="username" required
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>
                <div>
                    <label for="password" class="block text-gray-700 text-sm font-bold mb-2">Password</label>
                    <input type="password" id="password" name="password" required
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>
                <div id="errorMessage" class="text-red-500 text-sm hidden"></div>
                <button type="submit" 
                    class="w-full bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                    Login
                </button>
            </form>
            <div class="text-center mt-4">
                <p class="text-gray-600">Don't have an account? 
                    <a href="#" onclick="loadRegisterForm()" class="text-primary-600 hover:text-primary-800">Register</a>
                </p>
            </div>
        </div>
    `;

    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showError('Please fill in all fields');
        return;
    }
    
    showLoading(true);
    try {
        // Login - token is stored in auth.login()
        const response = await auth.login(username, password);
        console.log('Login response:', response);
        
        if (!response.access_token) {
            throw new Error('No access token received');
        }
        
        // Get user details and store ID
        const userData = await auth.getCurrentUser();
        console.log('User data:', userData);
        localStorage.setItem('userId', userData.id.toString());
        
        showSuccess('Login successful');
        history.pushState(null, '', '/');
        
        // Import and load main interface
        const { loadMainContent } = await import('../main.js');
        loadMainContent();
    } catch (error) {
        console.error('Login error:', error);
        const errorMessage = error.response?.data?.detail || 
                           error.response?.data?.message || 
                           error.message || 
                           'An error occurred during login';
        showError('Login failed: ' + errorMessage);
    } finally {
        showLoading(false);
    }
}

export function loadRegisterForm() {
    const content = document.getElementById('mainContent');
    content.innerHTML = `
        <div class="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
            <h2 class="text-2xl font-bold text-center mb-6">Create Account</h2>
            <form id="registerForm" class="space-y-4">
                <div>
                    <label for="username" class="block text-gray-700 text-sm font-bold mb-2">Username</label>
                    <input type="text" id="username" name="username" required
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>
                <div>
                    <label for="email" class="block text-gray-700 text-sm font-bold mb-2">Email</label>
                    <input type="email" id="email" name="email" required
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>
                <div>
                    <label for="password" class="block text-gray-700 text-sm font-bold mb-2">Password</label>
                    <input type="password" id="password" name="password" required
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>
                <div>
                    <label for="confirmPassword" class="block text-gray-700 text-sm font-bold mb-2">Confirm Password</label>
                    <input type="password" id="confirmPassword" name="confirmPassword" required
                        class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
                </div>
                <div id="errorMessage" class="text-red-500 text-sm p-2 rounded-md hidden"></div>
                <button type="submit" 
                    class="w-full bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                    Register
                </button>
            </form>
            <div class="text-center mt-4">
                <p class="text-gray-600">Already have an account? 
                    <a href="#" onclick="loadLoginForm()" class="text-primary-600 hover:text-primary-800">Login</a>
                </p>
            </div>
        </div>
    `;

    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // Clear previous error
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.classList.add('hidden');

        if (password !== confirmPassword) {
            showError('Passwords do not match');
            return;
        }

        try {
            showLoading(true);
            console.log('Registering user:', { username, email }); // Debug log
            const response = await auth.register({ username, email, password });
            console.log('Registration response:', response); // Debug log
            showSuccess('Registration successful! Please login.');
            setTimeout(() => {
                loadLoginForm();
            }, 1500);
        } catch (error) {
            console.error('Registration error:', error); // Debug log
            const errorDetail = error.response?.data?.detail || 'Registration failed';
            showError(errorDetail);
        } finally {
            showLoading(false);
        }
    });
}

// Make functions globally available
window.loadRegisterForm = loadRegisterForm;
window.loadLoginForm = loadLoginForm; 