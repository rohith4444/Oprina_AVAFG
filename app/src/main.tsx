import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  // Temporarily disabled StrictMode to prevent duplicate emails in development
  // <StrictMode>
    <App />
  // </StrictMode>
);
