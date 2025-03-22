
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { SocketProvider } from "@/contexts/SocketContext";
import { TaskProvider } from "@/contexts/TaskContext";
import { RoomProvider } from "@/contexts/RoomContext";
import AuthGuard from "@/components/auth/AuthGuard";

import Layout from "@/components/layout/Layout";
import Dashboard from "@/pages/Dashboard";
import Tasks from "@/pages/Tasks";
import Rooms from "@/pages/Rooms";
import RoomDetails from "@/pages/RoomDetails";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <SocketProvider>
          <TaskProvider>
            <RoomProvider>
              <BrowserRouter>
                <AuthGuard>
                  <Layout>
                    <Routes>
                      {/* Main Routes */}
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/tasks" element={<Tasks />} />
                      {/* <Route path="/rooms" element={<Rooms />} /> */}
                      {/* <Route path="/rooms/:roomId" element={<RoomDetails />} /> */}

                      {/* Redirect to Dashboard for any route that doesn't exist */}
                      <Route path="*" element={<Navigate to="/" />} />
                    </Routes>
                  </Layout>
                </AuthGuard>
              </BrowserRouter>
              <Sonner />
              <Toaster />
            </RoomProvider>
          </TaskProvider>
        </SocketProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
