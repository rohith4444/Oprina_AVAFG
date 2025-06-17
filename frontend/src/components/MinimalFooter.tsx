import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';

const MinimalFooter: React.FC = () => {
  return (
    <footer style={{ backgroundColor: '#F8F9FA' }} className="w-full mt-auto border-t border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main footer content */}
        <div className="py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            {/* Left side - Logo and brand */}
            <div className="flex items-center space-x-3 mb-6 md:mb-0 justify-center md:justify-start">
              <Logo size={30} />
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Oprina</h3>
                <p className="text-sm text-gray-600">Voice-Powered Gmail Assistant</p>
              </div>
            </div>
            
            {/* Right side - Links */}
            <div className="flex items-center justify-center md:justify-end space-x-6">
              <Link 
                to="/privacy" 
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors duration-200"
              >
                Privacy
              </Link>
              <Link 
                to="/terms" 
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors duration-200"
              >
                Terms
              </Link>
              <Link 
                to="/contact" 
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors duration-200"
              >
                Contact
              </Link>
            </div>
          </div>
        </div>
        
        {/* Bottom copyright */}
        <div className="border-t border-gray-300 py-4 text-center">
          <p className="text-sm text-gray-600">
            &copy; {new Date().getFullYear()} Oprina. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default MinimalFooter; 