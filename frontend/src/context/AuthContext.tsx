import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '@supabase/supabase-js';
import { supabase } from '../supabaseClient';

interface AuthContextType {
  user: User | null;
  userProfile: any | null;  // Backend profile data
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signupWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  updateUserDisplayName: (displayName: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Backend API URL
  const BACKEND_API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  // Load user profile from backend API
  const loadUserProfile = async (authToken: string) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/api/v1/user/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const profileData = await response.json();
        setUserProfile(profileData);
        
        // Set display name for UI (preferred name takes priority)
        const displayName = profileData.preferred_name || profileData.full_name || user?.email?.split('@')[0] || 'User';
        localStorage.setItem('user_display_name', displayName);
        
        console.log('User profile loaded:', profileData);
      } else {
        console.warn('Failed to load user profile:', response.status);
        // Don't throw error - profile might not exist yet for new users
        setUserProfile(null);
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
      setUserProfile(null);
    }
  };

  // Check if user has welcome email flag and send if needed
  const checkAndSendWelcomeEmail = async (user: User, isNewlyConfirmed: boolean = false) => {
    const welcomeKey = `welcome_sent_${user.id}`;
    const hasWelcomeSent = localStorage.getItem(welcomeKey);

    if (isNewlyConfirmed && !hasWelcomeSent) {
      try {
        localStorage.setItem(welcomeKey, 'true');
        
        const { error } = await supabase.functions.invoke('resend-email', {
          body: {
            email: user.email,
            name: user.user_metadata?.full_name || user.email?.split('@')[0]
          }
        });

        if (error) {
          console.error('Welcome email error:', error);
        } else {
          console.log('Welcome email sent successfully');
        }
      } catch (error) {
        console.error('Error sending welcome email:', error);
      }
    }
  };

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        
        if (session?.user) {
          setUser(session.user);
          
          // Load user profile from backend
          if (session.access_token) {
            await loadUserProfile(session.access_token);
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state changed:', event, session?.user?.email);

      if (session?.user) {
        setUser(session.user);
        
        // Load user profile from backend
        if (session.access_token) {
          await loadUserProfile(session.access_token);
        }
        
        // Handle welcome email for email confirmations
        if (event === 'SIGNED_IN' && session.user.email_confirmed_at) {
          const isNewlyConfirmed = !localStorage.getItem(`welcome_sent_${session.user.id}`);
          await checkAndSendWelcomeEmail(session.user, isNewlyConfirmed);
        }
      } else {
        setUser(null);
        setUserProfile(null);
        localStorage.removeItem('user_display_name');
      }
      
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    });
    if (error) throw error;
  };

  const signup = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/thank-you`
      }
    });
    if (error) throw error;
  };

  const loginWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/dashboard?login=true`,
        queryParams: {
          access_type: 'offline',
          prompt: 'select_account' // For login: just account selection, no consent unless new account
        }
      }
    });
    if (error) throw error;
  };

  const signupWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/dashboard?signup=true`,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent select_account'
        }
      }
    });
    if (error) throw error;
  };

  const logout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    
    // Clear local storage
    localStorage.removeItem('user_display_name');
    localStorage.removeItem('user_profile_backup');
    
    setUserProfile(null);
  };

  const updateUserDisplayName = (displayName: string) => {
    localStorage.setItem('user_display_name', displayName);
    
    // Update userProfile state if it exists
    if (userProfile) {
      setUserProfile((prev: any) => ({
        ...prev,
        display_name: displayName
      }));
    }
  };

  const value = {
    user,
    userProfile,
    loading,
    login,
    signup,
    loginWithGoogle,
    signupWithGoogle,
    logout,
    updateUserDisplayName
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};