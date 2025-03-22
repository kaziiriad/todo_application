
import React, { createContext, useState, useContext, useEffect } from 'react';
import { toast } from 'sonner';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  logout: () => void;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Auto-authenticate with demo user
    const mockUser = {
      id: '1',
      email: 'demo@example.com',
      name: 'Demo User',
    };
    
    setUser(mockUser);
    localStorage.setItem('authToken', 'mock-jwt-token');
    setLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    // Since we're auto-authenticating, this is just a stub function
    // that returns the already authenticated user
    toast.success('Logged in as Demo User');
    return Promise.resolve();
  };

  const signup = async (name: string, email: string, password: string): Promise<void> => {
    // Since we're auto-authenticating, this is just a stub function
    toast.success('Account created and logged in as Demo User');
    return Promise.resolve();
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('authToken');
    toast.info('You have been logged out');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        logout,
        isAuthenticated: true, // Always authenticated
        login,
        signup
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
