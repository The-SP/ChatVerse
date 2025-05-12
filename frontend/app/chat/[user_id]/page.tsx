'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { AppSidebar } from '@/components/app-sidebar';
import { ChatInterface } from '@/components/chat-interface';
import {
    Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbPage
} from '@/components/ui/breadcrumb';
import { Separator } from '@/components/ui/separator';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { useAuth } from '@/contexts/AuthContext';
import { getUserProfile } from '@/lib/api';
import { ChatUser } from '@/lib/types';

export default function ChatPage() {
  const params = useParams<{ user_id: string }>();
  const { token } = useAuth();
  const [chatUser, setChatUser] = useState<ChatUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const userId = params?.user_id as string;

  useEffect(() => {
    // Fetch user details for the breadcrumb
    const fetchUserDetails = async () => {
      if (!token || !userId) return;

      try {
        const userData = await getUserProfile(parseInt(userId), token);
        console.log(userData)
        setChatUser(userData);
      } catch (error) {
        console.error('Error fetching user details:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserDetails();
  }, [token, userId]);

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage>
                    {isLoading
                      ? 'Loading...'
                      : chatUser
                      ? `Chat with ${chatUser.full_name || chatUser.username}`
                      : 'Chat'}
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>
        {chatUser && (
          <div className="flex flex-1 flex-col">
            <ChatInterface userId={parseInt(userId)} chatUser={chatUser} />
          </div>
        )}
      </SidebarInset>
    </SidebarProvider>
  );
}
