import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import Logo from '../common/Logo';

interface NavbarProps {
  isAuthenticated?: boolean;
  onLogout?: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ 
  isAuthenticated = false, 
  onLogout = () => {} 
}) => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/signup';

  if (isAuthPage) {
    return null;
  }

  return (
    <nav className="w-full bg-white border-b border-gray-100">
      <div className="flex justify-between items-center py-4 px-6">
        <Link to="/" className="flex items-center space-x-2 cursor-pointer">
          <Logo />
          <span className="text-xl font-bold text-black">Oprina</span>
        </Link>
        
        <div className="flex items-center space-x-8">
          {isAuthenticated ? (
            <button onClick={onLogout} className="text-sm font-medium text-gray-700 hover:text-gray-900">
              Logout
            </button>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-gray-700 hover:text-gray-900">
                Login
              </Link>
              <Link to="/signup" className="text-sm font-medium text-gray-700 hover:text-gray-900">
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;