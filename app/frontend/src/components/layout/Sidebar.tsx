
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, CheckSquare, Users, Plus, ChevronRight, Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useRooms } from '@/contexts/RoomContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import CreateRoomForm from '@/components/room/CreateRoomForm';
import JoinRoomForm from '@/components/room/JoinRoomForm';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isJoinDialogOpen, setIsJoinDialogOpen] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { rooms } = useRooms();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const toggleMobileSidebar = () => {
    setIsMobileOpen(!isMobileOpen);
  };

  const navItems = [
    {
      name: 'Dashboard',
      path: '/',
      icon: <Home className="h-5 w-5" />,
    },
    {
      name: 'My Tasks',
      path: '/tasks',
      icon: <CheckSquare className="h-5 w-5" />,
    },
    // {
    //   name: 'Rooms',
    //   path: '/rooms',
    //   icon: <Users className="h-5 w-5" />,
    // },
  ];

  return (
    <>
      {/* Mobile Menu Toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-50 md:hidden"
        onClick={toggleMobileSidebar}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile Sidebar */}
      <div
        className={cn(
          "fixed inset-0 z-40 transform bg-background/80 backdrop-blur-sm transition-all duration-300 md:hidden",
          isMobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={toggleMobileSidebar}
      />

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r bg-background transition-all duration-300 md:static",
          isCollapsed ? "md:w-16" : "md:w-64",
          isMobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-4">
          <Link to="/" className="flex items-center">
            {!isCollapsed ? (
              <span className="text-xl font-semibold">TaskVerse</span>
            ) : (
              <span className="text-xl font-semibold">TV</span>
            )}
          </Link>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleMobileSidebar}
              className="md:hidden"
            >
              <X className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="hidden md:flex"
            >
              <ChevronRight
                className={cn(
                  "h-5 w-5 transition-transform",
                  isCollapsed ? "rotate-0" : "rotate-180"
                )}
              />
            </Button>
          </div>
        </div>

        <nav className="flex flex-1 flex-col overflow-y-auto p-3">
          <ul className="flex flex-1 flex-col gap-1">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={cn(
                    "group flex items-center rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground focus-ring",
                    location.pathname === item.path
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {item.icon}
                  {!isCollapsed && <span className="ml-3">{item.name}</span>}
                </Link>
              </li>
            ))}
          </ul>

          <Separator className="my-4" />

          {/* <div className="space-y-2">
            {!isCollapsed && <p className="px-3 text-xs font-semibold text-muted-foreground">Rooms</p>}
            
            <ul className="grid gap-1">
              {rooms.map((room) => (
                <li key={room.id}>
                  <Link
                    to={`/rooms/${room.id}`}
                    className={cn(
                      "group flex items-center rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground",
                      location.pathname === `/rooms/${room.id}`
                        ? "bg-accent text-accent-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    <span className="mr-3 flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 text-primary">
                      {room.name.substring(0, 1)}
                    </span>
                    {!isCollapsed && <span>{room.name}</span>}
                  </Link>
                </li>
              ))}
            </ul>
          </div> */}

          {/* <div className="mt-auto pt-4">
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className={cn("w-full", isCollapsed ? "px-2" : "")}>
                  <Plus className="h-4 w-4" />
                  {!isCollapsed && <span className="ml-2">New Room</span>}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create a new room</DialogTitle>
                </DialogHeader>
                <CreateRoomForm onSuccess={() => setIsCreateDialogOpen(false)} />
              </DialogContent>
            </Dialog>

            <Dialog open={isJoinDialogOpen} onOpenChange={setIsJoinDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="ghost" className={cn("mt-2 w-full", isCollapsed ? "px-2" : "")}>
                  <Users className="h-4 w-4" />
                  {!isCollapsed && <span className="ml-2">Join Room</span>}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Join a room</DialogTitle>
                </DialogHeader>
                <JoinRoomForm onSuccess={() => setIsJoinDialogOpen(false)} />
              </DialogContent>
            </Dialog>
          </div> */}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;
