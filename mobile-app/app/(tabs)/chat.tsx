// Chat Screen - Main interface for bond queries
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Image,
  ActivityIndicator,
} from 'react-native';
import {
  TextInput,
  Button,
  Card,
  Text,
  Chip,
  useTheme,
  Avatar,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api, QueryResponse } from '../../services/api';
import { storage, ChatMessage } from '../../services/storage';

type Persona = 'kei' | 'kin' | 'both';

export default function ChatScreen() {
  const theme = useTheme();
  const scrollViewRef = useRef<ScrollView>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [persona, setPersona] = useState<Persona>('kei');

  // Load chat history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Save messages whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      storage.saveChatHistory(messages);
    }
  }, [messages]);

  const loadHistory = async () => {
    const history = await storage.loadChatHistory();
    setMessages(history);
    const savedPersona = await storage.loadPersonaPreference();
    setPersona(savedPersona);
  };

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputText,
      persona: 'user',
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      // Check cache first
      const cached = await storage.findCachedQuery(inputText, persona);
      
      let response: QueryResponse;
      if (cached) {
        response = cached.response;
      } else {
        response = await api.sendChat(inputText, persona);
        await storage.cacheQuery(inputText, response, persona);
      }

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: response.text,
        persona: persona,
        timestamp: Date.now(),
        imageBase64: response.image_base64,
        rows: response.rows,
      };

      setMessages((prev) => [...prev, botMessage]);
      
      // Scroll to bottom
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: '❌ Failed to get response. Please check your connection and try again.',
        persona: persona,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const changePersona = async (newPersona: Persona) => {
    setPersona(newPersona);
    await storage.savePersonaPreference(newPersona);
  };

  const clearHistory = async () => {
    setMessages([]);
    await storage.clearChatHistory();
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.persona === 'user';
    
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessage : styles.botMessage,
        ]}
      >
        {!isUser && (
          <Avatar.Text
            size={32}
            label={message.persona === 'kei' ? 'K' : message.persona === 'kin' ? 'N' : 'B'}
            style={[
              styles.avatar,
              {
                backgroundColor:
                  message.persona === 'kei'
                    ? theme.colors.primary
                    : message.persona === 'kin'
                    ? theme.colors.secondary
                    : theme.colors.tertiary,
              },
            ]}
          />
        )}
        
        <Card style={[styles.messageCard, isUser && styles.userCard]}>
          <Card.Content>
            <Text style={styles.messageText}>{message.text}</Text>
            
            {/* Display table rows if present */}
            {message.rows && message.rows.length > 0 && (
              <View style={styles.tableContainer}>
                {message.rows.slice(0, 10).map((row, idx) => (
                  <Text key={idx} style={styles.tableRow}>
                    🔹 {row.series} | {row.tenor}
                    {row.date ? ` | ${row.date}` : ''}
                    {'\n'}   Price: {row.price.toFixed(2)} | Yield: {row.yield.toFixed(2)}%
                  </Text>
                ))}
                {message.rows.length > 10 && (
                  <Text style={styles.moreText}>
                    ... and {message.rows.length - 10} more rows
                  </Text>
                )}
              </View>
            )}
            
            {/* Display chart if present */}
            {message.imageBase64 && (
              <Image
                source={{ uri: `data:image/png;base64,${message.imageBase64}` }}
                style={styles.chartImage}
                resizeMode="contain"
              />
            )}
          </Card.Content>
        </Card>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={100}
      >
        {/* Persona Selector */}
        <View style={styles.personaContainer}>
          <Text variant="labelMedium" style={styles.personaLabel}>
            Select Persona:
          </Text>
          <View style={styles.chipContainer}>
            <Chip
              selected={persona === 'kei'}
              onPress={() => changePersona('kei')}
              style={styles.chip}
            >
              Kei (Quant)
            </Chip>
            <Chip
              selected={persona === 'kin'}
              onPress={() => changePersona('kin')}
              style={styles.chip}
            >
              Kin (Strategy)
            </Chip>
            <Chip
              selected={persona === 'both'}
              onPress={() => changePersona('both')}
              style={styles.chip}
            >
              Both
            </Chip>
          </View>
          <Button mode="text" onPress={clearHistory} compact>
            Clear History
          </Button>
        </View>

        {/* Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
        >
          {messages.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text variant="titleLarge" style={styles.emptyTitle}>
                👋 Welcome to Perisai Bond Bot
              </Text>
              <Text variant="bodyMedium" style={styles.emptyText}>
                Ask about Indonesian bond yields, prices, and auctions!
              </Text>
              <Text variant="bodySmall" style={styles.exampleText}>
                Examples:{'\n'}
                • "yield 5 year in dec 2024"{'\n'}
                • "plot yield 10 year from 2023 to 2024"{'\n'}
                • "auction demand in 2026"
              </Text>
            </View>
          ) : (
            messages.map(renderMessage)
          )}
          
          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={theme.colors.primary} />
              <Text variant="bodySmall" style={styles.loadingText}>
                {persona === 'kei'
                  ? 'Kei is analyzing...'
                  : persona === 'kin'
                  ? 'Kin is thinking...'
                  : 'Both are working...'}
              </Text>
            </View>
          )}
        </ScrollView>

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            mode="outlined"
            placeholder="Ask about bonds..."
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={sendMessage}
            multiline
            maxLength={500}
            style={styles.input}
            right={
              <TextInput.Icon
                icon="send"
                onPress={sendMessage}
                disabled={!inputText.trim() || loading}
              />
            }
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  personaContainer: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  personaLabel: {
    marginBottom: 8,
  },
  chipContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  chip: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  emptyTitle: {
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyText: {
    marginBottom: 24,
    textAlign: 'center',
    opacity: 0.7,
  },
  exampleText: {
    textAlign: 'left',
    opacity: 0.6,
    fontFamily: 'monospace',
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  botMessage: {
    justifyContent: 'flex-start',
  },
  avatar: {
    marginRight: 8,
  },
  messageCard: {
    maxWidth: '80%',
  },
  userCard: {
    alignSelf: 'flex-end',
  },
  messageText: {
    fontSize: 14,
  },
  tableContainer: {
    marginTop: 8,
    padding: 8,
    backgroundColor: '#f5f5f5',
    borderRadius: 4,
  },
  tableRow: {
    fontSize: 12,
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  moreText: {
    fontSize: 12,
    fontStyle: 'italic',
    opacity: 0.7,
    marginTop: 4,
  },
  chartImage: {
    width: '100%',
    height: 250,
    marginTop: 8,
    borderRadius: 4,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
  },
  loadingText: {
    marginLeft: 8,
    opacity: 0.7,
  },
  inputContainer: {
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  input: {
    maxHeight: 120,
  },
});
