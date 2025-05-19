// Determine the appropriate API URL
const getApiBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

// Determine the WebSocket URL
const getWsBaseUrl = (): string => {
  // Convert HTTP(S) to WS(S)
  const apiUrl = getApiBaseUrl();
  if (apiUrl.startsWith('https://')) {
    return apiUrl.replace('https://', 'wss://');
  } else if (apiUrl.startsWith('http://')) {
    return apiUrl.replace('http://', 'ws://');
  }

  // Default fallback
  return 'ws://localhost:8000';
};

// Generic fetch with authentication and error handling
export const apiFetch = async <T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;

  // Set up headers
  const headers = new Headers(options.headers);

  // Add content type for non-GET requests if not already set
  if (
    options.method &&
    options.method !== 'GET' &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json');
  }

  // Add auth token if provided
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Check if the request was successful
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: 'An unknown error occurred' }));
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }

    // Parse the JSON response
    const data = await response.json();
    return data as T;
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
};

export { getApiBaseUrl, getWsBaseUrl };

// Helper functions for common API operations
export const getDirectMessages = (otherUserId: number, token: string) => {
  return apiFetch<any[]>(
    `/direct-messages/?other_user_id=${otherUserId}`,
    { method: 'GET' },
    token,
  );
};

export const sendDirectMessage = (
  content: string,
  receiverId: number,
  token: string,
) => {
  return apiFetch<any>(
    '/direct-messages/',
    {
      method: 'POST',
      body: JSON.stringify({ content, receiver_id: receiverId }),
    },
    token,
  );
};

export const markMessageAsRead = (messageId: number, token: string) => {
  return apiFetch<any>(
    `/direct-messages/${messageId}/read`,
    { method: 'PUT' },
    token,
  );
};

export const getUserConversations = (token: string) => {
  return apiFetch<any[]>(
    '/direct-messages/conversations',
    { method: 'GET' },
    token,
  );
};

export const getUserProfile = (userId: number, token: string) => {
  return apiFetch<any>(`/users/${userId}`, { method: 'GET' }, token);
};

export const getUnreadMessageCount = (token: string) => {
  return apiFetch<{ unread_count: number }>(
    '/direct-messages/unread-count',
    { method: 'GET' },
    token,
  );
};

export const searchUsers = async (
  query: string,
  token: string,
  limit: number = 10,
) => {
  if (!query || !query.trim()) {
    return [];
  }

  try {
    // Ensure query is properly sanitized and encoded
    const sanitizedQuery = encodeURIComponent(query.trim());

    const users = await apiFetch<
      Array<{
        id: number;
        username: string;
        full_name?: string;
        avatar_url?: string;
        email?: string;
      }>
    >(
      `/users/search/?query=${sanitizedQuery}&limit=${limit}`,
      { method: 'GET' },
      token,
    );

    return Array.isArray(users) ? users : [];
  } catch (error) {
    console.error('Error searching users:', error);
    // Return empty array instead of throwing to avoid breaking the UI
    return [];
  }
};
