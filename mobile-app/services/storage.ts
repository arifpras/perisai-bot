// Storage Service - AsyncStorage wrapper with TypeScript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Storage keys
export const STORAGE_KEYS = {
  CHAT_HISTORY: '@perisai:chat_history',
  PERSONA_PREFERENCE: '@perisai:persona',
  THEME_MODE: '@perisai:theme',
  NOTIFICATIONS_ENABLED: '@perisai:notifications',
  LAST_SYNC: '@perisai:last_sync',
  CACHED_QUERIES: '@perisai:cached_queries',
} as const;

// Types
export interface ChatMessage {
  id: string;
  text: string;
  persona: 'kei' | 'kin' | 'both' | 'user';
  timestamp: number;
  imageBase64?: string;
  rows?: any[];
}

export interface CachedQuery {
  query: string;
  response: any;
  timestamp: number;
  persona: string;
}

export interface UserPreferences {
  persona: 'kei' | 'kin' | 'both';
  theme: 'light' | 'dark' | 'auto';
  notificationsEnabled: boolean;
}

// Storage utilities
export const storage = {
  /**
   * Save chat history
   */
  async saveChatHistory(messages: ChatMessage[]): Promise<void> {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.CHAT_HISTORY,
        JSON.stringify(messages)
      );
    } catch (error) {
      console.error('Error saving chat history:', error);
      throw error;
    }
  },

  /**
   * Load chat history
   */
  async loadChatHistory(): Promise<ChatMessage[]> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading chat history:', error);
      return [];
    }
  },

  /**
   * Clear chat history
   */
  async clearChatHistory(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
    } catch (error) {
      console.error('Error clearing chat history:', error);
      throw error;
    }
  },

  /**
   * Save persona preference
   */
  async savePersonaPreference(persona: 'kei' | 'kin' | 'both'): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.PERSONA_PREFERENCE, persona);
    } catch (error) {
      console.error('Error saving persona preference:', error);
      throw error;
    }
  },

  /**
   * Load persona preference
   */
  async loadPersonaPreference(): Promise<'kei' | 'kin' | 'both'> {
    try {
      const persona = await AsyncStorage.getItem(STORAGE_KEYS.PERSONA_PREFERENCE);
      return (persona as 'kei' | 'kin' | 'both') || 'kei';
    } catch (error) {
      console.error('Error loading persona preference:', error);
      return 'kei';
    }
  },

  /**
   * Cache query result
   */
  async cacheQuery(query: string, response: any, persona: string): Promise<void> {
    try {
      const cached = await this.loadCachedQueries();
      const newCache: CachedQuery = {
        query,
        response,
        timestamp: Date.now(),
        persona,
      };
      
      // Keep only last 50 queries
      const updatedCache = [newCache, ...cached.slice(0, 49)];
      await AsyncStorage.setItem(
        STORAGE_KEYS.CACHED_QUERIES,
        JSON.stringify(updatedCache)
      );
    } catch (error) {
      console.error('Error caching query:', error);
    }
  },

  /**
   * Load cached queries
   */
  async loadCachedQueries(): Promise<CachedQuery[]> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.CACHED_QUERIES);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading cached queries:', error);
      return [];
    }
  },

  /**
   * Find cached query
   */
  async findCachedQuery(query: string, persona: string): Promise<CachedQuery | null> {
    try {
      const cached = await this.loadCachedQueries();
      const found = cached.find(
        (c) => c.query.toLowerCase() === query.toLowerCase() && c.persona === persona
      );
      
      // Return only if less than 1 hour old
      if (found && Date.now() - found.timestamp < 3600000) {
        return found;
      }
      return null;
    } catch (error) {
      console.error('Error finding cached query:', error);
      return null;
    }
  },

  /**
   * Save user preferences
   */
  async savePreferences(prefs: UserPreferences): Promise<void> {
    try {
      await AsyncStorage.multiSet([
        [STORAGE_KEYS.PERSONA_PREFERENCE, prefs.persona],
        [STORAGE_KEYS.THEME_MODE, prefs.theme],
        [STORAGE_KEYS.NOTIFICATIONS_ENABLED, String(prefs.notificationsEnabled)],
      ]);
    } catch (error) {
      console.error('Error saving preferences:', error);
      throw error;
    }
  },

  /**
   * Load user preferences
   */
  async loadPreferences(): Promise<UserPreferences> {
    try {
      const keys = [
        STORAGE_KEYS.PERSONA_PREFERENCE,
        STORAGE_KEYS.THEME_MODE,
        STORAGE_KEYS.NOTIFICATIONS_ENABLED,
      ];
      const values = await AsyncStorage.multiGet(keys);
      
      return {
        persona: (values[0][1] as 'kei' | 'kin' | 'both') || 'kei',
        theme: (values[1][1] as 'light' | 'dark' | 'auto') || 'auto',
        notificationsEnabled: values[2][1] === 'true',
      };
    } catch (error) {
      console.error('Error loading preferences:', error);
      return {
        persona: 'kei',
        theme: 'auto',
        notificationsEnabled: true,
      };
    }
  },

  /**
   * Clear all app data
   */
  async clearAll(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
      throw error;
    }
  },

  /**
   * Get storage size (for debugging)
   */
  async getStorageSize(): Promise<number> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      let totalSize = 0;
      
      for (const key of keys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += new Blob([value]).size;
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Error getting storage size:', error);
      return 0;
    }
  },
};

export default storage;
