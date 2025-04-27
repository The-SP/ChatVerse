export const isTokenExpired = (token: string): boolean => {
  if (!token) return true;

  try {
    // Extract the payload from the JWT token
    const payload = JSON.parse(atob(token.split('.')[1]));

    // Check if the token has an expiration time
    if (!payload.exp) return false;

    // Convert exp to milliseconds and compare with current time
    const expirationTime = payload.exp * 1000;
    const currentTime = Date.now();

    return currentTime >= expirationTime;
  } catch (error) {
    console.error('Error checking token expiration:', error);
    return true;
  }
};
