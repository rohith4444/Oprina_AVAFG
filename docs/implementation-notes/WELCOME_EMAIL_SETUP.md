# Welcome Email Service Setup Guide

This guide walks you through setting up the welcome email service for Oprina using Resend and Supabase Edge Functions.

## 🎯 Overview

The welcome email service automatically sends a branded welcome email to new users after they confirm their email address. The service is integrated into the authentication flow and triggers seamlessly.

## 🛠️ Setup Steps

### 1. Create Resend Account

1. Visit [resend.com](https://resend.com) and create an account
2. Go to your dashboard and navigate to "API Keys"
3. Create a new API key for your project
4. Copy the API key (you'll need it in step 3)

### 2. Configure Domain (Optional but Recommended)

For production use:
1. In your Resend dashboard, go to "Domains"
2. Add your domain (e.g., `oprina.com`)
3. Follow the DNS verification steps
4. Update the `from` address in the edge function if needed

For development, you can use the default sandbox domain.

### 3. Set Supabase Environment Variables

1. Go to your Supabase project dashboard
2. Navigate to **Settings > Edge Functions**
3. Add these environment variables:

```bash
# Required
RESEND_API_KEY=re_xxxxxxxxxx

# Optional (defaults to http://localhost:5173)
SITE_URL=https://your-domain.com
```

### 4. Deploy the Edge Function

Run the following command in your project directory:

```bash
# Navigate to the app directory if not already there
cd app

# Deploy the welcome email function
supabase functions deploy send-welcome-email
```

### 5. Test the Setup

You can test the function directly using curl:

```bash
curl -X POST 'https://YOUR_PROJECT_ID.supabase.co/functions/v1/send-welcome-email' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

Replace:
- `YOUR_PROJECT_ID` with your Supabase project ID
- `YOUR_ANON_KEY` with your Supabase anon key

## 🔄 How It Works

### Integration Flow

1. **User Registration**: User signs up with email/password
2. **Email Confirmation**: User receives confirmation email from Supabase
3. **Email Verified**: User clicks confirmation link
4. **Authentication State Change**: Supabase triggers `SIGNED_IN` event
5. **Welcome Email Triggered**: `AuthContext.tsx` detects new user and calls edge function
6. **Email Sent**: Resend delivers the welcome email

### Code Integration

The service is integrated in `app/src/context/AuthContext.tsx`:

- Listens for authentication state changes
- Detects newly confirmed users
- Calls the `send-welcome-email` edge function
- Prevents duplicate emails using localStorage tracking

## 📧 Email Content

The welcome email includes:

- **Branded Header**: Oprina logo and welcome message
- **Personalization**: Uses user's name if available
- **Feature Overview**: Key capabilities of Oprina
- **Quick Start Guide**: Step-by-step getting started tips
- **Call-to-Action**: Direct link to dashboard
- **Support Links**: Contact and legal pages
- **Responsive Design**: Works on mobile and desktop

## 🔧 Troubleshooting

### Common Issues

1. **Function not found error**
   - Ensure the function is deployed: `supabase functions deploy send-welcome-email`
   - Check your Supabase project is linked correctly

2. **Email not sending**
   - Verify `RESEND_API_KEY` is set correctly in Supabase
   - Check Resend dashboard for API usage and errors
   - Ensure domain is verified (for production)

3. **Multiple emails sent**
   - The system prevents duplicates using localStorage
   - Check browser console for "Welcome email sent" logs

### Debug Steps

1. Check Supabase Edge Function logs:
   ```bash
   supabase functions logs send-welcome-email
   ```

2. Verify environment variables in Supabase dashboard

3. Test the function directly with curl (see step 5 above)

4. Check browser console for AuthContext logs

## 🚀 Production Considerations

1. **Domain Setup**: Use a verified domain in Resend for better deliverability
2. **Rate Limits**: Resend has rate limits - monitor usage in production
3. **Error Handling**: The function includes comprehensive error handling
4. **Logging**: Monitor Supabase function logs for issues
5. **Email Templates**: Consider customizing the email template for your brand

## 📁 File Structure

```
app/
├── supabase/
│   └── functions/
│       └── send-welcome-email/
│           ├── index.ts          # Edge function implementation
│           └── README.md         # Function-specific docs
├── src/
│   ├── context/
│   │   └── AuthContext.tsx       # Integration logic
│   └── utils/
│       └── emailConfig.ts        # Configuration and types
└── WELCOME_EMAIL_SETUP.md        # This file
```

## ✅ Verification

To verify everything is working:

1. Create a new test account
2. Check email for confirmation link
3. Click confirmation link
4. Check email again for welcome message
5. Verify user can access dashboard

The welcome email should arrive within a few seconds of email confirmation. 