
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Task } from '@/contexts/TaskContext';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { Edit, Trash2 } from 'lucide-react';
import { useTasks } from '@/contexts/TaskContext';

interface TaskListProps {
  tasks: Task[];
  minimal?: boolean;
  emptyMessage?: string;
}

const TaskList: React.FC<TaskListProps> = ({ 
  tasks, 
  minimal = false,
  emptyMessage = "No tasks found" 
}) => {
  const navigate = useNavigate();
  const { updateTask, deleteTask } = useTasks();

  const handleToggleComplete = async (task: Task) => {
    await updateTask(task.id, { completed: !task.completed });
  };

  const handleDelete = async (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this task?')) {
      await deleteTask(taskId);
    }
  };

  const handleEdit = (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/tasks/${taskId}`);
  };

  if (tasks.length === 0) {
    return (
      <div className="flex h-20 items-center justify-center rounded-md border border-dashed">
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="group flex items-start justify-between rounded-md border p-3 transition-colors hover:bg-muted/50"
          onClick={() => navigate(`/tasks/${task.id}`)}
        >
          <div className="flex items-start gap-3">
            <Checkbox
              checked={task.completed}
              onCheckedChange={() => handleToggleComplete(task)}
              onClick={(e) => e.stopPropagation()}
              className="mt-0.5"
            />
            <div>
              <h3 className={`font-medium ${task.completed ? 'line-through text-muted-foreground' : ''}`}>
                {task.title}
              </h3>
              
              {!minimal && task.description && (
                <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                  {task.description}
                </p>
              )}
              
              <div className="mt-2 flex flex-wrap gap-2">
                {task.due_date && (
                  <Badge variant={isOverdue(task.due_date) && !task.completed ? "destructive" : "outline"}>
                    {format(new Date(task.due_date), 'MMM d, yyyy')}
                  </Badge>
                )}
                
                {task.room_id && !minimal && (
                  <Badge variant="secondary">Room: {task.room_id}</Badge>
                )}
              </div>
            </div>
          </div>
          
          {!minimal && (
            <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              <Button variant="ghost" size="icon" onClick={(e) => handleEdit(task.id, e)}>
                <Edit className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={(e) => handleDelete(task.id, e)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// Helper to check if date is overdue
const isOverdue = (dateString: string): boolean => {
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return date < today;
};

export default TaskList;
