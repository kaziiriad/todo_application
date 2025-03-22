
import React, { useState } from 'react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { useRooms } from '@/contexts/RoomContext';
import { useNavigate } from 'react-router-dom';

const joinRoomSchema = z.object({
  inviteCode: z.string().min(4, 'Invite code must be at least 4 characters'),
});

type JoinRoomFormValues = z.infer<typeof joinRoomSchema>;

interface JoinRoomFormProps {
  onSuccess?: () => void;
}

const JoinRoomForm: React.FC<JoinRoomFormProps> = ({ onSuccess }) => {
  const { joinRoom, loading } = useRooms();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const form = useForm<JoinRoomFormValues>({
    resolver: zodResolver(joinRoomSchema),
    defaultValues: {
      inviteCode: '',
    },
  });

  const onSubmit = async (data: JoinRoomFormValues) => {
    try {
      setError(null);
      const room = await joinRoom(data.inviteCode);
      
      if (onSuccess) {
        onSuccess();
      }
      
      navigate(`/rooms/${room.id}`);
    } catch (err) {
      console.error('Error joining room:', err);
      setError('Invalid invite code or room not found');
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="inviteCode"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Invite Code</FormLabel>
              <FormControl>
                <Input placeholder="Enter invite code" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Joining...' : 'Join Room'}
        </Button>
      </form>
    </Form>
  );
};

export default JoinRoomForm;
