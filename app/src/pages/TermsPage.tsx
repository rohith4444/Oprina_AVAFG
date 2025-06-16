import React from 'react';
import Navbar from '../components/Navbar';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/AuthPages.css';

const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="auth-page flex-1">
        <div className="auth-container">
        <div className="auth-card" style={{ maxWidth: '800px' }}>
          <h1 className="auth-title">Terms of Service</h1>
          <p className="auth-subtitle">Last updated: {new Date().toLocaleDateString()}</p>
          
          <div style={{ textAlign: 'left', lineHeight: '1.6', color: '#374151' }}>
            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                1. Acceptance of Terms
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                By accessing and using Oprina ("the Service"), you accept and agree to be bound by the terms and provision of this agreement.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                2. Description of Service
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                Oprina is a voice-powered Gmail assistant that allows users to manage their email through natural conversation with an AI-powered avatar. The service includes voice recognition, email management, and AI-generated responses.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                3. User Accounts
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                To use certain features of the Service, you must register for an account. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                4. Gmail Integration
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                Our service integrates with Gmail through Google's OAuth2 system. We only access your Gmail data with your explicit permission and use it solely to provide the voice assistant functionality.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                5. Privacy and Data Protection
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the Service, to understand our practices.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                6. Prohibited Uses
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                You may not use the Service for any unlawful purpose or to solicit others to perform unlawful acts. You may not transmit any worms, viruses, or any code of a destructive nature.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                7. Disclaimer of Warranties
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                The Service is provided "as is" without any representations or warranties, express or implied. We make no representations or warranties in relation to this Service or the information and materials provided on this Service.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                8. Limitation of Liability
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                In no event shall Oprina, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, punitive, special, or consequential damages.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                9. Changes to Terms
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We reserve the right to modify these terms at any time. We will notify users of any significant changes via email or through the Service.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                10. Contact Information
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                If you have any questions about these Terms of Service, please contact us at support@oprina.com.
              </p>
            </section>
          </div>
        </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default TermsPage; 