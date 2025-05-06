'use client';

import { useEffect, useState } from 'react';
import { User } from 'lucide-react';

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

interface ConversationUser {
  id: number;
  username: string;
  avatar_url?: string;
  full_name?: string;
}

export function NavRecentChats() {
  const { token } = useAuth();
  const [conversations, setConversations] = useState<ConversationUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchConversations = async () => {
      if (!token) return;

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/direct-messages/conversations`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        );

        if (!response.ok) {
          throw new Error('Failed to fetch conversations');
        }

        const data = await response.json();
        setConversations(data);
      } catch (error) {
        console.error('Error fetching conversations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [token]);

  if (isLoading) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>Recent Chats</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {[1, 2, 3].map((_, index) => (
              <SidebarMenuItem key={index}>
                <SidebarMenuButton disabled>
                  <Avatar className="size-4">
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
            conversations.map((user) => (
              <SidebarMenuItem key={user.id}>
                <SidebarMenuButton asChild>
                  <a
                    href={`/chat/${user.id}`}
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
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))
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
