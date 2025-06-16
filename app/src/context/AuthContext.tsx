import { supabase } from '../supabaseClient';
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { WelcomeEmailPayload } from '../utils/emailConfig';

interface User {
  uid: string;
  email: string | null;
  displayName?: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  updateUserDisplayName: (displayName: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Function to send welcome email
  const sendWelcomeEmail = async (email: string, name?: string) => {
    try {
      const payload: WelcomeEmailPayload = { email, name };
      const { data, error } = await supabase.functions.invoke('resend-email', {
        body: payload
      });

      if (error) {
        console.error('Error sending welcome email:', error);
        return false;
      }

      console.log('Welcome email sent successfully:', data);
      return true;
    } catch (error) {
      console.error('Error invoking welcome email function:', error);
      return false;
    }
  };

  useEffect(() => {
    const restoreSession = async () => {
      const { data, error } = await supabase.auth.getUser();

      if (error || !data.user) {
        setUser(null);
        localStorage.removeItem('user');
      } else {
        const restoredUser: User = {
          uid: data.user.id,
          email: data.user.email ?? null,
          displayName: localStorage.getItem('user_display_name'),
        };
        setUser(restoredUser);
        localStorage.setItem('user', JSON.stringify(restoredUser));
      }

      setLoading(false);
    };

    // Set up auth state change listener with proper cleanup
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('🔐 Auth state change:', event, session?.user?.email);
      
      if (event === 'SIGNED_IN' && session?.user) {
        const newUser: User = {
          uid: session.user.id,
          email: session.user.email ?? null,
          displayName: localStorage.getItem('user_display_name'),
        };
        setUser(newUser);
        localStorage.setItem('user', JSON.stringify(newUser));

        // Check if this is a new user (email confirmation) and send welcome email
        // Only for users who just confirmed their email (not regular logins)
        const welcomeKey = `welcome_sent_${session.user.id}`;
        const hasWelcomeSent = localStorage.getItem(welcomeKey);
        
        const isNewlyConfirmed = session.user.email_confirmed_at && 
                                !hasWelcomeSent &&
                                event === 'SIGNED_IN';
        
        if (isNewlyConfirmed && session.user.email) {
          console.log('📧 Sending welcome email to new user:', session.user.email);
          
          // Set flag BEFORE sending to prevent duplicates
          localStorage.setItem(welcomeKey, 'true');
          
          try {
            await sendWelcomeEmail(session.user.email);
            console.log('✅ Welcome email sent successfully');
          } catch (error) {
            console.error('❌ Failed to send welcome email:', error);
            // Remove flag if sending failed so it can be retried
            localStorage.removeItem(welcomeKey);
          }
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        localStorage.removeItem('user');
      }
    });

    restoreSession();

    // Cleanup function to unsubscribe from auth state changes
    return () => {
      console.log('🧹 Cleaning up auth subscription');
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;

      const newUser = { 
        uid: data.user?.id || '', 
        email: data.user?.email || null,
        displayName: localStorage.getItem('user_display_name'),
      };
      setUser(newUser);
      localStorage.setItem('user', JSON.stringify(newUser));
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/thank-you`,
        },
      });
      if (error) throw error;
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: 'http://localhost:5173/dashboard',
        queryParams: {
          prompt: 'select_account',
        },
      },
    });
    if (error) throw error;
  };

  const logout = async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
      setUser(null);
      localStorage.removeItem('user');
      localStorage.removeItem('user_display_name');
    } finally {
      setLoading(false);
    }
  };

  const updateUserDisplayName = (displayName: string) => {
    if (user) {
      const updatedUser = { ...user, displayName };
      setUser(updatedUser);
      localStorage.setItem('user_display_name', displayName);
      localStorage.setItem('user', JSON.stringify(updatedUser));
    }
  };

  const value = {
    user,
    loading,
    login,
    signup,
    loginWithGoogle,
    logout,
    updateUserDisplayName,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
