'use client';

import { useEffect, useState } from 'react';
import { User } from 'lucide-react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { getUserConversations } from '@/lib/api';

interface ConversationUser {
  id: number;
  username: string;
  avatar_url?: string;
  full_name?: string;
}

export function NavRecentChats() {
  const { token } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [conversations, setConversations] = useState<ConversationUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Get the current active chat user ID from the URL
  const activeChatId = pathname?.startsWith('/chat/')
    ? parseInt(pathname.split('/')[2])
    : null;

  useEffect(() => {
    const fetchConversations = async () => {
      if (!token) return;

      try {
        setIsLoading(true);
        const data = await getUserConversations(token);
        setConversations(data);
      } catch (error) {
        console.error('Error fetching conversations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();

    // Set up periodic refresh
    const intervalId = setInterval(fetchConversations, 60000); // Refresh every minute

    return () => clearInterval(intervalId);
  }, [token]);

  const handleChatSelect = (userId: number) => {
    router.push(`/chat/${userId}`);
  };

  if (isLoading) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>Recent Chats</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {[1, 2, 3].map((_, index) => (
              <SidebarMenuItem key={index}>
                <SidebarMenuButton disabled>
                  <Avatar className="size-5">
                    <AvatarFallback className="rounded-full">
                      <div
                        className="animate-pulse rounded-full bg-muted"
                        style={{ width: '100%', height: '100%' }}
                      />
                    </AvatarFallback>
                  </Avatar>
                  <span>Loading...</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    );
  }

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Recent Chats</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {conversations.length > 0 ? (
            conversations.map((user) => {
              const isActive = activeChatId === user.id;

              return (
                <SidebarMenuItem key={user.id}>
                  <SidebarMenuButton
                    isActive={isActive}
                    onClick={() => handleChatSelect(user.id)}
                    className="flex items-center gap-2"
                  >
                    <Avatar className="size-5">
                      {user.avatar_url ? (
                        <AvatarImage
                          src={user.avatar_url}
                          alt={user.username}
                        />
                      ) : (
                        <AvatarFallback className="rounded-full bg-sidebar-primary text-sidebar-primary-foreground">
                          {user.username.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      )}
                    </Avatar>
                    <span>{user.full_name || user.username}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })
          ) : (
            <SidebarMenuItem>
              <SidebarMenuButton disabled>
                <User className="size-4" />
                <span>No conversations yet</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          )}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
