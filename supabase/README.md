# Supabase - Database & Authentication

Database schema, authentication system, and edge functions for the Oprina platform using Supabase as the backend-as-a-service.

## 🏗️ Architecture

### Core Components
- **PostgreSQL Database** - Contact form submissions with case management
- **Authentication** - User registration, login, and session management (handled by Supabase Auth)
- **Edge Functions** - Serverless functions for contact forms and user management
- **Row Level Security** - Data isolation between users
- **Contact System** - Support case management with auto-incrementing IDs

### Key Features
- ✅ **User Authentication** - Email/password and OAuth providers (Supabase Auth)
- ✅ **Contact System** - Support case management with auto-incrementing IDs  
- ✅ **Edge Functions** - Contact forms, welcome emails, user deletion
- ✅ **Admin Functions** - User account deletion with proper authorization
- ✅ **Email Integration** - Welcome emails via Resend API

## 📁 Structure

```
supabase/
├── README.md                   # This documentation
├── .branches/
│   └── *current*branch        # Current branch info
├── migrations/                 # Database schema files
│   └── 20240101_create_contact_tables.sql # Contact system tables
└── functions/                  # Edge Functions (Serverless)
    ├── _shared/
    │   └── cors.ts            # CORS utilities
    ├── contact-form/
    │   └── index.ts           # Contact form handler
    ├── delete-user/
    │   └── index.ts           # User account deletion
    └── resend-email/
        └── index.ts           # Welcome email sender
```

## 🗄️ Database Schema

### Contact System Tables

The Supabase project contains one migration file that creates the contact form system:

#### Contact System (`migrations/20240101_create_contact_tables.sql`)

**Auto-incrementing Case Counter:**
```sql
CREATE TABLE case_counter (
    id BIGINT PRIMARY KEY DEFAULT 1,
    last_case_id BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Contact Form Submissions:**
```sql
CREATE TABLE contact_submissions (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    subject TEXT,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Features:**
- **Auto-incrementing Case IDs** - Each submission gets a unique case number (#1, #2, #3...)
- **Complete Contact Information** - Name, email, phone, subject, message
- **Audit Trail** - Created timestamps for all submissions
- **Data Integrity** - Proper constraints and indexes

**Note:** Other database tables (users, sessions, messages, etc.) are managed by the backend application and are not part of this Supabase project.

## 🚀 Setup Instructions

### 1. Create Supabase Project

1. **Sign up** at [supabase.com](https://supabase.com)
2. **Create new project**
   - Choose organization
   - Set project name: `oprina-production`
   - Set database password
   - Select region (use same as Google Cloud)
3. **Wait for setup** (~2 minutes)

### 2. Get API Credentials

Navigate to **Settings → API** and copy:

```bash
# Project Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Run Database Migration

**Execute the migration in Supabase SQL Editor:**

Navigate to your **Supabase project → SQL Editor → New Query** and run:

```bash
# Copy the content of the migration file
cat supabase/migrations/20240101_create_contact_tables.sql

# Paste into Supabase SQL Editor and execute
```

**What this migration creates:**
- **`case_counter`** table for auto-incrementing case IDs
- **`contact_submissions`** table for storing contact form data
- **Indexes** for better query performance
- **Triggers** for auto-updating timestamps

**Verification:**
After running the migration, verify tables exist in Supabase:
- Go to **Table Editor** in Supabase dashboard  
- Confirm tables are created: `case_counter`, `contact_submissions`
- Check that the case counter has initial record with `last_case_id = 0`

### 4. Configure Authentication

**Navigate to Authentication → Settings:**

1. **Site URL:** `http://localhost:3000` (development)
2. **Redirect URLs:** Add your frontend URLs
3. **Email Templates:** Customize signup/recovery emails
4. **Providers:** Enable Google OAuth if needed

**For Google OAuth:**
1. **Enable Google provider**
2. **Add Client ID and Secret** from Google Cloud Console
3. **Configure redirect URI:** `https://your-project.supabase.co/auth/v1/callback`

### 5. Deploy Edge Functions

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link project
supabase link --project-ref your-project-id

# Deploy functions
supabase functions deploy contact-form
supabase functions deploy delete-user
supabase functions deploy resend-email
```

## 🔧 Edge Functions

### Contact Form Handler (`functions/contact-form/index.ts`)

**Purpose:** Process contact form submissions with auto-incrementing case IDs

**Endpoint:** `https://your-project.supabase.co/functions/v1/contact-form`

**Request:**
```typescript
{
  name: string;
  email: string;
  phone?: string;
  subject: string;
  message: string;
}
```

**Response:**
```typescript
{
  success: true;
  caseId: "#1";
  message: "Contact form submitted successfully";
}
```

**Features:**
- Auto-incrementing case IDs (#1, #2, #3...)
- Email notification to support team
- Database storage for tracking
- CORS enabled for frontend

### User Deletion (`functions/delete-user/index.ts`)

**Purpose:** Securely delete user accounts with admin privileges

**Endpoint:** `https://your-project.supabase.co/functions/v1/delete-user`

**Request:**
```typescript
{
  userId: string;
}
```

**Authentication:** Requires valid JWT token

**Features:**
- Admin-level user deletion
- Cascading delete of user data
- Audit logging
- Authorization checks

### Welcome Email (`functions/resend-email/index.ts`)

**Purpose:** Send welcome emails to new users

**Endpoint:** `https://your-project.supabase.co/functions/v1/resend-email`

**Request:**
```typescript
{
  email: string;
  name?: string;
}
```

**Features:**
- Professional welcome email templates
- Resend API integration
- Error handling and logging
- Customizable email content


## 📄 Integration

### Frontend Integration

**Contact Form Integration:**
```typescript
// Frontend contact form submission
const submitContactForm = async (formData) => {
  const response = await fetch(
    `https://your-project.supabase.co/functions/v1/contact-form`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY
      },
      body: JSON.stringify(formData)
    }
  );
  
  const result = await response.json();
  console.log(`Contact submitted with case ID: ${result.caseId}`);
};
```

**User Account Deletion:**
```typescript
// Frontend user deletion (authenticated)
const deleteUserAccount = async (userId: string) => {
  const { data: { session } } = await supabase.auth.getSession();
  
  const response = await fetch(
    `https://your-project.supabase.co/functions/v1/delete-user`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.access_token}`,
        'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY
      },
      body: JSON.stringify({ userId })
    }
  );
};
```

**Authentication (Handled by Supabase directly):**
```typescript
// User authentication
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

// Signup
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123'
});

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
});
```
 
For complete application setup, see the [local development guide](../docs/local-setup.md).