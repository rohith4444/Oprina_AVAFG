/**
 * Email Service Configuration
 * 
 * This file documents the required environment variables for the email services.
 * 
 * REQUIRED SUPABASE ENVIRONMENT VARIABLES:
 * 
 * 1. RESEND_API_KEY - Your Resend API key for sending emails
 *    - Get this from: https://resend.com/api-keys
 *    - Set in Supabase Dashboard > Settings > Edge Functions > Environment Variables
 * 
 * 2. SITE_URL - Your application's URL (optional, defaults to localhost)
 *    - Production: https://your-domain.com
 *    - Development: http://localhost:5173
 * 
 * SETUP INSTRUCTIONS:
 * 
 * 1. Sign up for Resend: https://resend.com
 * 2. Create an API key in your Resend dashboard
 * 3. Add the API key to Supabase environment variables
 * 4. Deploy the contact-form function: `supabase functions deploy contact-form`
 * 
 * The welcome email service will automatically trigger when new users confirm their email.
 */

export const EMAIL_CONFIG = {
  // These should be set in Supabase Edge Functions environment
  REQUIRED_ENV_VARS: [
    'RESEND_API_KEY',
    'SITE_URL' // Optional, has default
  ],
  
  // Email template settings
  SENDER: 'Oprina <noreply@oprina.com>',
  SUBJECT: 'Welcome to Oprina - Your AI Assistant is Ready!',
  
  // Default URLs for development
  DEFAULT_SITE_URL: 'http://localhost:5173'
} as const;

// Type for the email service payload
export interface WelcomeEmailPayload {
  email: string;
  name?: string;
} 