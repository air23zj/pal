import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  xsrfCookieName: null,
  xsrfHeaderName: null
});

// Create a separate instance for non-authenticated endpoints
export const publicApi = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  xsrfCookieName: null,
  xsrfHeaderName: null
});

// Add a request interceptor to include auth token and handle content type
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  const tokenType = localStorage.getItem('token_type') || 'Bearer';
  console.log('Token from localStorage:', token);
  
  if (token) {
    config.headers.Authorization = `${tokenType} ${token}`;
  }

  // Don't override Content-Type for FormData
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  
  // Log the request configuration
  console.log('Request Config:', {
    url: config.url,
    method: config.method,
    headers: config.headers,
    data: config.data,
    baseURL: config.baseURL
  });
  return config;
}, error => {
  console.error('Request interceptor error:', error);
  return Promise.reject(error);
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => {
    return response;
  },
  async error => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Clear all auth data
      localStorage.removeItem('token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('username');
      localStorage.removeItem('userId');
      
      // Return a rejected promise with a standardized error
      return Promise.reject({
        status: 401,
        message: 'Please login to continue'
      });
    }

    // For other errors, just pass them through
    return Promise.reject(error);
  }
);

// Export auth-related API functions
export const auth = {
  async login(username, password) {
    if (!username || !password) {
      throw new Error('Username and password are required');
    }

    console.log('Attempting login with:', { username });

    // Create form data with exact fields required by OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('grant_type', 'password');

    console.log('Request payload:', formData.toString());

    try {
      const response = await publicApi.post('/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json'
        }
      });

      console.log('Login response:', response.data);

      if (!response.data.access_token || !response.data.token_type) {
        throw new Error('Invalid response format');
      }

      // Store the token and username after successful login
      const { access_token, token_type } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('token_type', token_type.toLowerCase());
      localStorage.setItem('username', username);

      return response.data;
    } catch (error) {
      console.error('Login request error:', {
        status: error.response?.status,
        data: error.response?.data,
        headers: error.response?.headers
      });

      // Clear any partial auth data on error
      localStorage.removeItem('token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('username');
      localStorage.removeItem('userId');

      throw error;
    }
  },

  async register(userData) {
    const response = await publicApi.post('/users', userData);
    return response.data;
  },

  async verify() {
    const response = await api.get('/users/me');
    return {
      valid: true,
      user: response.data
    };
  },

  async getCurrentUser() {
    const response = await api.get('/users/me');
    return response.data;
  },

  async logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
    return { success: true };
  }
};
