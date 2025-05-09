'use client';

import { useEffect, useState, useRef } from 'react';
import { Send } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getDirectMessages, sendDirectMessage } from '@/lib/api';

interface Message {
  id: number;
  content: string;
  created_at: string;
  sender_id: number;
  receiver_id: number;
  is_read: boolean;
  sender?: {
    id: number;
    username: string;
    avatar_url?: string;
    full_name?: string;
  };
}

interface ChatInterfaceProps {
  userId: number;
}

export function ChatInterface({ userId }: ChatInterfaceProps) {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Function to format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Function to get initials for avatar fallback
  const getInitials = (name: string) => {
    return name.charAt(0).toUpperCase();
  };

  // Fetch messages
  useEffect(() => {
    const fetchMessages = async () => {
      if (!token || !userId) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      try {
        console.log('Fetching messages for user:', userId);
        const data = await getDirectMessages(Number(userId), token);
        console.log('Received messages:', data?.length || 0);
        setMessages(data || []);
        setIsLoading(false);
        setError(null);
      } catch (error) {
        console.error('Error fetching messages:', error);
        setError('Failed to load messages. Please try again.');
        setIsLoading(false);
      }
    };

    fetchMessages();
    const intervalId = setInterval(fetchMessages, 5000);

    return () => clearInterval(intervalId);
  }, [token, userId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({
        top: scrollAreaRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  // Send new message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !token || !user) return;

    const receiverId = Number(userId);
    const tempId = Date.now();
    const tempMessage = {
      id: tempId,
      content: newMessage,
      created_at: new Date().toISOString(),
      sender_id: user.id,
      receiver_id: receiverId,
      is_read: false,
      sender: {
        id: user.id,
        username: user.username,
        avatar_url: user.avatar_url,
        full_name: user.full_name,
      },
      pending: true,
    } as Message & { pending?: boolean };

    setMessages((prevMessages) => [...prevMessages, tempMessage]);
    setNewMessage('');

    try {
      console.log('Sending message to user:', receiverId);
      const sentMessage = await sendDirectMessage(
        newMessage,
        receiverId,
        token,
      );
      console.log('Message sent successfully:', sentMessage?.id);

      sentMessage.sender = {
        id: user.id,
        username: user.username,
        avatar_url: user.avatar_url,
        full_name: user.full_name,
      };

      setMessages((prevMessages) =>
        prevMessages.map((msg) => (msg.id === tempId ? sentMessage : msg)),
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prevMessages) =>
        prevMessages.map((msg) =>
          msg.id === tempId ? { ...msg, failed: true, pending: false } : msg,
        ),
      );
      setError('Failed to send message. Please try again.');
    }
  };

  // Check if a message is from the current user
  const isCurrentUserMessage = (message: Message) => {
    return user && message.sender_id === user.id;
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>Loading messages...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
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
                : message.sender?.full_name ||
                  message.sender?.username ||
                  'User';
              const avatarUrl = isCurrentUser
                ? user?.avatar_url
                : message.sender?.avatar_url;

              const isPending =
                'pending' in message && message.pending === true;
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
                        {isPending && ' (sending...)'}
                        {isFailed && ' (failed)'}
                      </span>
                    </div>
                    <Card
                      className={`mt-1 px-3 py-2 ${
                        isCurrentUser
                          ? isFailed
                            ? 'bg-destructive/10 text-destructive'
                            : 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      {message.content}
                    </Card>
                  </div>
                </div>
              );
            })
          )}
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
