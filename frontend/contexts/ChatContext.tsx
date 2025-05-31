'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ChatUser } from '@/lib/types';
import { getUserConversations } from '@/lib/api';

interface ChatContextType {
  recentChats: ChatUser[];
  isLoadingChats: boolean;
  addToRecentChats: (user: ChatUser) => void;
  refreshRecentChats: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [recentChats, setRecentChats] = useState<ChatUser[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);

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
        addToRecentChats,
        refreshRecentChats,
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
