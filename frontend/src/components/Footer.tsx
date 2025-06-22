import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';
import '../styles/Footer.css';

const Footer: React.FC = () => {
  const { user } = useAuth();
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-branding">
          <Logo size={30} />
          <h3 className="footer-title">Oprina</h3>
          <p className="footer-tagline">Voice-Powered Gmail Assistant</p>
        </div>
        
        <div className="footer-links">
          <div className="footer-section">
            <h4 className="footer-heading">Product</h4>
            <ul>
              <li><Link to="/">Home</Link></li>
              <li><Link to="/features">Features</Link></li>
              <li><Link to="/pricing">Pricing</Link></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-heading">Company</h4>
            <ul>
              <li><Link to="/about">About</Link></li>
              <li><Link to="/blog">Blog</Link></li>
              <li><Link to="/careers">Careers</Link></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-heading">Resources</h4>
            <ul>
              <li><Link to="/help">Help Center</Link></li>
              <li><Link to={user ? "/support" : "/contact"}>{user ? "Support" : "Contact"}</Link></li>
              <li><Link to="/faq">FAQ</Link></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h4 className="footer-heading">Legal</h4>
            <ul>
              <li><Link to="/terms">Terms</Link></li>
              <li><Link to="/privacy">Privacy</Link></li>
              <li><Link to="/cookies">Cookies</Link></li>
            </ul>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} Oprina. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;