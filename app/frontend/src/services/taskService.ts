import axios from 'axios';
import API_URL from '../config/api';

// Task type definition
export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
  room_id?: string;
  user_id?: string;
}

// Fetch all tasks
export const fetchTasks = async (roomId?: string): Promise<Task[]> => {
  const url = roomId 
    ? `${API_URL}/?room_id=${roomId}`
    : `${API_URL}/`;
  
  const response = await axios.get(url);
  return response.data;
};

// Create a new task
export const createTask = async (taskData: Partial<Task>): Promise<Task> => {
  const response = await axios.post(`${API_URL}/`, taskData);
  return response.data;
};

// Update an existing task
export const updateTask = async (taskId: string, updates: Partial<Task>): Promise<Task> => {
  const response = await axios.patch(`${API_URL}/${taskId}`, updates);
  return response.data;
};

// Delete a task
export const deleteTask = async (taskId: string): Promise<void> => {
  await axios.delete(`${API_URL}/${taskId}`);
};