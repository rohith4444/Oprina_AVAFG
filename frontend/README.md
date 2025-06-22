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
├── frontend.md                  # Additional frontend documentation
├── favicon.svg                  # Application favicon
├── index.html                   # HTML entry point
├── server.js                    # Development server (if needed)
├── package.json                 # Dependencies and scripts
├── package-lock.json            # Dependency lock file
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.js           # PostCSS configuration
├── tsconfig.json               # TypeScript configuration
├── eslint.config.js            # ESLint configuration
├── src/
│   ├── main.tsx                # App entry point
│   ├── App.tsx                 # Main app component with routing
│   ├── App.css                 # App-specific styles
│   ├── index.css               # Global styles (Tailwind imports)
│   ├── supabaseClient.ts       # Supabase connection setup
│   ├── vite-env.d.ts          # TypeScript environment definitions
│   ├── components/             # Reusable UI components
│   │   ├── Avatar.tsx          # Avatar wrapper component
│   │   ├── Button.tsx          # Styled button component
│   │   ├── ConversationDisplay.tsx # Chat message display
│   │   ├── EnvTest.tsx         # Environment testing component
│   │   ├── FeatureCard.tsx     # Feature showcase cards
│   │   ├── Footer.tsx          # Main footer component
│   │   ├── GmailPanel.tsx      # Gmail integration panel
│   │   ├── HeyGenAvatar.tsx    # Streaming avatar component
│   │   ├── Logo.tsx            # Company logo
│   │   ├── LogoHalo.tsx        # Animated logo with halo effect
│   │   ├── MinimalFooter.tsx   # Simple footer for auth pages
│   │   ├── Navbar.tsx          # Navigation bar
│   │   ├── ProtectedRoute.tsx  # Authentication wrapper
│   │   ├── QuotaDisplay.tsx    # Avatar usage display
│   │   ├── Sidebar.tsx         # Dashboard sidebar
│   │   ├── StaticAvatar.tsx    # Static avatar component
│   │   ├── UnauthenticatedNavbar.tsx # Navbar for logged-out users
│   │   └── VoiceControls.tsx   # Voice interaction controls
│   ├── pages/                  # Page components
│   │   ├── HomePage.tsx        # Landing page
│   │   ├── LoginPage.tsx       # User login
│   │   ├── SignupPage.tsx      # User registration
│   │   ├── DashboardPage.tsx   # Main app interface
│   │   ├── ContactPage.tsx     # Contact form
│   │   ├── EmailConfirmationPending.tsx # Email verification page
│   │   ├── GmailAuthHandler.tsx # Gmail OAuth callback handler
│   │   ├── PrivacyPage.tsx     # Privacy policy
│   │   ├── SettingsPage.tsx    # Settings main page
│   │   ├── TermsPage.tsx       # Terms of service
│   │   ├── ThankYou.tsx        # Success confirmation page
│   │   └── settings/           # Settings pages
│   │       ├── SettingsLayout.tsx
│   │       ├── ProfileSettings.tsx
│   │       ├── ConnectedAppsSettings.tsx
│   │       └── AccountSettings.tsx
│   ├── context/
│   │   └── AuthContext.tsx     # Authentication state management
│   ├── services/
│   │   └── oauthApi.ts         # OAuth API integration
│   ├── types/
│   │   └── staticAvatar.types.ts # TypeScript types for avatar
│   ├── utils/
│   │   ├── emailConfig.ts      # Email configuration utilities
│   │   └── staticAvatarAPI.ts  # Static avatar API functions
│   └── styles/                 # Component-specific CSS files
│       ├── AuthPages.css       # Authentication page styles
│       ├── Avatar.css          # Avatar component styles
│       ├── ConversationDisplay.css # Chat display styles
│       ├── DashboardPage.css   # Dashboard styles
│       ├── FeatureCard.css     # Feature card styles
│       ├── Footer.css          # Footer styles
│       ├── GmailPanel.css      # Gmail panel styles
│       ├── HeyGenAvatar.css    # HeyGen avatar styles
│       ├── HomePage.css        # Landing page styles
│       ├── Navbar.css          # Navigation styles
│       ├── SettingsPage.css    # Settings page styles
│       ├── Sidebar.css         # Sidebar styles
│       ├── StaticAvatar.css    # Static avatar styles
│       └── VoiceControls.css   # Voice controls styles
└── public/                     # Static assets
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Running backend API
- Supabase project configured

### 1. Environment Setup

#### Development Environment
```bash
cd frontend
cp .env.example .env
```

Edit `.env` for local development:
```bash
# Backend API (Local)
VITE_BACKEND_URL=http://localhost:8000

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# HeyGen Avatar (Optional)
VITE_HEYGEN_API_KEY=your-heygen-api-key
VITE_HEYGEN_AVATAR_ID=your-avatar-id

# Feature Flags
VITE_USE_STATIC_AVATAR=true
VITE_SHOW_AVATAR_TOGGLE=true
VITE_DEBUG_AVATAR_API=true
```

