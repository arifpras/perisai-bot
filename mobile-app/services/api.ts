// API Service - Connects to FastAPI backend
import axios, { AxiosInstance, AxiosError } from 'axios';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

// API Configuration
// On native/Expo Go: use the exposed IP from app.json
// On web: use localhost
// Falls back to localhost if nothing is configured
let API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000';

// If running on web, ensure we use localhost
if (Platform.OS === 'web') {
  API_URL = 'http://localhost:8000';
}

const TIMEOUT = 30000; // 30 seconds

// Types
export interface QueryRequest {
  q: string;
  persona?: 'kei' | 'kin' | 'both';
  csv?: string;
}

export interface QueryResponse {
  text: string;
  rows?: Array<{
    series: string;
    tenor: string;
    date?: string;
    price: number;
    yield: number;
  }>;
  image_base64?: string;
  query_type?: string;
  intent?: string;
  error?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version?: string;
}

export interface BotStats {
  total_queries: number;
  active_users: number;
  avg_response_time: number;
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': `Perisai-Mobile/${Platform.OS}/${Constants.expoConfig?.version || '1.0.0'}`,
  },
});

// Request interceptor (for auth tokens in future)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = await SecureStore.getItemAsync('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (for error handling)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API Methods
export const api = {
  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  },

  /**
   * Send query to backend
   */
  async sendQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post<QueryResponse>('/query', request);
    return response.data;
  },

  /**
   * Send chat message (with persona)
   */
  async sendChat(message: string, persona: 'kei' | 'kin' | 'both' = 'kei'): Promise<QueryResponse> {
    const response = await apiClient.post<QueryResponse>('/chat', {
      q: message,
      persona,
    });
    return response.data;
  },

  /**
   * Get bot statistics
   */
  async getBotStats(): Promise<BotStats> {
    const response = await apiClient.get<BotStats>('/bot/stats');
    return response.data;
  },

  /**
   * Test connection with retry
   */
  async testConnection(maxRetries: number = 3): Promise<boolean> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        await this.checkHealth();
        return true;
      } catch (error) {
        if (i === maxRetries - 1) {
          return false;
        }
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
      }
    }
    return false;
  },
};

export default api;
