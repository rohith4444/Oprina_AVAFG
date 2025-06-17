import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';
import '../styles/Navbar.css';

const UnauthenticatedNavbar: React.FC = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <Logo />
          <span className="navbar-brand">Oprina</span>
        </Link>
        
        {/* No authentication buttons - user is treated as logged out */}
        <div className="navbar-links">
          {/* Empty - no buttons shown */}
        </div>
      </div>
    </nav>
  );
};

export default UnauthenticatedNavbar; 