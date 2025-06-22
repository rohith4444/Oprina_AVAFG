// Setup type definitions for built-in Supabase Runtime APIs
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

// Type declarations for Deno
declare global {
  const Deno: {
    env: {
      get(key: string): string | undefined;
    };
    serve(handler: (req: Request) => Promise<Response> | Response): void;
  };
}

const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY');

Deno.serve(async (req) => {
  console.log("🚀 Welcome email function called");

  // Handle CORS for local development
  if (req.method === 'OPTIONS') {
    return new Response('ok', { 
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      }
    });
  }

  try {
    // Check if API key is configured
    if (!RESEND_API_KEY) {
      console.error('❌ RESEND_API_KEY not found');
      return new Response(JSON.stringify({ error: 'Email service not configured' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get email and optional name from request
    const { email, name } = await req.json();
    console.log(`📧 Sending welcome email to: ${email}`);

    if (!email) {
      return new Response(JSON.stringify({ error: 'Email is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Prepare welcome email content
    const welcomeEmail = {
      from: 'Oprina <hello@oprinaai.com>',
      reply_to: ['oprina123789@gmail.com'],
      to: [email],
      subject: 'Welcome to Oprina',
      html: `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width,initial-scale=1" />
          <title>Welcome to Oprina</title>
          <style>
            body {
              background: #f8fafc;
              margin: 0;
              padding: 0;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
              color: #1e293b;
              line-height: 1.6;
            }
            .container {
              max-width: 600px;
              margin: 40px auto;
              background: #ffffff;
              border-radius: 12px;
              overflow: hidden;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            .header {
              background: linear-gradient(135deg, #3B82F6 0%, #10B981 100%);
              padding: 32px 40px;
              text-align: center;
            }
            .logo-container {
              display: flex;
              align-items: center;
              justify-content: center;
              margin-bottom: 16px;
            }
            .logo {
              width: 48px;
              height: 48px;
              margin-right: 12px;
            }
            .brand-name {
              font-size: 28px;
              font-weight: 700;
              color: #ffffff;
              letter-spacing: -0.5px;
            }
            .header-title {
              font-size: 24px;
              font-weight: 600;
              color: #ffffff;
              margin: 0;
            }
            .header-subtitle {
              font-size: 16px;
              color: rgba(255, 255, 255, 0.9);
              margin: 8px 0 0 0;
              font-weight: 400;
            }
            .content {
              padding: 40px;
            }
            .welcome-section {
              margin-bottom: 32px;
            }
            .welcome-heading {
              font-size: 20px;
              font-weight: 600;
              color: #1e293b;
              margin: 0 0 16px 0;
            }
            .welcome-text {
              font-size: 16px;
              color: #475569;
              margin: 0 0 32px 0;
            }
            .features-section {
              margin-bottom: 32px;
            }
            .section-title {
              font-size: 18px;
              font-weight: 600;
              color: #1e293b;
              margin: 0 0 20px 0;
            }
            .features-grid {
              display: grid;
              gap: 16px;
            }
            .feature-item {
              display: flex;
              align-items: flex-start;
              padding: 16px;
              background: #f8fafc;
              border-radius: 8px;
              border-left: 4px solid #3B82F6;
            }
            .feature-emoji {
              font-size: 20px;
              margin-right: 12px;
              line-height: 1;
            }
            .feature-content {
              flex: 1;
            }
            .feature-title {
              font-size: 15px;
              font-weight: 600;
              color: #1e293b;
              margin: 0 0 4px 0;
            }
            .feature-description {
              font-size: 14px;
              color: #64748b;
              margin: 0;
            }
            .cta-section {
              text-align: center;
              margin: 32px 0;
            }
            .cta-button {
              display: inline-block;
              background: linear-gradient(135deg, #3B82F6 0%, #10B981 100%);
              color: #ffffff;
              font-size: 16px;
              font-weight: 600;
              text-decoration: none;
              padding: 14px 32px;
              border-radius: 8px;
              transition: transform 0.2s, box-shadow 0.2s;
            }
            .cta-button:hover {
              transform: translateY(-1px);
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            }
            .quickstart-section {
              background: #f1f5f9;
              border-radius: 8px;
              padding: 24px;
              margin: 32px 0;
            }
            .quickstart-title {
              font-size: 16px;
              font-weight: 600;
              color: #1e293b;
              margin: 0 0 16px 0;
            }
            .quickstart-list {
              margin: 0;
              padding-left: 20px;
              color: #475569;
            }
            .quickstart-list li {
              margin-bottom: 8px;
              font-size: 14px;
            }
            .footer {
              background: #18181b;
              color: #a1a1aa;
              text-align: center;
              padding: 24px 40px;
              font-size: 14px;
            }
            .footer a {
              color: #10b981;
              text-decoration: none;
            }
            .footer a:hover {
              text-decoration: underline;
            }
            @media (max-width: 640px) {
              .container {
                margin: 20px;
                border-radius: 8px;
              }
              .header, .content, .footer {
                padding: 24px 20px;
              }
              .brand-name {
                font-size: 24px;
              }
              .header-title {
                font-size: 20px;
              }
              .features-grid {
                gap: 12px;
              }
              .feature-item {
                padding: 12px;
              }
            }
          </style>
        </head>
        <body>
          <div class="container">
            <!-- Header -->
            <div class="header">
              <div class="logo-container">
                <svg class="logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="24" cy="24" r="20" stroke="#ffffff" stroke-width="3" fill="none"/>
                  <circle cx="24" cy="24" r="6" fill="#ffffff"/>
                  <path d="M24 4 L26 8 L24 12 L22 8 Z" fill="#ffffff"/>
                  <path d="M44 24 L40 26 L36 24 L40 22 Z" fill="#ffffff"/>
                </svg>
                <div class="brand-name">Oprina</div>
              </div>
              <h1 class="header-title">Welcome to Oprina</h1>
              <p class="header-subtitle">Your Conversational AI Avatar Assistant</p>
            </div>

            <!-- Content -->
            <div class="content">
              <!-- Welcome Message -->
              <div class="welcome-section">
                <h2 class="welcome-heading">🎉 You're all set!</h2>
                <p class="welcome-text">
                  Thank you for joining Oprina. Your account has been successfully created and verified. You're now ready to unlock the future of AI-powered productivity.
                </p>
              </div>

              <!-- What You Can Do Section -->
              <div class="features-section">
                <h3 class="section-title">What You Can Do Now</h3>
                <div class="features-grid">
                  <div class="feature-item">
                    <span class="feature-emoji">🗣️</span>
                    <div class="feature-content">
                      <h4 class="feature-title">Voice Interaction</h4>
                      <p class="feature-description">Talk naturally to manage your Gmail and Calendar.</p>
                    </div>
                  </div>
                  <div class="feature-item">
                    <span class="feature-emoji">📧</span>
                    <div class="feature-content">
                      <h4 class="feature-title">Email Assistant</h4>
                      <p class="feature-description">Compose, read, and reply with voice commands.</p>
                    </div>
                  </div>
                  <div class="feature-item">
                    <span class="feature-emoji">📆</span>
                    <div class="feature-content">
                      <h4 class="feature-title">Calendar Scheduling</h4>
                      <p class="feature-description">Schedule meetings directly with natural voice prompts.</p>
                    </div>
                  </div>
                  <div class="feature-item">
                    <span class="feature-emoji">🤖</span>
                    <div class="feature-content">
                      <h4 class="feature-title">AI Suggestions</h4>
                      <p class="feature-description">Get smart responses and productivity nudges.</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Call-to-Action -->
              <div class="cta-section">
                <a href="http://localhost:5173/get-started" class="cta-button">Get Started with Oprina</a>
              </div>

              <!-- Quick Start Tips -->
              <div class="quickstart-section">
                <h3 class="quickstart-title">🧭 Quick Start Tips</h3>
                <ul class="quickstart-list">
                  <li>Connect Gmail & Calendar</li>
                  <li>Try Voice Control</li>
                  <li>Customize Your Preferences</li>
                  <li>Contact Support if Needed</li>
                </ul>
              </div>
            </div>

            <!-- Footer -->
            <div class="footer">
              <p>
                Need help? <a href="http://localhost:5173/contact">Contact Support</a>
              </p>
              <p>© 2025 Oprina. All rights reserved.</p>
            </div>
          </div>
        </body>
        </html>
      `,
      text: `
Welcome to Oprina
Your Conversational AI Avatar Assistant

🎉 You're all set!

Hi${name ? ` ${name}` : ''}!

Thank you for joining Oprina. Your account has been successfully created and verified. You're now ready to unlock the future of AI-powered productivity.

What You Can Do Now:

🗣️ Voice Interaction: Talk naturally to manage your Gmail and Calendar.

📧 Email Assistant: Compose, read, and reply with voice commands.

📆 Calendar Scheduling: Schedule meetings directly with natural voice prompts.

🤖 AI Suggestions: Get smart responses and productivity nudges.

🚀 Get Started with Oprina: http://localhost:5173/get-started

🧭 Quick Start Tips:
• Connect Gmail & Calendar
• Try Voice Control
• Customize Your Preferences
• Contact Support if Needed

Need help? Contact Support: http://localhost:5173/contact

© ${new Date().getFullYear()} Oprina. All rights reserved.
      `
    };

    console.log('📤 Sending email via Resend API...');

    // Send email via Resend
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${RESEND_API_KEY}`
      },
      body: JSON.stringify(welcomeEmail)
    });

    const result = await response.json();
    console.log('📬 Resend API response:', result);

    if (!response.ok) {
      console.error('❌ Resend API error:', result);
      return new Response(JSON.stringify({ 
        error: 'Failed to send welcome email', 
        details: result 
      }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    console.log('✅ Welcome email sent successfully!');
    return new Response(JSON.stringify({ 
      success: true, 
      message: 'Welcome email sent successfully',
      emailId: result.id
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });

  } catch (error) {
    console.error('💥 Error in welcome email function:', error);
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}); 