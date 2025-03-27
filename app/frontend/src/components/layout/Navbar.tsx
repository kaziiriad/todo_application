
import React, { useState, useEffect } from 'react';
import { Bell, User, ChevronDown } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [checkingConnection, setCheckingConnection] = useState(true);
  
  // API URL from environment variables or default to localhost
  // const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const BACKEND_URL = import.meta.env.BACKEND_URL || 'http://localhost:8000';
  
  // Check backend connection status
  useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        // Try to connect to the backend health endpoint
        const response = await axios.get(`/health`, { timeout: 5000 });
        setIsBackendConnected(response.status === 200);
      } catch (error) {
        console.error('Backend connection check failed:', error);
        setIsBackendConnected(false);
      } finally {
        setCheckingConnection(false);
      }
    };

    // Check connection immediately
    checkBackendConnection();

    // Set up periodic connection checks
    const intervalId = setInterval(checkBackendConnection, 30000); // Check every 30 seconds

    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase();
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between py-4">
        <div className="flex items-center gap-2">
          <div className="text-sm text-muted-foreground">
            {checkingConnection ? (
              <span className="flex items-center">
                <span className="mr-2 h-2 w-2 rounded-full bg-yellow-500 animate-pulse"></span>
                Checking...
              </span>
            ) : isBackendConnected ? (
              <span className="flex items-center">
                <span className="mr-2 h-2 w-2 rounded-full bg-green-500"></span>
                Connected
              </span>
            ) : (
              <span className="flex items-center">
                <span className="mr-2 h-2 w-2 rounded-full bg-red-500"></span>
                Disconnected
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] text-primary-foreground">
              3
            </span>
          </Button>

          {/* <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{user?.name ? getInitials(user.name) : 'U'}</AvatarFallback>
                </Avatar>
                <div className="flex items-center gap-1 text-sm font-medium">
                  {user?.name || 'User'}
                  <ChevronDown className="h-4 w-4 opacity-50" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="flex items-center justify-start gap-2 p-2">
                <div className="flex flex-col space-y-1 leading-none">
                  <p className="font-medium">{user?.name || 'User'}</p>
                  <p className="text-xs text-muted-foreground">{user?.email || 'user@example.com'}</p>
                </div>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <a href="/profile" className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile</span>
                </a>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="cursor-pointer text-red-600 focus:text-red-600">
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu> */}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
