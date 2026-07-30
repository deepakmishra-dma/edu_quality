import axios, { AxiosError } from 'axios';

const axiosInstance = axios.create({
  withCredentials: true // Always send cookies with requests
});

const getUserFriendlyErrorMessage = (error: AxiosError): string => {
  // Network connectivity issues
  if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
    return 'No internet connection. Please check your network and try again.';
  }
  
  // DNS resolution issues
  if (error.code === 'ENOTFOUND' || error.message.includes('ENOTFOUND')) {
    return 'Unable to connect to the server. Please check your internet connection.';
  }
  
  // Connection refused/timeout
  if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
    return 'Connection failed. Please try again later.';
  }
  
  // Server errors
  if (error.response) {
    switch (error.response.status) {
      case 403:
        return 'Access denied. Please log in again.';
      case 404:
        return 'Service not available. Please try again later.';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'Server error. Please try again later.';
      default:
        return `Server error (${error.response.status}). Please try again.`;
    }
  }
  
  // Generic fallback
  return 'Something went wrong. Please check your connection and try again.';
};

// Response interceptor to handle errors globally
axiosInstance.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    // Get user-friendly error message
    const userFriendlyMessage = getUserFriendlyErrorMessage(error);
    
    // Attach the user-friendly message to the error
    error.message = userFriendlyMessage;
    
    // Log the original error for debugging
    console.error('API Error:', {
      code: error.code,
      message: error.message,
      status: error.response?.status,
      url: error.config?.url
    });
    return Promise.reject(error);
  }
);

export default axiosInstance;
