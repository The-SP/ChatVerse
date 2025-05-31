'use client';

import { ReactNode } from 'react';
import { ChatProvider } from '@/contexts/ChatContext';

export default function MainLayout({ children }: { children: ReactNode }) {
  return <ChatProvider>{children}</ChatProvider>;
}
