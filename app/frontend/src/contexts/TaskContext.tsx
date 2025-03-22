
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { useSocket } from './SocketContext';
import { toast } from 'sonner';

export interface Task {
  id: string;
  title: string;
  description: string;
  is_completed: boolean;
  due_date: string | null;
  room_id: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface TaskContextType {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  fetchTasks: (roomId?: string) => Promise<void>;
  createTask: (task: Partial<Task>) => Promise<Task>;
  updateTask: (taskId: string, updates: Partial<Task>) => Promise<Task>;
  deleteTask: (taskId: string) => Promise<void>;
  getTaskById: (taskId: string) => Task | undefined;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

// Mock data for demonstration purposes
const MOCK_TASKS: Task[] = [
  {
    id: '1',
    title: 'Complete project documentation',
    description: 'Write comprehensive documentation for the project',
    is_completed: false,
    due_date: '2023-12-31',
    room_id: '1',
    created_at: '2023-11-15T10:00:00Z',
    updated_at: '2023-11-15T10:00:00Z',
    created_by: '1',
  },
  {
    id: '2',
    title: 'Design user interface',
    description: 'Create wireframes and UI design for all screens',
    is_completed: true,
    due_date: '2023-11-20',
    room_id: '1',
    created_at: '2023-11-10T09:00:00Z',
    updated_at: '2023-11-15T11:30:00Z',
    created_by: '1',
  },
  {
    id: '3',
    title: 'Setup development environment',
    description: 'Install and configure all necessary tools and libraries',
    is_completed: true,
    due_date: null,
    room_id: '2',
    created_at: '2023-11-05T14:00:00Z',
    updated_at: '2023-11-06T15:45:00Z',
    created_by: '1',
  },
];

export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();
  const { socket, isConnected } = useSocket();

  // Fetch tasks from API
  const fetchTasks = async (roomId?: string) => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Filter mock tasks by room if provided
      const filteredTasks = roomId 
        ? MOCK_TASKS.filter(task => task.room_id === roomId)
        : MOCK_TASKS;
        
      setTasks(filteredTasks);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Failed to fetch tasks. Please try again later.');
      toast.error('Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  // Create a new task
  const createTask = async (taskData: Partial<Task>): Promise<Task> => {
    setLoading(true);
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const newTask: Task = {
        id: Date.now().toString(),
        title: taskData.title || '',
        description: taskData.description || '',
        is_completed: taskData.is_completed || false,
        due_date: taskData.due_date || null,
        room_id: taskData.room_id || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        created_by: '1', // Current user ID would come from auth context
      };
      
      // Optimistic update - add to local state immediately
      setTasks(prev => [...prev, newTask]);
      toast.success('Task created successfully');
      
      return newTask;
    } catch (err) {
      console.error('Error creating task:', err);
      toast.error('Failed to create task');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Update existing task
  const updateTask = async (taskId: string, updates: Partial<Task>): Promise<Task> => {
    setLoading(true);
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Optimistic update
      const updatedTasks = tasks.map(task => 
        task.id === taskId ? { ...task, ...updates, updated_at: new Date().toISOString() } : task
      );
      
      setTasks(updatedTasks);
      
      const updatedTask = updatedTasks.find(task => task.id === taskId);
      if (!updatedTask) throw new Error('Task not found');
      
      toast.success('Task updated successfully');
      return updatedTask;
    } catch (err) {
      console.error('Error updating task:', err);
      toast.error('Failed to update task');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Delete a task
  const deleteTask = async (taskId: string): Promise<void> => {
    setLoading(true);
    try {
      // In production, make an actual API call here
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Optimistic update
      setTasks(prev => prev.filter(task => task.id !== taskId));
      toast.success('Task deleted successfully');
    } catch (err) {
      console.error('Error deleting task:', err);
      toast.error('Failed to delete task');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Get task by ID
  const getTaskById = (taskId: string): Task | undefined => {
    return tasks.find(task => task.id === taskId);
  };

  // Listen for socket events
  useEffect(() => {
    if (!isConnected || !socket) return;

    const handleTaskCreated = (data: Task) => {
      setTasks(prev => [...prev, data]);
    };

    const handleTaskUpdated = (data: Task) => {
      setTasks(prev => prev.map(task => task.id === data.id ? data : task));
    };

    const handleTaskDeleted = (data: { id: string }) => {
      setTasks(prev => prev.filter(task => task.id !== data.id));
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
  }, [socket, isConnected]);

  // Auto fetch tasks when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchTasks();
    }
  }, [isAuthenticated]);

  return (
    <TaskContext.Provider
      value={{
        tasks,
        loading,
        error,
        fetchTasks,
        createTask,
        updateTask,
        deleteTask,
        getTaskById,
      }}
    >
      {children}
    </TaskContext.Provider>
  );
};

export const useTasks = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTasks must be used within a TaskProvider');
  }
  return context;
};
