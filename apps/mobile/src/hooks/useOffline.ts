/**
 * Hook for monitoring online/offline status.
 */
import { useState, useEffect } from 'react';
import NetInfo from '@react-native-community/netinfo';

interface UseOfflineResult {
  isOnline: boolean;
  isOffline: boolean;
}

export function useOffline(): UseOfflineResult {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsOnline(state.isConnected ?? false);
    });
    return () => unsubscribe();
  }, []);

  return { isOnline, isOffline: !isOnline };
}
