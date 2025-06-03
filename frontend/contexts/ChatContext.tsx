'use client';

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { getUserConversations, getWsBaseUrl } from '@/lib/api';
import { ChatUser, Message } from '@/lib/types';

interface ChatContextType {
  recentChats: ChatUser[];
  isLoadingChats: boolean;
  wsConnected: boolean;
  addToRecentChats: (user: ChatUser) => void;
  refreshRecentChats: () => Promise<void>;
  sendMessage: (receiverId: number, content: string) => Promise<boolean>;
  subscribeToMessages: (callback: (message: Message) => void) => () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { token, user } = useAuth();
  const [recentChats, setRecentChats] = useState<ChatUser[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket refs and state
  const websocketRef = useRef<WebSocket | null>(null);
  const messageCallbacksRef = useRef<Set<(message: Message) => void>>(
    new Set(),
  );
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const fetchRecentChats = async () => {
    if (!token) {
      setIsLoadingChats(false);
      return;
    }

    try {
      setIsLoadingChats(true);
      const data = await getUserConversations(token);
      setRecentChats(data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setIsLoadingChats(false);
    }
  };

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!token || !user) return;

    // Don't create multiple connections
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsBaseUrl = getWsBaseUrl();
    const wsUrl = `${wsBaseUrl}/direct-messages/ws/?token=${token}`;

    console.log('Connecting to WebSocket:', wsUrl);

    const ws = new WebSocket(wsUrl);
    websocketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected globally');
      setWsConnected(true);
      reconnectAttemptsRef.current = 0; // Reset reconnect attempts on successful connection
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'new_message') {
          const receivedMessage: Message = {
            ...data.data,
            sender: data.data.sender || {
              id: data.data.sender_id,
              username:
                data.data.sender_id === user.id ? user.username : 'Unknown',
              avatar_url:
                data.data.sender_id === user.id ? user.avatar_url : undefined,
            },
          };

          // Notify all subscribers
          messageCallbacksRef.current.forEach((callback) => {
            callback(receivedMessage);
          });
        } else if (data.error) {
          console.error('WebSocket error:', data.error);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setWsConnected(false);
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      setWsConnected(false);
      websocketRef.current = null;

      // Only attempt to reconnect if not manually closed and user is still authenticated
      if (
        event.code !== 1000 &&
        token &&
        user &&
        reconnectAttemptsRef.current < maxReconnectAttempts
      ) {
        const delay = Math.min(
          1000 * Math.pow(2, reconnectAttemptsRef.current),
          30000,
        ); // Exponential backoff, max 30s
        console.log(
          `Attempting to reconnect in ${delay}ms (attempt ${
            reconnectAttemptsRef.current + 1
          }/${maxReconnectAttempts})`,
        );

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          if (document.visibilityState === 'visible') {
            connectWebSocket();
          }
        }, delay);
      }
    };

    return ws;
  }, [token, user]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Manual disconnect'); // Normal closure
      websocketRef.current = null;
    }

    setWsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  // Send message via WebSocket
  const sendMessage = useCallback(
    async (receiverId: number, content: string): Promise<boolean> => {
      if (
        !websocketRef.current ||
        websocketRef.current.readyState !== WebSocket.OPEN
      ) {
        console.log('WebSocket not connected, cannot send message');
        return false;
      }

      try {
        websocketRef.current.send(
          JSON.stringify({
            receiver_id: receiverId,
            content: content,
          }),
        );
        return true;
      } catch (error) {
        console.error('Error sending message via WebSocket:', error);
        return false;
      }
    },
    [],
  );

  // Subscribe to new messages
  const subscribeToMessages = useCallback(
    (callback: (message: Message) => void) => {
      messageCallbacksRef.current.add(callback);

      // Return unsubscribe function
      return () => {
        messageCallbacksRef.current.delete(callback);
      };
    },
    [],
  );

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Reconnect if not connected and user is authenticated
        if (!wsConnected && token && user) {
          connectWebSocket();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [wsConnected, token, user, connectWebSocket]);

  // Connect WebSocket when user is authenticated
  useEffect(() => {
    if (token && user) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [token, user, connectWebSocket, disconnectWebSocket]);

  // Fetch recent chats when token changes
  useEffect(() => {
    fetchRecentChats();
  }, [token]);

  const addToRecentChats = (user: ChatUser) => {
    setRecentChats((prevChats) => {
      // Check if the user already exists in the recent chats
      const existingIndex = prevChats.findIndex((chat) => chat.id === user.id);

      if (existingIndex >= 0) {
        // If the user is already at position 0, don't update at all to avoid re-renders
        if (existingIndex === 0) {
          return prevChats;
        }

        // Move the existing user to the top of the list
        const updatedChats = [...prevChats];
        const [movedUser] = updatedChats.splice(existingIndex, 1);
        return [movedUser, ...updatedChats];
      } else {
        // Add the new user to the top of the list
        return [user, ...prevChats];
      }
    });
  };

  const refreshRecentChats = async () => {
    return fetchRecentChats();
  };

  return (
    <ChatContext.Provider
      value={{
        recentChats,
        isLoadingChats,
        wsConnected,
        addToRecentChats,
        refreshRecentChats,
        sendMessage,
        subscribeToMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
