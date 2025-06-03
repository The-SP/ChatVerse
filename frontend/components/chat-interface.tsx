'use client';

import { Send } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAuth } from '@/contexts/AuthContext';
import { useChat } from '@/contexts/ChatContext';
import { getDirectMessages, sendDirectMessage } from '@/lib/api';
import { ChatUser, Message } from '@/lib/types';

interface ChatInterfaceProps {
  userId: number;
  chatUser: ChatUser;
}

export function ChatInterface({ userId, chatUser }: ChatInterfaceProps) {
  const { user, token } = useAuth();
  const { addToRecentChats, wsConnected, sendMessage, subscribeToMessages } =
    useChat();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Function to format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Function to get initials for avatar fallback
  const getInitials = (name: string) => {
    return name.charAt(0).toUpperCase();
  };

  // Function to scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Check if a message is from the current user
  const isCurrentUserMessage = (message: Message) => {
    return user && message.sender_id === user.id;
  };

  // Load initial messages when component mounts or userId changes
  useEffect(() => {
    const fetchInitialMessages = async () => {
      if (!token || !userId) return;

      try {
        console.log('Fetching initial messages for user:', userId);
        setIsLoading(true);
        setError(null);

        const data = await getDirectMessages(Number(userId), token);
        console.log('Received messages:', data?.length || 0);
        setMessages(data || []);
      } catch (error) {
        console.error('Error fetching initial messages:', error);
        setError('Failed to load messages. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    // Reset messages when switching to a new chat
    setMessages([]);
    fetchInitialMessages();
  }, [token, userId]);

  // Subscribe to new messages from the global WebSocket
  useEffect(() => {
    if (!user || !userId) return;

    const handleNewMessage = (message: Message) => {
      // Only add messages that are part of this conversation
      const isPartOfConversation =
        (message.sender_id === userId && message.receiver_id === user.id) ||
        (message.sender_id === user.id && message.receiver_id === userId);

      if (isPartOfConversation) {
        setMessages((prevMessages) => {
          // Don't add duplicate messages
          if (!prevMessages.some((msg) => msg.id === message.id)) {
            return [...prevMessages, message];
          }
          return prevMessages;
        });
      }
    };

    // Subscribe to messages
    const unsubscribe = subscribeToMessages(handleNewMessage);

    // Cleanup subscription when component unmounts or dependencies change
    return unsubscribe;
  }, [subscribeToMessages, userId, user]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Send new message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !token || !user || !userId) return;

    // Add chat user to recent chats when a message is sent
    if (chatUser) {
      addToRecentChats(chatUser);
    }

    const tempId = Date.now();
    const tempMessage: Message & { failed?: boolean } = {
      id: tempId,
      content: newMessage,
      created_at: new Date().toISOString(),
      sender_id: user.id,
      receiver_id: userId,
      is_read: false,
      sender: {
        id: user.id,
        username: user.username,
        avatar_url: user.avatar_url,
        full_name: user.full_name,
      },
    };

    // Add to messages immediately for UI feedback
    setMessages((prevMessages) => [...prevMessages, tempMessage]);
    const messageContent = newMessage;
    setNewMessage('');

    // Try to send via WebSocket first
    const sentViaWebSocket = await sendMessage(userId, messageContent);

    if (!sentViaWebSocket) {
      // Fallback to HTTP method
      console.log('WebSocket not available, sending via HTTP');
      try {
        const sentMessage = await sendDirectMessage(
          messageContent,
          userId,
          token,
        );

        // Add sender info to the response
        sentMessage.sender = {
          id: user.id,
          username: user.username,
          avatar_url: user.avatar_url,
          full_name: user.full_name,
        };

        // Update the message in state with server-generated ID
        setMessages((prevMessages) =>
          prevMessages.map((msg) => (msg.id === tempId ? sentMessage : msg)),
        );
      } catch (error) {
        console.error('Error sending message via HTTP:', error);
        // Mark message as failed
        setMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === tempId ? { ...msg, failed: true } : msg,
          ),
        );
        setError('Failed to send message. Please try again.');
      }
    }
  };

  // Handle retry for failed messages
  const handleRetryMessage = (message: Message & { failed?: boolean }) => {
    if (!message.failed) return;

    // Remove the failed message
    setMessages((prevMessages) =>
      prevMessages.filter((msg) => msg.id !== message.id),
    );

    // Set the content back to the input
    setNewMessage(message.content);

    // Focus on the input
    setTimeout(() => {
      document.querySelector('input')?.focus();
    }, 0);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>Loading messages...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {!wsConnected && (
        <div className="bg-amber-100 p-2 text-amber-800 text-sm text-center">
          Currently using offline mode. Reconnecting...
        </div>
      )}

      {error && (
        <div className="bg-red-100 p-2 text-red-800 text-sm text-center">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="flex flex-col gap-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center pt-10">
              <p className="text-muted-foreground">
                No messages yet. Start a conversation!
              </p>
            </div>
          ) : (
            messages.map((message) => {
              const isCurrentUser = isCurrentUserMessage(message);
              const senderName = isCurrentUser
                ? user?.full_name || user?.username || 'You'
                : chatUser?.full_name || chatUser?.username || 'User';
              const avatarUrl = isCurrentUser
                ? user?.avatar_url
                : chatUser?.avatar_url;

              const isFailed = 'failed' in message && message.failed === true;

              return (
                <div
                  key={message.id}
                  className={`flex gap-2 ${
                    isCurrentUser ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  <Avatar className="h-8 w-8 flex-shrink-0">
                    <AvatarImage src={avatarUrl || ''} alt={senderName} />
                    <AvatarFallback>{getInitials(senderName)}</AvatarFallback>
                  </Avatar>
                  <div
                    className={`flex max-w-[80%] flex-col ${
                      isCurrentUser ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-medium ${
                          isCurrentUser ? 'order-last' : 'order-first'
                        }`}
                      >
                        {senderName}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(message.created_at)}
                        {isFailed && ' (failed)'}
                      </span>
                    </div>
                    <Card
                      className={`mt-1 px-3 py-2 ${
                        isCurrentUser
                          ? isFailed
                            ? 'bg-destructive/10 text-destructive cursor-pointer hover:bg-destructive/20'
                            : 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                      onClick={() =>
                        isFailed &&
                        handleRetryMessage(
                          message as Message & { failed: boolean },
                        )
                      }
                    >
                      {message.content}
                      {isFailed && (
                        <div className="text-xs mt-1">Click to retry</div>
                      )}
                    </Card>
                  </div>
                </div>
              );
            })
          )}
          {/* This is the div that we'll scroll to */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      <div className="border-t p-4">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Input
            placeholder="Type your message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={!newMessage.trim()}>
            <Send className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </form>
      </div>
    </div>
  );
}
