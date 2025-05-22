import React from 'react';
import { useNavigate } from 'react-router-dom';
import SignupForm from '../components/auth/SignupForm';
import Logo from '../components/common/Logo';

const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  
  // Mock signup function - would connect to auth service in a real app
  const handleSignup = (email: string, password: string) => {
    console.log('Signup with:', email, password);
    // Mock successful signup
    navigate('/app');
  };
  
  const handleGoogleSignup = () => {
    console.log('Signup with Google');
    // Mock successful Google signup
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
        <SignupForm 
          onSignup={handleSignup}
          onGoogleSignup={handleGoogleSignup}
        />
      </div>
    </div>
  );
};

export default SignupPage;