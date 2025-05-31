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
import { getDirectMessages, getWsBaseUrl, sendDirectMessage } from '@/lib/api';
import { ChatUser, Message } from '@/lib/types';

interface ChatInterfaceProps {
  userId: number;
  chatUser: ChatUser;
}

export function ChatInterface({ userId, chatUser }: ChatInterfaceProps) {
  const { user, token } = useAuth();
  const { addToRecentChats } = useChat();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);

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

  // Initialize WebSocket connection
  useEffect(() => {
    if (!token || !userId || !user) return;

    const wsBaseUrl = getWsBaseUrl();
    const wsUrl = `${wsBaseUrl}/direct-messages/ws/?token=${token}`;

    const setupWebSocket = () => {
      const ws = new WebSocket(wsUrl);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected for user:', userId);
        setWsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'new_message') {
            const receivedMessage = data.data;

            // Only add the message if it's part of this conversation
            if (
              (receivedMessage.sender_id === userId &&
                receivedMessage.receiver_id === user.id) ||
              (receivedMessage.sender_id === user.id &&
                receivedMessage.receiver_id === userId)
            ) {
              // Add message to state if it's not already there
              setMessages((prevMessages) => {
                // Don't add duplicate messages
                if (
                  !prevMessages.some((msg) => msg.id === receivedMessage.id)
                ) {
                  return [
                    ...prevMessages,
                    {
                      ...receivedMessage,
                      sender:
                        receivedMessage.sender_id === user.id
                          ? user
                          : receivedMessage.sender,
                    },
                  ];
                }
                return prevMessages;
              });
            }
          } else if (data.error) {
            console.error('WebSocket error:', data.error);
            setError(`WebSocket error: ${data.error}`);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error for user:', userId, event);
        setError('Connection error. Try refreshing the page.');
        setWsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);

        // Attempt to reconnect after a delay
        setTimeout(() => {
          if (document.visibilityState !== 'hidden') {
            setupWebSocket();
          }
        }, 3000);
      };

      return ws;
    };

    const ws = setupWebSocket();

    // Handle page visibility changes to reconnect when tab becomes visible again
    const handleVisibilityChange = () => {
      if (
        document.visibilityState === 'visible' &&
        !websocketRef.current?.OPEN
      ) {
        setupWebSocket();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Initial fetch of messages
    const fetchInitialMessages = async () => {
      try {
        console.log('Fetching initial messages for user:', userId);
        const data = await getDirectMessages(Number(userId), token);
        console.log('Received messages:', data?.length || 0);
        setMessages(data || []);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching initial messages:', error);
        setError('Failed to load messages. Please try again.');
        setIsLoading(false);
      }
    };

    fetchInitialMessages();

    // Clean up function
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    };
  }, [token, userId, user]);

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
    const tempMessage = {
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
    } as Message;

    // Add to messages immediately for UI feedback
    setMessages((prevMessages) => [...prevMessages, tempMessage]);
    setNewMessage('');

    // If WebSocket is connected, send via WebSocket
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      try {
        websocketRef.current.send(
          JSON.stringify({
            receiver_id: userId,
            content: newMessage,
          }),
        );
        // No need to update the message since the server will echo it back via WebSocket
      } catch (error) {
        console.error('Error sending message via WebSocket:', error);

        // Fallback to HTTP method
        sendMessageViaHTTP(tempId, newMessage);
      }
    } else {
      console.log('WebSocket not open, sending via HTTP');
      // WebSocket is not connected, use HTTP
      sendMessageViaHTTP(tempId, newMessage);
    }
  };

  // Fallback to HTTP method if WebSocket fails
  const sendMessageViaHTTP = async (tempId: number, content: string) => {
    try {
      if (!token || !user) return;

      console.log('Sending message via HTTP to user:', userId);
      const sentMessage = await sendDirectMessage(content, userId, token);
      console.log('Message sent successfully:', sentMessage?.id);

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
      console.error('Error sending message:', error);
      setMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.id === tempId ? { ...msg, failed: true } : msg,
        ),
      );
      setError('Failed to send message. Please try again.');
    }
  };

  // Check if a message is from the current user
  const isCurrentUserMessage = (message: Message) => {
    return user && message.sender_id === user.id;
  };

  // Handle retry for failed messages
  const handleRetryMessage = (message: Message & { failed?: boolean }) => {
    if (!message.failed) return;

    // Remove the failed message
    setMessages((prevMessages) =>
      prevMessages.filter((msg) => msg.id !== message.id),
    );

    // Create a new message with the same content
    const content = message.content;
    setNewMessage(content);

    // Focus on the input
    document.querySelector('input')?.focus();
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
                            ? 'bg-destructive/10 text-destructive cursor-pointer'
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
