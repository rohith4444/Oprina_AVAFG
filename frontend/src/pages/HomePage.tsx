// ✅ FIXED SignupPage.tsx + HomePage.tsx integration
import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Mic, Zap, Shield, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Logo from '../components/Logo';
import Button from '../components/Button';
import FeatureCard from '../components/FeatureCard';
import MinimalFooter from '../components/MinimalFooter';
import StaticAvatar, { StaticAvatarRef } from '../components/StaticAvatar';
import '../styles/HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [avatarReady, setAvatarReady] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const avatarRef = useRef<StaticAvatarRef>(null);

  const handleAvatarReady = () => {
    setAvatarReady(true);
    if (avatarRef.current) {
      avatarRef.current.speak("Welcome to Oprina! I'm your conversational AI avatar assistant.");
    }
  };

  const handleAvatarStartTalking = () => {
    setIsSpeaking(true);
  };

  const handleAvatarStopTalking = () => {
    setIsSpeaking(false);
  };

  return (
    <div className="home-page">
      <Navbar LogoComponent={Logo} />

      <section className="hero">
        <div className="hero-content">
          <div className="hero-grid">
            <div className="hero-avatar-container">
              <StaticAvatar
                ref={avatarRef}
                isListening={false}
                isSpeaking={isSpeaking}
                onAvatarReady={handleAvatarReady}
                onAvatarStartTalking={handleAvatarStartTalking}
                onAvatarStopTalking={handleAvatarStopTalking}
              />
            </div>
            <div className="hero-text-content">
              <h1 className="hero-title">
                <span className="gradient-text">Conversational AI Avatar Assistant</span>
              </h1>
              <p className="hero-subtitle">
                It's the first one of its kind.
              </p>
              <Button
                variant="primary"
                className="hero-cta"
                onClick={() => navigate('/signup')}
              >
                Try Oprina <ArrowRight className="ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="container">
          <h2 className="section-title">Why Choose Oprina</h2>
          <div className="features-grid">
            <FeatureCard
              icon={<Mic />}
              title="Natural Voice Control"
              description="Use your voice to manage emails, schedule meetings, and more with natural language commands."
            />
            <FeatureCard
              icon={<Mail />}
              title="Seamless Integration"
              description="Connect with Gmail and Google Calendar to streamline your communication and scheduling."
            />
            <FeatureCard
              icon={<Zap />}
              title="Smart Suggestions"
              description="AI-powered insights help you write emails, book meetings, and respond faster."
            />
          </div>
        </div>
      </section>

      <section className="how-it-works">
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3 className="step-title">Connect Your Google Account</h3>
              <p className="step-description">
                Securely link Gmail and Calendar to start using Oprina.
              </p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h3 className="step-title">Talk to Oprina</h3>
              <p className="step-description">
                Use natural commands like "Schedule a meeting at 3PM" or "Show unread emails."
              </p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h3 className="step-title">Boost Your Productivity</h3>
              <p className="step-description">
                Let Oprina handle your messages and meetings while you stay focused.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to experience Oprina?</h2>
            <p className="cta-subtitle">
              Save time and stay organized with voice-powered actions on email and calendar tools — powered by Oprina.
            </p>
            <Button
              variant="primary"
              className="cta-button"
              onClick={() => navigate('/signup')}
            >
              Get Started for Free
            </Button>
            <p className="cta-device-notice">
              💻 For better experience, please use login on desktop and laptops only!
            </p>
          </div>
        </div>
      </section>
      
      <section className="updates-section">
        <div className="container">
          <h2 className="updates-title">Exciting Updates Coming Soon!</h2>
          <div className="updates-pills">
            <div className="update-pill">Limitless Avatar Conversations</div>
            <div className="update-pill">Customizable Email & Calendar Workflows</div>
            <div className="update-pill">Desktop App Experience</div>
          </div>
        </div>
      </section>

      <MinimalFooter />
    </div>
  );
};

export default HomePage;