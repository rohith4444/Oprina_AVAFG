# Frontend - Oprina Web Application

React TypeScript frontend for the Oprina conversational AI platform with voice interaction, user authentication, and avatar integration.

## 🏗️ Architecture

### Modern React Stack
- **React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **Tailwind CSS** for responsive styling
- **React Router v6** for navigation
- **Context API** for state management
- **Supabase Client** for authentication and database

### Key Features
- ✅ **Voice-First Interface** - Speech-to-text and text-to-speech
- ✅ **AI Avatar Integration** - HeyGen streaming avatars
- ✅ **User Authentication** - Email/password and Google OAuth
- ✅ **Session Management** - Persistent chat conversations
- ✅ **Responsive Design** - Mobile and desktop optimized
- ✅ **Real-time Updates** - Live conversation sync

## 📁 Folder Structure

```
frontend/
├── .env                         # Local environment variables (gitignored)
├── .env.example                 # Development environment template
├── .env.production              # Production environment variables (gitignored)
├── .env.production.example      # Production environment template
├── README.md                    # This documentation
├── package.json                 # Dependencies and scripts
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
├── src/
│   ├── main.tsx                # App entry point
│   ├── App.tsx                 # Main app component with routing
│   ├── index.css               # Global styles (Tailwind imports)
│   ├── supabaseClient.ts       # Supabase connection setup
│   ├── components/             # Reusable UI components
│   ├── pages/                  # Page components
│   ├── context/                # State management
│   ├── services/               # API integration
│   ├── types/                  # TypeScript type definitions
│   ├── utils/                  # Utility functions
│   └── styles/                 # Component-specific CSS files
└── public/                     # Static assets
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Running backend API
- Supabase project configured

### Setup Process
1. Install dependencies
2. Configure environment variables
3. Start development server
4. Access application at localhost

## 🔧 Environment Variables

### Core Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_BACKEND_URL` | ✅ | Backend API URL (localhost:8000 for dev, production URL for prod) |
| `VITE_SUPABASE_URL` | ✅ | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key |

### Avatar Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_HEYGEN_API_KEY` | ➖ | HeyGen API key for streaming avatars |
| `VITE_HEYGEN_API_URL` | ➖ | HeyGen API URL (defaults to official endpoint) |
| `VITE_HEYGEN_AVATAR_ID` | ➖ | Specific HeyGen avatar ID |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_USE_STATIC_AVATAR` | `true` | Use static avatar vs HeyGen streaming |
| `VITE_ENABLE_AVATAR_SELECTOR` | `false` | Show avatar selection UI |
| `VITE_SHOW_AVATAR_TOGGLE` | `true` | Show avatar type toggle in dev |
| `VITE_CACHE_AVATAR_IMAGES` | `false` | Cache avatar images locally |
| `VITE_DEBUG_AVATAR_API` | `false` | Enable avatar API debugging |

### Environment-Specific Configuration

**Development (`.env`):**
- `VITE_BACKEND_URL=http://localhost:8000`
- `VITE_USE_STATIC_AVATAR=true` (easier testing)
- `VITE_SHOW_AVATAR_TOGGLE=true` (dev features)
- `VITE_DEBUG_AVATAR_API=true` (debugging enabled)

**Production (`.env.production`):**
- `VITE_BACKEND_URL=https://your-backend.run.app`
- `VITE_USE_STATIC_AVATAR=false` (streaming avatars)
- `VITE_SHOW_AVATAR_TOGGLE=false` (no dev UI)
- `VITE_DEBUG_AVATAR_API=false` (no debugging)
- `VITE_CACHE_AVATAR_IMAGES=true` (performance optimization)

## 📱 Pages Overview

### Public Pages
- **HomePage** - Landing page with features and avatar demo
- **LoginPage** - User authentication with email/Google OAuth
- **SignupPage** - User registration with email verification
- **EmailConfirmationPending** - Email verification waiting page
- **ThankYou** - Success confirmation page
- **TermsPage** - Terms of service
- **PrivacyPage** - Privacy policy

