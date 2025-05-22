import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState } from '../types';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  signupWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const defaultAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

const AuthContext = createContext<AuthContextType>({
  ...defaultAuthState,
  login: async () => {},
  loginWithGoogle: async () => {},
  signup: async () => {},
  signupWithGoogle: async () => {},
  logout: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(defaultAuthState);

  // Mock authentication functions
  const login = async (email: string, password: string) => {
    setAuthState({ ...authState, isLoading: true, error: null });
    
    try {
      // In a real app, this would make an API call to authenticate
      const mockUser: User = {
        id: '1',
        email,
        name: email.split('@')[0],
      };
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAuthState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      // Store in localStorage for persistence
      localStorage.setItem('user', JSON.stringify(mockUser));
      
    } catch (error) {
      setAuthState({
        ...authState,
        isLoading: false,
        error: 'Invalid email or password',
      });
    }
  };

  const loginWithGoogle = async () => {
    setAuthState({ ...authState, isLoading: true, error: null });
    
    try {
      // In a real app, this would integrate with Google OAuth
      const mockUser: User = {
        id: '2',
        email: 'user@gmail.com',
        name: 'Google User',
        avatar: 'https://lh3.googleusercontent.com/a/default-user',
      };
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAuthState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      // Store in localStorage for persistence
      localStorage.setItem('user', JSON.stringify(mockUser));
      
    } catch (error) {
      setAuthState({
        ...authState,
        isLoading: false,
        error: 'Google login failed',
      });
    }
  };

  const signup = async (email: string, password: string) => {
    setAuthState({ ...authState, isLoading: true, error: null });
    
    try {
      // In a real app, this would make an API call to create an account
      const mockUser: User = {
        id: '3',
        email,
        name: email.split('@')[0],
      };
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAuthState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      // Store in localStorage for persistence
      localStorage.setItem('user', JSON.stringify(mockUser));
      
    } catch (error) {
      setAuthState({
        ...authState,
        isLoading: false,
        error: 'Failed to create account',
      });
    }
  };

  const signupWithGoogle = async () => {
    setAuthState({ ...authState, isLoading: true, error: null });
    
    try {
      // In a real app, this would integrate with Google OAuth
      const mockUser: User = {
        id: '4',
        email: 'newuser@gmail.com',
        name: 'New Google User',
        avatar: 'https://lh3.googleusercontent.com/a/default-user',
      };
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setAuthState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      // Store in localStorage for persistence
      localStorage.setItem('user', JSON.stringify(mockUser));
      
    } catch (error) {
      setAuthState({
        ...authState,
        isLoading: false,
        error: 'Google signup failed',
      });
    }
  };

  const logout = async () => {
    // In a real app, this would call an API to log out
    localStorage.removeItem('user');
    
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  };

  // Check for existing user on initial load
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser) as User;
        setAuthState({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        localStorage.removeItem('user');
        setAuthState({
          ...defaultAuthState,
          isLoading: false,
        });
      }
    } else {
      setAuthState({
        ...defaultAuthState,
        isLoading: false,
      });
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        loginWithGoogle,
        signup,
        signupWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};