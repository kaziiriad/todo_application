
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { useSocket } from './SocketContext';
import { toast } from 'sonner';

export interface Participant {
  id: string;
  name: string;
  email: string;
  is_online: boolean;
  joined_at: string;
}

export interface Room {
  id: string;
  name: string;
  description: string;
  invite_code: string;
  created_at: string;
  created_by: string;
  participants: Participant[];
}

interface RoomContextType {
  rooms: Room[];
  currentRoom: Room | null;
  loading: boolean;
  error: string | null;
  fetchRooms: () => Promise<void>;
  fetchRoomById: (roomId: string) => Promise<Room | null>;
  createRoom: (roomData: { name: string; description: string }) => Promise<Room>;
  joinRoom: (inviteCode: string) => Promise<Room>;
  setCurrentRoom: (room: Room | null) => void;
  onlineParticipants: Participant[];
}

const RoomContext = createContext<RoomContextType | undefined>(undefined);

// Mock data for demonstration purposes
const MOCK_ROOMS: Room[] = [
  {
    id: '1',
    name: 'Project Alpha',
    description: 'Main project planning and task tracking',
    invite_code: 'ALPHA123',
    created_at: '2023-11-01T10:00:00Z',
    created_by: '1',
    participants: [
      {
        id: '1',
        name: 'Demo User',
        email: 'demo@example.com',
        is_online: true,
        joined_at: '2023-11-01T10:00:00Z',
      },
      {
        id: '2',
        name: 'John Doe',
        email: 'john@example.com',
        is_online: false,
        joined_at: '2023-11-02T14:30:00Z',
      },
    ],
  },
  {
    id: '2',
    name: 'Marketing Campaign',
    description: 'Q4 marketing campaign planning and execution',
    invite_code: 'MARKET456',
    created_at: '2023-11-05T09:15:00Z',
    created_by: '1',
    participants: [
      {
        id: '1',
        name: 'Demo User',
        email: 'demo@example.com',
        is_online: true,
        joined_at: '2023-11-05T09:15:00Z',
      },
      {
        id: '3',
        name: 'Jane Smith',
        email: 'jane@example.com',
        is_online: true,
        joined_at: '2023-11-05T10:20:00Z',
      },
    ],
  },
];

