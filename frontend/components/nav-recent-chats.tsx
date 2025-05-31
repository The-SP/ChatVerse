'use client';

import { useRouter, usePathname } from 'next/navigation';
import { User } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { useChat } from '@/contexts/ChatContext';

export function NavRecentChats() {
  const router = useRouter();
  const pathname = usePathname();
  const { recentChats, isLoadingChats } = useChat();

  // Get the current active chat user ID from the URL
  const activeChatId = pathname?.startsWith('/chat/')
    ? parseInt(pathname.split('/')[2])
    : null;

  const handleChatSelect = (userId: number) => {
    router.push(`/chat/${userId}`);
  };

  if (isLoadingChats) {
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
          {recentChats.length > 0 ? (
            recentChats.map((user) => {
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