#### Production Environment
```bash
cp .env.production.example .env.production
```

Edit `.env.production` for production deployment:
```bash
# Backend API (Production)
VITE_BACKEND_URL=https://your-backend-url.run.app

# Supabase Configuration (Same as development)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# HeyGen Avatar (Production)
VITE_HEYGEN_API_KEY=your-heygen-api-key
VITE_HEYGEN_AVATAR_ID=your-avatar-id

# Feature Flags (Production)
VITE_USE_STATIC_AVATAR=false
VITE_SHOW_AVATAR_TOGGLE=false
VITE_DEBUG_AVATAR_API=false
VITE_CACHE_AVATAR_IMAGES=true
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

### 4. Access Application

Open [http://localhost:5173](http://localhost:5173) in your browser.

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

## 🎨 Key Components

### Avatar System
```typescript
// Avatar wrapper component
<Avatar
  type="static" // or "heygen"
  isListening={isListening}
  isSpeaking={isSpeaking}
  onReady={handleReady}
/>

// Static avatar for simple interactions
<StaticAvatar
  isListening={isListening}
  isSpeaking={isSpeaking}
  onAvatarReady={handleReady}
/>

// HeyGen streaming avatar for advanced features
<HeyGenAvatar
  isListening={isListening}
  onAvatarReady={handleReady}
  onAvatarStartTalking={handleStartTalking}
/>
```

### Voice Interaction
```typescript
// Voice controls component
<VoiceControls
  isListening={isListening}
  onStartListening={handleStartListening}
  onStopListening={handleStopListening}
  isAvatarSpeaking={isSpeaking}
/>
```

### Authentication Flow
```typescript
// AuthContext provides authentication state
const { user, login, logout, userProfile } = useAuth();

// ProtectedRoute wraps authenticated pages
<ProtectedRoute>
  <DashboardPage />
</ProtectedRoute>

// UnauthenticatedNavbar for logged-out users
<UnauthenticatedNavbar />
```

### Gmail Integration
```typescript
// Gmail panel component
<GmailPanel
  isConnected={isGmailConnected}
  onConnect={handleGmailConnect}
  emails={recentEmails}
/>

// OAuth API service
import { connectGmail, disconnectGmail } from './services/oauthApi';
```

### Session Management
```typescript
// Session state management in DashboardPage
const [sessions, setSessions] = useState<Session[]>([]);
const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
const [messages, setMessages] = useState<Message[]>([]);
```

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
```css
/* Global variables in index.css */
:root {
  --primary-blue: #5b7cff;
  --primary-teal: #14b8a6;
  --background: #ffffff;
  --text: #374151;
  --border: #e5e7eb;
}

/* Component-specific styles in separate files */
@import './styles/DashboardPage.css';
@import './styles/Sidebar.css';
```

### Component Styling
- **CSS Modules** for component isolation
- **Tailwind utilities** for common patterns
- **Custom CSS** for complex layouts
- **Animation classes** for smooth transitions

## 🧪 Development

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

### Adding New Components

1. **Create component** in `src/components/`
```typescript
// Example: NewComponent.tsx
interface NewComponentProps {
  title: string;
  onAction: () => void;
}

const NewComponent: React.FC<NewComponentProps> = ({ title, onAction }) => {
  return (
    <div className="new-component">
      <h2>{title}</h2>
      <Button onClick={onAction}>Action</Button>
    </div>
  );
};

export default NewComponent;
```

2. **Add TypeScript types** in `src/types/` if complex
```typescript
// types/newComponent.types.ts
export interface NewComponentConfig {
  theme: 'light' | 'dark';
  animation: boolean;
}
```

3. **Add styles** in `src/styles/`
```css
/* styles/NewComponent.css */
.new-component {
  /* Tailwind + custom styles */
}
```

4. **Add services** in `src/services/` for API calls
```typescript
// services/newApi.ts
export const fetchNewData = async () => {
  // API integration logic
};
```

5. **Add utilities** in `src/utils/` for helper functions
```typescript
// utils/newHelpers.ts
export const formatNewData = (data: any) => {
  // Helper function logic
};
```

6. **Export and use** in pages or other components

## 🔧 Architecture Details

### Services Layer (`src/services/`)
- **`oauthApi.ts`** - OAuth integration API calls
  - Gmail connection/disconnection
  - Calendar authorization
  - Token management

### Type Definitions (`src/types/`)
- **`staticAvatar.types.ts`** - TypeScript types for avatar system
  - Avatar configuration interfaces
  - Avatar state management types
  - Event handler definitions

### Utilities (`src/utils/`)
- **`emailConfig.ts`** - Email configuration and validation
- **`staticAvatarAPI.ts`** - Static avatar API functions
  - Text-to-speech utilities
  - Avatar animation controls
  - Voice synthesis helpers

### State Management Patterns

```typescript
// Context for global state (AuthContext)
const AuthContext = createContext<AuthContextType>();