export const RoomProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [currentRoom, setCurrentRoom] = useState<Room | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, user } = useAuth();
  const { socket, isConnected } = useSocket();

  // Compute online participants
  const onlineParticipants = currentRoom?.participants.filter(p => p.is_online) || [];

  // Fetch all rooms the user belongs to
  const fetchRooms = async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 800));
      setRooms(MOCK_ROOMS);
    } catch (err) {
      console.error('Error fetching rooms:', err);
      setError('Failed to fetch rooms. Please try again later.');
      toast.error('Failed to fetch rooms');
    } finally {
      setLoading(false);
    }
  };

  // Fetch a specific room by ID
  const fetchRoomById = async (roomId: string): Promise<Room | null> => {
    setLoading(true);
    setError(null);
    
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const room = MOCK_ROOMS.find(r => r.id === roomId) || null;
      if (room) {
        setCurrentRoom(room);
      }
      return room;
    } catch (err) {
      console.error('Error fetching room:', err);
      setError('Failed to fetch room details');
      toast.error('Failed to fetch room details');
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Create a new room
  const createRoom = async (roomData: { name: string; description: string }): Promise<Room> => {
    setLoading(true);
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 700));
      
      const newRoom: Room = {
        id: Date.now().toString(),
        name: roomData.name,
        description: roomData.description,
        invite_code: `INVITE${Math.floor(Math.random() * 10000)}`,
        created_at: new Date().toISOString(),
        created_by: user?.id || '1',
        participants: [
          {
            id: user?.id || '1',
            name: user?.name || 'Demo User',
            email: user?.email || 'demo@example.com',
            is_online: true,
            joined_at: new Date().toISOString(),
          }
        ],
      };
      
      // Optimistic update
      setRooms(prev => [...prev, newRoom]);
      toast.success('Room created successfully');
      
      return newRoom;
    } catch (err) {
      console.error('Error creating room:', err);
      toast.error('Failed to create room');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Join a room using invite code
  const joinRoom = async (inviteCode: string): Promise<Room> => {
    setLoading(true);
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 700));
      
      // Find room by invite code (mock implementation)
      const room = MOCK_ROOMS.find(r => r.invite_code === inviteCode);
      
      if (!room) {
        throw new Error('Invalid invite code');
      }
      
      // Check if user is already a participant
      const isParticipant = room.participants.some(p => p.id === (user?.id || '1'));
      
      if (!isParticipant) {
        // Add current user as participant
        const updatedRoom: Room = {
          ...room,
          participants: [
            ...room.participants,
            {
              id: user?.id || '1',
              name: user?.name || 'Demo User',
              email: user?.email || 'demo@example.com',
              is_online: true,
              joined_at: new Date().toISOString(),
            }
          ],
        };
        
        // Update rooms list
        setRooms(prev => prev.map(r => r.id === room.id ? updatedRoom : r));
        toast.success(`Joined room: ${room.name}`);
        setCurrentRoom(updatedRoom);
        return updatedRoom;
      }
      
      toast.info(`You are already a member of: ${room.name}`);
      setCurrentRoom(room);
      return room;
    } catch (err) {
      console.error('Error joining room:', err);
      toast.error('Failed to join room. Invalid invite code.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Listen for socket events
  useEffect(() => {
    if (!isConnected || !socket) return;

    const handleRoomCreated = (data: Room) => {
      setRooms(prev => [...prev, data]);
    };

    const handleParticipantJoined = (data: { room_id: string; user: Participant }) => {
      setRooms(prev => prev.map(room => {
        if (room.id === data.room_id) {
          return {
            ...room,
            participants: [...room.participants, data.user],
          };
        }
        return room;
      }));

      // Update current room if needed
      if (currentRoom?.id === data.room_id) {
        setCurrentRoom(prev => {
          if (!prev) return null;
          return {
            ...prev,
            participants: [...prev.participants, data.user],
          };
        });
      }
    };

    const handleUserDisconnected = (data: { room_id: string; user_id: string }) => {
      setRooms(prev => prev.map(room => {
        if (room.id === data.room_id) {
          return {
            ...room,
            participants: room.participants.map(p => 
              p.id === data.user_id ? { ...p, is_online: false } : p
            ),
          };
        }
        return room;
      }));

      // Update current room if needed
      if (currentRoom?.id === data.room_id) {
        setCurrentRoom(prev => {
          if (!prev) return null;
          return {
            ...prev,
            participants: prev.participants.map(p => 
              p.id === data.user_id ? { ...p, is_online: false } : p
            ),
          };
        });
      }
    };

    // Register socket event listeners
    socket.on('room_created', handleRoomCreated);
    socket.on('participant_joined', handleParticipantJoined);
    socket.on('user_disconnected', handleUserDisconnected);

    return () => {
      // Clean up event listeners
      socket.off('room_created', handleRoomCreated);
      socket.off('participant_joined', handleParticipantJoined);
      socket.off('user_disconnected', handleUserDisconnected);
    };
  }, [socket, isConnected, currentRoom]);

  // Auto fetch rooms when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchRooms();
    } else {
      setRooms([]);
      setCurrentRoom(null);
    }
  }, [isAuthenticated]);

  return (
    <RoomContext.Provider
      value={{
        rooms,
        currentRoom,
        loading,
        error,
        fetchRooms,
        fetchRoomById,
        createRoom,
        joinRoom,
        setCurrentRoom,
        onlineParticipants,
      }}
    >
      {children}
    </RoomContext.Provider>
  );
};

export const useRooms = () => {
  const context = useContext(RoomContext);
  if (context === undefined) {
    throw new Error('useRooms must be used within a RoomProvider');
  }
  return context;
};
