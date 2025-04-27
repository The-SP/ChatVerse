'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Public routes that don't require authentication
    const publicRoutes = ['/auth/login', '/auth/register', '/auth/success'];

    // Check if the current route is a public route
    const isPublicRoute = publicRoutes.some((route) =>
      pathname?.startsWith(route),
    );

    if (!isLoading) {
      if (isAuthenticated && isPublicRoute) {
        // If user is authenticated and trying to access a public route,
        // redirect them to the dashboard
        router.push('/dashboard');
      } else if (!isAuthenticated && !isPublicRoute) {
        // If user is not authenticated and trying to access a protected route,
        // redirect them to the login page
        router.push('/auth/login');
      }
      setIsChecking(false);
    }
  }, [isAuthenticated, isLoading, router, pathname]);

  if (isLoading || isChecking) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="mt-4 text-lg">Loading...</p>
      </div>
    );
  }

  return <>{children}</>;
}
