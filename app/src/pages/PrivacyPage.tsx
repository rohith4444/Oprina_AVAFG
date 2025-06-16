import React from 'react';
import Navbar from '../components/Navbar';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/AuthPages.css';

const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="auth-page flex-1">
        <div className="auth-container">
        <div className="auth-card" style={{ maxWidth: '800px' }}>
          <h1 className="auth-title">Privacy Policy</h1>
          <p className="auth-subtitle">Last updated: {new Date().toLocaleDateString()}</p>
          
          <div style={{ textAlign: 'left', lineHeight: '1.6', color: '#374151' }}>
            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                1. Information We Collect
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We collect information you provide directly to us, such as when you create an account, use our services, or contact us for support.
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Account information (email address, password)</li>
                <li>Profile information (name, preferences)</li>
                <li>Voice recordings (processed locally, not stored)</li>
                <li>Usage data and analytics</li>
              </ul>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                2. Gmail Data Access
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                When you connect your Gmail account, we access your email data solely to provide voice assistant functionality:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Read email messages and metadata</li>
                <li>Search through your emails</li>
                <li>Compose and send emails on your behalf</li>
                <li>Organize and manage your inbox</li>
              </ul>
              <p style={{ marginBottom: '1rem' }}>
                <strong>Important:</strong> We do not store your email content on our servers. All email processing happens in real-time and is not retained.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                3. How We Use Your Information
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We use the information we collect to:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Provide, maintain, and improve our services</li>
                <li>Process voice commands and generate responses</li>
                <li>Authenticate and authorize access to your accounts</li>
                <li>Send you technical notices and support messages</li>
                <li>Analyze usage patterns to improve user experience</li>
              </ul>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                4. Voice Data Processing
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                Voice recordings are processed using browser-based speech recognition technology. Voice data is:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Processed locally in your browser when possible</li>
                <li>Transmitted securely for speech recognition services</li>
                <li>Not stored permanently on our servers</li>
                <li>Used only for immediate command processing</li>
              </ul>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                5. Data Sharing and Disclosure
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We do not sell, trade, or otherwise transfer your personal information to third parties except:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>With your explicit consent</li>
                <li>To comply with legal obligations</li>
                <li>To protect our rights and safety</li>
                <li>With trusted service providers who assist in our operations</li>
              </ul>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                6. Data Security
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We implement appropriate security measures to protect your personal information:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Encryption of data in transit and at rest</li>
                <li>Secure authentication protocols</li>
                <li>Regular security audits and updates</li>
                <li>Limited access to personal data by authorized personnel</li>
              </ul>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                7. Third-Party Services
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                Our service integrates with third-party providers:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li><strong>Google:</strong> For Gmail access and authentication</li>
                <li><strong>Supabase:</strong> For user authentication and account management</li>
                <li><strong>HeyGen:</strong> For avatar generation and animation</li>
              </ul>
              <p style={{ marginBottom: '1rem' }}>
                These services have their own privacy policies, which we encourage you to review.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                8. Your Rights and Choices
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                You have the right to:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Access and update your personal information</li>
                <li>Delete your account and associated data</li>
                <li>Revoke Gmail access permissions</li>
                <li>Opt out of non-essential communications</li>
                <li>Request a copy of your data</li>
              </ul>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                9. Data Retention
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We retain your information only as long as necessary to provide our services and comply with legal obligations. Account data is deleted within 30 days of account deletion.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                10. Changes to This Policy
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page and updating the "Last updated" date.
              </p>
            </section>

            <section style={{ marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem', color: '#1f2937' }}>
                11. Contact Us
              </h2>
              <p style={{ marginBottom: '1rem' }}>
                If you have any questions about this Privacy Policy, please contact us at:
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li>Email: privacy@oprina.com</li>
                <li>Support: support@oprina.com</li>
              </ul>
            </section>
          </div>
        </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default PrivacyPage; 