import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRooms } from '@/contexts/RoomContext';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Clock, CopyIcon, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

const RoomDetails: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { fetchRoomById, currentRoom, loading } = useRooms();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRoom = async () => {
      if (!roomId) return;
      
      try {
        console.log('Fetching room with ID:', roomId);
        const room = await fetchRoomById(roomId);
        console.log('Fetched room:', room);

        if (!room) {
          setError('Room not found');
        }
      } catch (err) {
        console.error('Error loading room:', err);
        setError('Failed to load room details');
      }
    };
    
    loadRoom();
  }, [roomId, fetchRoomById]);

  console.log('Current state:', { loading, currentRoom, error });

  const copyInviteCode = () => {
    if (!currentRoom) return;
    
    navigator.clipboard.writeText(currentRoom.invite_code);
    toast.success('Invite code copied to clipboard');
  };

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <p className="text-muted-foreground">Loading room details...</p>
      </div>
    );
  }

  if (error || !currentRoom) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <p className="text-muted-foreground mb-4">{error || 'Room not found'}</p>
        <Button onClick={() => navigate('/rooms')}>Go back to Rooms</Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-2">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => navigate('/rooms')}
          className="mr-2"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{currentRoom.name}</h1>
          <p className="text-muted-foreground">
            {currentRoom.description || 'No description'}
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Participants ({currentRoom.participants.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {currentRoom.participants.map((participant) => (
                <div key={participant.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div 
                      className={`flex h-8 w-8 items-center justify-center rounded-full 
                      ${participant.is_online 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted text-muted-foreground'}`}
                    >
                      {participant.name.substring(0, 1)}
                    </div>
                    <div>
                      <p className="font-medium">{participant.name}</p>
                      <p className="text-sm text-muted-foreground">{participant.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <span className={`h-2 w-2 rounded-full mr-2 ${
                      participant.is_online ? 'bg-green-500' : 'bg-gray-300'
                    }`} />
                    <span className="text-sm text-muted-foreground">
                      {participant.is_online ? 'Online' : 'Offline'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Room Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Created by</p>
                <p>{currentRoom.participants.find(p => p.id === currentRoom.created_by)?.name || 'Unknown'}</p>
              </div>
              
              <div>
                <p className="text-sm font-medium text-muted-foreground">Created</p>
                <p>{formatDistanceToNow(new Date(currentRoom.created_at), { addSuffix: true })}</p>
              </div>
              
              <Separator />
              
              <div>
                <p className="text-sm font-medium text-muted-foreground">Invite Code</p>
                <div className="flex items-center justify-between mt-1">
                  <code className="bg-muted px-2 py-1 rounded font-mono">
                    {currentRoom.invite_code}
                  </code>
                  <Button variant="outline" size="icon" onClick={copyInviteCode}>
                    <CopyIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RoomDetails;
