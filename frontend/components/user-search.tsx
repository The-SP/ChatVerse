'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Search } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { searchUsers } from '@/lib/api';
import { SearchUser } from '@/lib/types';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

export function UserSearch() {
  const { token } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState<SearchUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch users based on search query
  useEffect(() => {
    // If search query is empty, clear users and return early
    if (!token || !searchQuery.trim()) {
      setUsers([]);
      setIsLoading(false);
      return;
    }

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Set a new timeout to debounce the search
    searchTimeoutRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await searchUsers(searchQuery, token);
        console.log('Search results:', data);
        console.log('Search results length:', data.length);
        // Check the data structure
        if (data && data.length > 0) {
          console.log('First user:', data[0]);
        }
        setUsers(data || []);
      } catch (error) {
        console.error('Error searching users:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, token]);

  const handleUserSelect = (userId: number) => {
    router.push(`/chat/${userId}`);
    setOpen(false);
    setSearchQuery('');
  };

  // Get initials for avatar fallback
  const getInitials = (name: string) => {
    return name.charAt(0).toUpperCase();
  };

  return (
    <div className="px-2 pb-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className="w-full justify-start gap-2 text-sm font-normal"
          >
            <Search className="h-4 w-4" />
            <span className="text-muted-foreground">Search users...</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0" align="start" sideOffset={5}>
          <Command className="w-[250px]">
            <CommandInput
              placeholder="Search users..."
              value={searchQuery}
              onValueChange={(value) => {
                console.log('Search query changed:', value);
                setSearchQuery(value);
              }}
              className="h-9"
            />
            <CommandList>
              <CommandEmpty>
                {isLoading
                  ? 'Searching...'
                  : users && users.length === 0
                  ? 'No users found'
                  : 'Try typing a name or username'}
              </CommandEmpty>
              <CommandGroup>
                {users &&
                  users.length > 0 &&
                  users.map((user) => (
                    <CommandItem
                      key={user.id}
                      onSelect={() => handleUserSelect(user.id)}
                      className="flex items-center gap-2 py-2"
                      value={`${user.username} ${user.full_name || ''}`}
                    >
                      <Avatar className="h-6 w-6">
                        {user.avatar_url ? (
                          <AvatarImage
                            src={user.avatar_url}
                            alt={user.username}
                          />
                        ) : (
                          <AvatarFallback className="text-xs">
                            {getInitials(user.full_name || user.username)}
                          </AvatarFallback>
                        )}
                      </Avatar>
                      <span>{user.full_name || user.username}</span>
                    </CommandItem>
                  ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
