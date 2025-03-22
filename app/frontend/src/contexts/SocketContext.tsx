
import React, { createContext, useContext, useState } from 'react';
import { Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  reconnect: () => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export const SocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { isAuthenticated } = useAuth();

  // This is a mock function that doesn't actually connect to any server
  const connectSocket = () => {
    console.log('Mock socket connection - not actually connecting');
    
    // For debugging purposes, we can simulate a connected state
    if (isAuthenticated) {
      console.log('Mock: User is authenticated, simulating connected state');
      setIsConnected(true);
      
      // You could simulate socket events here if needed
      // For example: setTimeout(() => toast.info('Mock: Simulated event'), 2000);
    }
    
    return null;
  };

  // Mock reconnect function
  const reconnect = () => {
    console.log('Mock socket reconnection - not actually reconnecting');
    toast.info('Mock: Attempting to reconnect socket');
    connectSocket();
  };

  return (
    <SocketContext.Provider
      value={{
        socket,
        isConnected,
        reconnect,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (context === undefined) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

// Add mock socket event emitter functions if needed
// Example:
// export const mockEmitEvent = (eventName: string, data: any) => {
//   console.log(`Mock: Emitting ${eventName} with data:`, data);
//   toast.info(`Mock: Event ${eventName} emitted`);
// };