### Authenticated Pages
- **DashboardPage** - Main application interface with voice interaction
- **ContactPage** - Support contact form
- **SettingsPage** - Settings overview page
- **Settings Pages** - Nested settings:
  - **ProfileSettings** - User profile management
  - **ConnectedAppsSettings** - OAuth app connections
  - **AccountSettings** - Security and account deletion

### Special Handler Pages
- **GmailAuthHandler** - Gmail OAuth callback processing

### Page Features
- **Responsive Design** - Mobile-first approach with Tailwind CSS
- **Loading States** - Smooth user experience with loading indicators
- **Error Handling** - User-friendly error messages and recovery
- **Navigation** - Intuitive routing with React Router v6
- **Authentication Flow** - Seamless login/logout with Supabase Auth

## 🎨 Styling System

### Tailwind CSS
- **Utility-first** approach for rapid development
- **Responsive design** with mobile-first breakpoints
- **Dark mode** support (extendable)
- **Custom design tokens** via CSS variables

### CSS Architecture
- Global variables in index.css
- Component-specific styles in separate files
- CSS Modules for component isolation
- Tailwind utilities for common patterns
- Custom CSS for complex layouts
- Animation classes for smooth transitions

## 🔧 Architecture Details

### Services Layer (`src/services/`)
- **OAuth integration** - API calls for Gmail/Calendar connections
- **Token management** - OAuth token handling

### Type Definitions (`src/types/`)
- **Avatar system types** - TypeScript interfaces for avatar configuration
- **State management types** - Event handler definitions

### Utilities (`src/utils/`)
- **Email configuration** - Email service configuration and validation
- **Avatar API functions** - Text-to-speech utilities and avatar controls
- **Voice synthesis helpers** - Browser voice API integration

### State Management Patterns
- **AuthContext** - Global authentication state
- **Local state** - Component-specific data management
- **Custom hooks** - Reusable logic patterns
- **Service integration** - API call management

## 🚨 Troubleshooting

### Common Issues

**Build Errors**
- Clear node modules and reinstall dependencies
- Check TypeScript configuration
- Verify missing dependencies

**Environment Variables Not Loading**
- Ensure variables start with VITE_ prefix
- Check file names (.env for dev, .env.production for prod)
- Restart development server after environment changes

**Authentication Issues**
- Verify Supabase URL and keys
- Check CORS configuration in Supabase dashboard
- Ensure backend is running and accessible

**Avatar Not Working**
- Check HeyGen API credentials
- Test with static avatar first
- Verify microphone permissions in browser
- Check browser console for avatar errors

**OAuth Integration Issues**
- Check Gmail OAuth configuration
- Verify redirect URIs in Google Cloud Console
- Test OAuth API endpoints

**Production vs Development Issues**
- Ensure correct environment file is used
- Check backend URL configuration
- Verify CORS settings match frontend domain

### Debug Tools
- Environment variable debugging
- Supabase client debugging
- OAuth API debugging
- Avatar API debugging

### Environment Testing
- Use the `EnvTest` component to verify configuration
- Check network tab for API calls
- Verify browser console for errors

## 🏭 Production Build

### Environment-Specific Builds
- **Development Build** - Uses .env file
- **Production Build** - Uses .env.production file

### Build Process
- Install dependencies
- Run production build
- Preview production build locally

### Build Output
- Static files in dist/ folder
- Optimized and minified code
- Source maps for debugging (if enabled)
- Environment variables baked into build

### Deployment Options
- **Vercel** (Recommended) - Connect GitHub repo with auto-deployment
- **Netlify** - GitHub integration or manual upload
- **Google Cloud Storage + CDN** - Static hosting with CDN
- **Docker Deployment** - Containerized with nginx

### Production Configuration
- Use `.env.production` file during build
- Set `VITE_BACKEND_URL` to production backend URL
- Disable debug flags
- Enable production optimizations
- Update CORS settings for production domain
- Configure OAuth redirect URIs for production

For deployment and production setup, see the [self-hosting guide](../docs/self-hosting.md).