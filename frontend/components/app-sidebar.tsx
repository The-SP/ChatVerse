'use client';

import type * as React from 'react';
import { MessageSquare } from 'lucide-react';

import { NavMain } from './nav-main';
import { NavRecentChats } from './nav-recent-chats';
import { NavUser } from './nav-user';
import { UserSearch } from './user-search';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';

const data = {
  navMain: [
    {
      title: 'general',
      url: '#',
      isActive: true,
    },
    {
      title: 'random',
      url: '#',
    },
    {
      title: 'announcements',
      url: '#',
    },
    {
      title: 'development',
      url: '#',
    },
    {
      title: 'design',
      url: '#',
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="#">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <MessageSquare className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">Chats</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <UserSearch />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavRecentChats />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  );
}
