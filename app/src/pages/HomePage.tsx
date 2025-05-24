import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Mic, Zap, Shield } from 'lucide-react';
import Navbar from '../components/Navbar';
import Button from '../components/Button';
import FeatureCard from '../components/FeatureCard';
import Footer from '../components/Footer';
import '../styles/HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="home-page">
      <Navbar />
      
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            <span>Oprina</span>
          </h1>
          <h2 className="hero-tagline">
            <span className="gradient-text">Voice-Powered Gmail Assistant</span>
          </h2>
          <p className="hero-subtitle">
            Manage your inbox through natural conversation with an intelligent, visual assistant
          </p>
          <Button 
            variant="primary" 
            className="hero-cta"
            onClick={() => navigate('/signup')}
          >
            Try Oprina
          </Button>
        </div>
      </section>
      
      <section className="features">
        <div className="container">
          <h2 className="section-title">Why Choose Oprina</h2>
          <div className="features-grid">
            <FeatureCard 
              icon={<Mic />}
              title="Natural Voice Control"
              description="Use your voice to compose, read, and manage emails with natural language commands."
            />
            <FeatureCard 
              icon={<Mail />}
              title="Seamless Gmail Integration"
              description="Connect directly to your Gmail account for instant access to your inbox."
            />
            <FeatureCard 
              icon={<Zap />}
              title="Intelligent Responses"
              description="AI-powered suggestions help you respond to emails quickly and effectively."
            />
            <FeatureCard 
              icon={<Shield />}
              title="Secure & Private"
              description="Your data is encrypted and protected. We never store your emails or content."
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
              <h3 className="step-title">Connect Your Gmail</h3>
              <p className="step-description">
                Securely link your Gmail account to Oprina with just a few clicks.
              </p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h3 className="step-title">Ask Oprina</h3>
              <p className="step-description">
                Speak naturally to Oprina about your emails and what you need.
              </p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h3 className="step-title">Get Things Done</h3>
              <p className="step-description">
                Let Oprina handle your email tasks while you focus on what matters.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      <section className="cta-section">
        <div className="container">
          <div className="cta-card">
            <h2 className="cta-title">Ready to experience Oprina?</h2>
            <p className="cta-text">
              Join thousands of users who are already saving time with voice-powered email management.
            </p>
            <Button 
              variant="primary" 
              className="cta-button"
              onClick={() => navigate('/signup')}
            >
              Get Started for Free
            </Button>
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
};

export default HomePage;