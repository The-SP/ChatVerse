'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl">Dashboard</CardTitle>
          <CardDescription>Welcome to your dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-xl font-medium">User Profile</h2>
              {user ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">
                      Username
                    </p>
                    <p>{user.username}</p>
                  </div>
                  {user.email && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Email</p>
                      <p>{user.email}</p>
                    </div>
                  )}
                  {user.full_name && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Full Name
                      </p>
                      <p>{user.full_name}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p>Loading user information...</p>
              )}
            </div>

            <div className="pt-4">
              <Button onClick={logout} variant="destructive">
                Logout
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
