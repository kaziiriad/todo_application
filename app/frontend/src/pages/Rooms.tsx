
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useRooms } from '@/contexts/RoomContext';
import { Button } from '@/components/ui/button';
import { Plus, Users, Link as LinkIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import CreateRoomForm from '@/components/room/CreateRoomForm';
import JoinRoomForm from '@/components/room/JoinRoomForm';
import { toast } from 'sonner';
import { Separator } from '@/components/ui/separator';

const Rooms: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { rooms, loading } = useRooms();
  const navigate = useNavigate();
  
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [joinDialogOpen, setJoinDialogOpen] = React.useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  const copyInviteCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success('Invite code copied to clipboard');
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rooms</h1>
          <p className="text-muted-foreground">
            Collaborative workspaces for your team
          </p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 flex-1 sm:flex-none">
                <Plus className="h-4 w-4" />
                Create Room
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create a new room</DialogTitle>
              </DialogHeader>
              <CreateRoomForm onSuccess={() => setCreateDialogOpen(false)} />
            </DialogContent>
          </Dialog>
          
          <Dialog open={joinDialogOpen} onOpenChange={setJoinDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2 flex-1 sm:flex-none">
                <Users className="h-4 w-4" />
                Join Room
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Join a room</DialogTitle>
              </DialogHeader>
              <JoinRoomForm onSuccess={() => setJoinDialogOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <p className="text-muted-foreground">Loading rooms...</p>
        </div>
      ) : rooms.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {rooms.map((room) => (
            <Card key={room.id} className="overflow-hidden hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <CardTitle className="text-xl">{room.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {room.description || 'No description'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium mb-1">Participants</p>
                    <div className="flex -space-x-2">
                      {room.participants.slice(0, 5).map((participant, index) => (
                        <div
                          key={participant.id}
                          className={`flex h-8 w-8 items-center justify-center rounded-full border-2 border-background ${
                            participant.is_online ? 'bg-primary text-primary-foreground' : 'bg-muted'
                          }`}
                          title={participant.name}
                        >
                          {participant.name.substring(0, 1)}
                        </div>
                      ))}
                      {room.participants.length > 5 && (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-background bg-muted text-xs">
                          +{room.participants.length - 5}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div className="flex items-center justify-between">
                    <div className="text-sm flex items-center">
                      <span className="text-muted-foreground mr-2">Invite code:</span>
                      <span className="font-mono">{room.invite_code}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyInviteCode(room.invite_code)}
                    >
                      <LinkIcon className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <Button
                    className="w-full"
                    onClick={() => navigate(`/rooms/${room.id}`)}
                  >
                    Enter Room
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 border border-dashed rounded-lg">
          <p className="text-muted-foreground mb-4">You haven't created or joined any rooms yet</p>
          <div className="flex gap-2">
            <Button onClick={() => setCreateDialogOpen(true)}>Create your first room</Button>
            <Button variant="outline" onClick={() => setJoinDialogOpen(true)}>Join a room</Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Rooms;
