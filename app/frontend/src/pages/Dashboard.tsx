
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTasks } from '@/contexts/TaskContext';
import { useRooms } from '@/contexts/RoomContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckSquare, Users, Clock, Plus, ChevronRight } from 'lucide-react';
import TaskList from '@/components/task/TaskList';

const Dashboard: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { tasks, loading: tasksLoading } = useTasks();
  const { rooms, loading: roomsLoading } = useRooms();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Calculate some stats
  const completedTasks = tasks.filter(task => task.is_completed).length;
  const pendingTasks = tasks.length - completedTasks;
  const upcomingTasks = tasks.filter(task => {
    if (!task.due_date || task.is_completed) return false;
    const dueDate = new Date(task.due_date);
    const today = new Date();
    return dueDate > today && dueDate <= new Date(today.setDate(today.getDate() + 7));
  }).length;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.name || 'User'}
          </p>
        </div>
        <Button onClick={() => navigate('/tasks/new')} className="gap-2">
          <Plus className="h-4 w-4" />
          New Task
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
            <CheckSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingTasks}</div>
            <p className="text-xs text-muted-foreground">
              {completedTasks} completed, {tasks.length} total
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Rooms</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rooms.length}</div>
            <p className="text-xs text-muted-foreground">
              {rooms.length > 0 ? 'Collaborative workspaces' : 'No active rooms'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Deadlines</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingTasks}</div>
            <p className="text-xs text-muted-foreground">
              Tasks due in the next 7 days
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Recent Tasks</CardTitle>
            <CardDescription>Your most recent tasks</CardDescription>
          </CardHeader>
          <CardContent>
            {tasksLoading ? (
              <div className="flex h-40 items-center justify-center">
                <p className="text-sm text-muted-foreground">Loading tasks...</p>
              </div>
            ) : tasks.length > 0 ? (
              <TaskList 
                tasks={tasks.slice(0, 5)} 
                minimal 
                emptyMessage="No tasks found"
              />
            ) : (
              <div className="flex h-40 items-center justify-center">
                <p className="text-sm text-muted-foreground">No tasks yet</p>
              </div>
            )}
            <div className="mt-4 text-center">
              <Button variant="ghost" size="sm" onClick={() => navigate('/tasks')}>
                View all tasks
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Your Rooms</CardTitle>
            <CardDescription>Collaborative workspaces</CardDescription>
          </CardHeader>
          <CardContent>
            {roomsLoading ? (
              <div className="flex h-40 items-center justify-center">
                <p className="text-sm text-muted-foreground">Loading rooms...</p>
              </div>
            ) : rooms.length > 0 ? (
              <div className="space-y-4">
                {rooms.slice(0, 5).map(room => (
                  <div 
                    key={room.id} 
                    className="flex items-center justify-between rounded-md border p-3 text-sm transition-colors hover:bg-muted/50"
                    onClick={() => navigate(`/rooms/${room.id}`)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                        {room.name.substring(0, 1)}
                      </div>
                      <div>
                        <p className="font-medium">{room.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {room.participants.length} participants
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/rooms/${room.id}`);
                    }}>
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex h-40 flex-col items-center justify-center gap-2">
                <p className="text-sm text-muted-foreground">No rooms yet</p>
                <Button size="sm" onClick={() => navigate('/rooms')}>
                  Create a room
                </Button>
              </div>
            )}
            <div className="mt-4 text-center">
              <Button variant="ghost" size="sm" onClick={() => navigate('/rooms')}>
                View all rooms
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
