import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader } from 'lucide-react';
import UnauthenticatedNavbar from '../components/UnauthenticatedNavbar';
import MinimalFooter from '../components/MinimalFooter';

const GetStartedPage: React.FC = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Wait for auth to load, then redirect based on user state
    if (!loading) {
      if (user) {
        // User is logged in → redirect to dashboard
        navigate('/dashboard');
      } else {
        // User is not logged in → redirect to login with return path
        navigate('/login?return=dashboard');
      }
    }
  }, [user, loading, navigate]);

  // Show loading state while checking authentication
  return (
    <div className="min-h-screen flex flex-col">
      <UnauthenticatedNavbar />
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <Loader className="animate-spin h-8 w-8 text-blue-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Getting Started with Oprina
          </h2>
          <p className="text-gray-600">
            Checking your authentication status...
          </p>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default GetStartedPage; 