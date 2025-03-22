
import React, { createContext, useContext } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// API base URL - should be configured based on your environment
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Task {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  due_date: string | null;
  room_id: string | null;
  created_at: string;
  updated_at: string;
  // created_by: string;
}

interface TaskContextType {
  tasks: Task[];
  loading: boolean;
  error: Error | null;
  fetchTasks: (roomId?: string) => Promise<Task[]>;
  createTask: (task: Partial<Task>) => Promise<Task>;
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<Task>;
  deleteTask: (taskId: string) => Promise<void>;
  getTaskById: (taskId: string) => Task | undefined;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);


export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  // Fetch tasks from API
  const fetchTasks = async (roomId?: string): Promise<Task[]> => {
    if (!isAuthenticated) return [];
    
    try {
      const url = roomId 
        ? `${API_URL}/tasks/?room_id=${roomId}`
        : `${API_URL}/tasks/`;
      
      const response = await axios.get(url);
      return response.data;
    } catch (err) {
      console.error('Error fetching tasks:', err);
      toast.error('Failed to fetch tasks');
      throw err;
    }
  };

  // Create a new task
  const createTask = async (taskData: Partial<Task>): Promise<Task> => {
    try {
      const response = await axios.post(`${API_URL}/tasks/`, taskData);
      toast.success('Task created successfully');
      return response.data;
    } catch (err) {
      console.error('Error creating task:', err);
      toast.error('Failed to create task');
      throw err;
    }
  };

  // Update existing task
  const updateTask = async (taskId: string, updates: Partial<Task>): Promise<Task> => {
    try {
      const response = await axios.patch(`${API_URL}/tasks/${taskId}`, updates);
      toast.success('Task updated successfully');
      return response.data;
    } catch (err) {
      console.error('Error updating task:', err);
      toast.error('Failed to update task');
      throw err;
    }
  };

  // Delete a task
  const deleteTask = async (taskId: string): Promise<void> => {
    try {
      await axios.delete(`${API_URL}/tasks/${taskId}`);
      toast.success('Task deleted successfully');
    } catch (err) {
      console.error('Error deleting task:', err);
      toast.error('Failed to delete task');
      throw err;
    }
  };

  // Get task by ID
  const getTaskById = (taskId: string): Task | undefined => {
    return tasks.find(task => task.id === taskId);
  };

  // Use React Query to manage tasks data
  const { 
    data: tasks = [], 
    isLoading: loading, 
    error 
  } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => fetchTasks(),
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 30000, // Poll every 30 seconds to keep data fresh without sockets
  });

  // Set up mutations
  const createTaskMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, updates }: { taskId: string; updates: Partial<Task> }) => 
      updateTask(taskId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const deleteTaskMutation = useMutation({
    mutationFn: deleteTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Socket implementation is completely removed
  // To add it back later, see the commented code below


  return (
    <TaskContext.Provider
      value={{
        tasks,
        loading,
        error,
        fetchTasks,
        createTask: createTaskMutation.mutateAsync,
        updateTask: (taskId, updates) => updateTaskMutation.mutateAsync({ taskId, updates }),
        deleteTask: deleteTaskMutation.mutateAsync,
        getTaskById,
      }}
    >
      {children}
    </TaskContext.Provider>
  );
};

// Export both hook names for backward compatibility
export const useTasks = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  return context;
};

export const useTask = useTasks; // Alias for compatibility

/* 
// Socket implementation for future use:

import { useSocket } from './SocketContext';

// Inside the TaskProvider component:
const { socket, isConnected } = useSocket();

// Add this useEffect to handle socket events:
useEffect(() => {
  if (!isConnected || !socket) return;

  const handleTaskCreated = (data: Task) => {
    // Update the cache with the new task
    queryClient.setQueryData(['tasks'], (oldData: Task[] | undefined) => {
      return oldData ? [...oldData, data] : [data];
    });
    toast.info(`New task created: ${data.title}`);
  };

  const handleTaskUpdated = (data: Task) => {
    // Update the cache with the updated task
    queryClient.setQueryData(['tasks'], (oldData: Task[] | undefined) => {
      return oldData 
        ? oldData.map(task => task.id === data.id ? data : task)
        : [data];
    });
    toast.info(`Task updated: ${data.title}`);
  };

  const handleTaskDeleted = (data: { id: string }) => {
    // Update the cache by removing the deleted task
    queryClient.setQueryData(['tasks'], (oldData: Task[] | undefined) => {
      return oldData 
        ? oldData.filter(task => task.id !== data.id)
        : [];
    });
    toast.info(`Task deleted`);
  };

  // Register socket event listeners
  socket.on('task_created', handleTaskCreated);
  socket.on('task_updated', handleTaskUpdated);
  socket.on('task_deleted', handleTaskDeleted);

  return () => {
    // Clean up event listeners
    socket.off('task_created', handleTaskCreated);
    socket.off('task_updated', handleTaskUpdated);
    socket.off('task_deleted', handleTaskDeleted);
  };
}, [socket, isConnected, queryClient]);
*/
