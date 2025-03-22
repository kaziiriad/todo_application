
import React from 'react';
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
import { Textarea } from '@/components/ui/textarea';
import { useRooms } from '@/contexts/RoomContext';
import { useNavigate } from 'react-router-dom';

const roomSchema = z.object({
  name: z.string().min(3, 'Room name must be at least 3 characters'),
  description: z.string().optional(),
});

type RoomFormValues = z.infer<typeof roomSchema>;

interface CreateRoomFormProps {
  onSuccess?: () => void;
}

const CreateRoomForm: React.FC<CreateRoomFormProps> = ({ onSuccess }) => {
  const { createRoom, loading } = useRooms();
  const navigate = useNavigate();

  const form = useForm<RoomFormValues>({
    resolver: zodResolver(roomSchema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  const onSubmit = async (data: RoomFormValues) => {
    try {
      const newRoom = await createRoom({
        name: data.name,
        description: data.description || '',
      });
      
      if (onSuccess) {
        onSuccess();
      }
      
      navigate(`/rooms/${newRoom.id}`);
    } catch (error) {
      console.error('Error creating room:', error);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Room Name</FormLabel>
              <FormControl>
                <Input placeholder="Project Alpha" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description (optional)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="What is this room for?"
                  className="resize-none"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Creating...' : 'Create Room'}
        </Button>
      </form>
    </Form>
  );
};

export default CreateRoomForm;