// Local state for component-specific data
const [isLoading, setIsLoading] = useState(false);

// Custom hooks for reusable logic
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Service integration
import { connectGmail } from '../services/oauthApi';
import { speakText } from '../utils/staticAvatarAPI';
```

## 🔊 Voice Integration

### Speech Recognition
```typescript
// Voice command processing
const handleVoiceInput = (transcript: string) => {
  // Send to backend for processing
  // Update conversation state
  // Trigger avatar response
};
```

### Text-to-Speech
```typescript
// Avatar speech synthesis
const handleAvatarSpeak = (text: string) => {
  if (useStaticAvatar) {
    // Browser TTS
    speechSynthesis.speak(utterance);
  } else {
    // HeyGen streaming avatar
    avatarRef.current?.speak(text);
  }
};
```

## 🚨 Troubleshooting

### Common Issues

**Build Errors**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# TypeScript errors
npm run type-check

# Check for missing dependencies
npm audit
```

**Environment Variables Not Loading**
```bash
# Ensure variables start with VITE_
echo $VITE_BACKEND_URL

# Check file names (.env for dev, .env.production for prod)
ls -la .env*

# Restart dev server after changes
npm run dev
```

**Authentication Issues**
```bash
# Verify Supabase URL and keys
console.log(import.meta.env.VITE_SUPABASE_URL);

# Check CORS configuration in Supabase dashboard
# Ensure backend is running and accessible
curl http://localhost:8000/api/v1/health/ping
```

**Avatar Not Working**
```bash
# Check HeyGen API credentials
console.log(import.meta.env.VITE_HEYGEN_API_KEY);

# Test with static avatar first
VITE_USE_STATIC_AVATAR=true

# Check browser console for avatar errors
# Verify microphone permissions in browser
```

**OAuth Integration Issues**
```bash
# Check Gmail OAuth configuration
# Verify redirect URIs in Google Cloud Console
# Test OAuth API endpoints
curl http://localhost:8000/api/v1/oauth/connect/gmail
```

**Production vs Development Issues**
```bash
# Ensure correct environment file is used
# Development: .env
# Production: .env.production

# Check backend URL configuration
# Dev: http://localhost:8000
# Prod: https://your-backend.run.app

# Verify CORS settings match frontend domain
```

### Debug Tools

```typescript
// Environment variable debugging
console.log('Environment:', import.meta.env.MODE);
console.log('Backend URL:', import.meta.env.VITE_BACKEND_URL);
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL);

// Supabase client debugging
import { supabase } from './supabaseClient';
console.log('Supabase session:', await supabase.auth.getSession());

// OAuth API debugging
import { connectGmail } from './services/oauthApi';
// Check Network tab for API calls

// Avatar API debugging
import { speakText } from './utils/staticAvatarAPI';
// Check console for TTS errors
```

### Environment Testing

Use the `EnvTest` component to verify configuration:
```typescript
import EnvTest from './components/EnvTest';

// Add to any page during development
<EnvTest />
```

## 🏭 Production Build

### Environment-Specific Builds

**Development Build**
```bash
# Uses .env file
npm run dev
```

**Production Build**
```bash
# Uses .env.production file
npm run build
```

### Build Process
```bash
# Install dependencies
npm install

# Run production build
npm run build

# Preview production build locally
npm run preview
```

### Build Output
- Static files in `dist/` folder
- Optimized and minified code
- Source maps for debugging (if enabled)
- Environment variables baked into build

### Deployment Options

**Vercel (Recommended)**
```bash
# 1. Connect GitHub repo to Vercel
# 2. Configure environment variables in Vercel dashboard:
#    - Copy values from .env.production.example
#    - Set VITE_BACKEND_URL to your production backend
# 3. Auto-deploys on push to main branch

# Manual deployment:
npm run build
npx vercel --prod
```

**Netlify**
```bash
# 1. Connect GitHub repo or drag/drop dist/ folder
# 2. Configure build settings:
#    - Build command: npm run build
#    - Publish directory: dist
# 3. Set environment variables in Netlify dashboard
```

**Google Cloud Storage + CDN**
```bash
# Build the application
npm run build

# Upload to Cloud Storage
gsutil -m cp -r dist/* gs://your-bucket-name/

# Configure CDN and custom domain
gcloud compute url-maps create frontend-map
```

**Docker Deployment**
```dockerfile
# Use nginx to serve static files
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Production Configuration

**Environment Variables in Production:**
- Use `.env.production` file during build
- Set `VITE_BACKEND_URL` to production backend URL
- Disable debug flags (`VITE_DEBUG_AVATAR_API=false`)
- Enable production optimizations (`VITE_CACHE_AVATAR_IMAGES=true`)

**CORS Configuration:**
- Update Supabase CORS settings to include production domain
- Configure backend CORS to allow frontend domain
- Ensure all OAuth redirect URIs include production URLs

For deployment and production setup, see the [self-hosting guide](../docs/self-hosting.md).