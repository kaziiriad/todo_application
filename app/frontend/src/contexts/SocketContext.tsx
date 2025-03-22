
import React, { createContext, useContext, useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
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
  const { user, isAuthenticated } = useAuth();

  const connectSocket = () => {
    if (!isAuthenticated) return;

    // Use your actual API URL here
    const socketInstance = io('http://localhost:8000', {
      auth: {
        token: localStorage.getItem('authToken'),
      },
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    setSocket(socketInstance);

    // Socket event handlers
    socketInstance.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    socketInstance.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setIsConnected(false);
    });

    // Event handlers for task-related events
    socketInstance.on('task_created', (data) => {
      toast.info(`New task created: ${data.title}`);
    });

    socketInstance.on('task_updated', (data) => {
      toast.info(`Task updated: ${data.title}`);
    });

    socketInstance.on('task_deleted', (data) => {
      toast.info(`Task deleted: ID ${data.id}`);
    });

    // Event handlers for room-related events
    socketInstance.on('room_created', (data) => {
      toast.info(`New room created: ${data.name}`);
    });

    socketInstance.on('participant_joined', (data) => {
      toast.info(`${data.user_name} joined the room`);
    });

    socketInstance.on('user_disconnected', (data) => {
      toast.info(`${data.user_name} disconnected`);
    });

    socketInstance.on('room_joined', (data) => {
      toast.success(`You joined room: ${data.room_name}`);
    });

    return socketInstance;
  };

  useEffect(() => {
    let socketInstance: Socket | null = null;
    
    if (isAuthenticated) {
      socketInstance = connectSocket();
    }

    return () => {
      if (socketInstance) {
        socketInstance.disconnect();
      }
    };
  }, [isAuthenticated, user?.id]);

  const reconnect = () => {
    if (socket) {
      socket.disconnect();
    }
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
