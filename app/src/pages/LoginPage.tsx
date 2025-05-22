import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import Logo from '../components/common/Logo';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  
  // Mock login function - would connect to auth service in a real app
  const handleLogin = (email: string, password: string) => {
    console.log('Login with:', email, password);
    // Mock successful login
    navigate('/app');
  };
  
  const handleGoogleLogin = () => {
    console.log('Login with Google');
    // Mock successful Google login
    navigate('/app');
  };
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md flex flex-col items-center">
        <Logo size="lg" />
        <div className="mt-2 text-center text-2xl font-bold bg-gradient-to-r from-[#5B7CFF] via-[#4FD1C5] to-[#4ADE80] text-transparent bg-clip-text">
          Oprina
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <LoginForm 
          onLogin={handleLogin}
          onGoogleLogin={handleGoogleLogin}
        />
      </div>
    </div>
  );
};

export default LoginPage;