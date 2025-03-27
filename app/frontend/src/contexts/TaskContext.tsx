
import React, { createContext, useContext } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Task, 
  fetchTasks, 
  createTask, 
  updateTask, 
  deleteTask 
} from '../services/taskService';

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

  // Wrap API calls with error handling
  const fetchTasksWithErrorHandling = async (roomId?: string): Promise<Task[]> => {
    if (!isAuthenticated) return [];
    
    try {
      return await fetchTasks(roomId);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      toast.error('Failed to fetch tasks');
      throw err;
    }
  };

  const createTaskWithErrorHandling = async (taskData: Partial<Task>): Promise<Task> => {
    try {
      const result = await createTask(taskData);
      toast.success('Task created successfully');
      return result;
    } catch (err) {
      console.error('Error creating task:', err);
      toast.error('Failed to create task');
      throw err;
    }
  };

  const updateTaskWithErrorHandling = async (taskId: string, updates: Partial<Task>): Promise<Task> => {
    try {
      const result = await updateTask(taskId, updates);
      toast.success('Task updated successfully');
      return result;
    } catch (err) {
      console.error('Error updating task:', err);
      toast.error('Failed to update task');
      throw err;
    }
  };

  const deleteTaskWithErrorHandling = async (taskId: string): Promise<void> => {
    try {
      await deleteTask(taskId);
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
    queryFn: () => fetchTasksWithErrorHandling(),
    enabled: isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 30000, // Poll every 30 seconds to keep data fresh without sockets
  });

  // Set up mutations
  const createTaskMutation = useMutation({
    mutationFn: createTaskWithErrorHandling,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, updates }: { taskId: string; updates: Partial<Task> }) => 
      updateTaskWithErrorHandling(taskId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const deleteTaskMutation = useMutation({
    mutationFn: deleteTaskWithErrorHandling,
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
        fetchTasks: fetchTasksWithErrorHandling,
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

// Custom hook to use the task context
export const useTask = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTask must be used within a TaskProvider');
  }
  return context;
};

export const useTasks = useTask; // Alias for backward compatibility

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
