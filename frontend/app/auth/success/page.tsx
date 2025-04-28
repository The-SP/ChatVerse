'use client';

import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

export default function AuthSuccess() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleOAuthSuccess } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const hasProcessedToken = useRef(false);

  useEffect(() => {
    const processToken = async () => {
      // Skip if we've already processed the token
      if (hasProcessedToken.current) {
        return;
      }

      const token = searchParams.get('token');

      if (!token) {
        setError('No authentication token found');
        return;
      }

      hasProcessedToken.current = true;

      try {
        await handleOAuthSuccess(token);
        // Redirect to dashboard immediately on success
        router.push('/dashboard');
      } catch (error) {
        setError(
          error instanceof Error ? error.message : 'Authentication failed',
        );
      }
    };

    processToken();
  }, []);

  // Only show error state or loading state
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            {error ? 'Authentication Failed' : 'Authenticating...'}
          </h2>

          {!error ? (
            <div className="mt-4">
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
              </div>
              <p className="mt-4 text-sm text-gray-600">
                Please wait while we complete your authentication...
              </p>
            </div>
          ) : (
            <div className="mt-4">
              <p className="text-sm text-red-600">{error}</p>
              <div className="mt-4">
                <Link
                  href="/auth/login"
                  className="text-indigo-600 hover:text-indigo-500"
                >
                  Return to login
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
