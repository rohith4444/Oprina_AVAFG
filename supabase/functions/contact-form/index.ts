import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from 'jsr:@supabase/supabase-js@2';

console.log("📞 Contact form function started");

const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY');
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

// Initialize Supabase client with service role key for admin operations
const supabase = createClient(
  SUPABASE_URL!,
  SUPABASE_SERVICE_ROLE_KEY!
);

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { 
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      }
    });
  }

  try {
    console.log("Processing contact form submission");
    
    if (!RESEND_API_KEY) {
      console.error('❌ RESEND_API_KEY not found');
      return new Response(JSON.stringify({ error: 'Email service not configured' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const { fullName, email, phone, subject, message } = await req.json();
    console.log(`📝 Processing contact form from: ${email}`);

    // Validate required fields
    if (!fullName || !email || !message) {
      return new Response(JSON.stringify({ error: 'Name, email, and message are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get and increment case ID
    let caseId = 1;
    
    try {
      // First, try to get the current case counter
      const { data: counterData, error: counterError } = await supabase
        .from('case_counter')
        .select('last_case_id')
        .single();

      if (counterError && counterError.code !== 'PGRST116') { // PGRST116 = no rows returned
        console.error('Error fetching case counter:', counterError);
      }

      if (counterData) {
        caseId = counterData.last_case_id + 1;
        
        // Update the counter
        const { error: updateError } = await supabase
          .from('case_counter')
          .update({ last_case_id: caseId })
          .eq('id', 1);

        if (updateError) {
          console.error('Error updating case counter:', updateError);
        }
      } else {
        // Initialize counter if it doesn't exist
        const { error: insertError } = await supabase
          .from('case_counter')
          .insert({ id: 1, last_case_id: 1 });

        if (insertError) {
          console.error('Error initializing case counter:', insertError);
        }
      }
    } catch (error) {
      console.error('Case ID generation error:', error);
      // Fallback to timestamp-based ID if database is not available
      caseId = Math.floor(Date.now() / 1000);
    }

    console.log(`📋 Generated Case ID: #${caseId}`);

    // Store the contact submission
    try {
      const { error: submissionError } = await supabase
        .from('contact_submissions')
        .insert({
          case_id: caseId,
          full_name: fullName,
          email: email,
          phone: phone || null,
          subject: subject || 'General Inquiry',
          message: message,
          created_at: new Date().toISOString()
        });

      if (submissionError) {
        console.error('Error storing submission:', submissionError);
      }
    } catch (error) {
      console.error('Database storage error:', error);
      // Continue with email sending even if storage fails
    }

    // Send email to support team
    const supportEmail = {
      from: 'Oprina Contact Form <hello@oprinaai.com>',
      to: ['oprina123789@gmail.com'],
      subject: `Oprina Support Case #${caseId} - ${subject || 'General Inquiry'}`,
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>New Support Case</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <div style="background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">🎧 New Support Case</h1>
          </div>
          
          <div style="border: 1px solid #e5e7eb; border-top: none; padding: 30px; border-radius: 0 0 8px 8px;">
            <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin-bottom: 25px;">
              <h2 style="margin: 0; color: #92400e; font-size: 18px;">Case ID: #${caseId}</h2>
            </div>
            
            <div style="space-y: 15px;">
              <div style="margin-bottom: 15px;">
                <strong style="color: #374151;">Name:</strong> ${fullName}
              </div>
              <div style="margin-bottom: 15px;">
                <strong style="color: #374151;">Email:</strong> ${email}
              </div>
              ${phone ? `<div style="margin-bottom: 15px;"><strong style="color: #374151;">Phone:</strong> ${phone}</div>` : ''}
              <div style="margin-bottom: 15px;">
                <strong style="color: #374151;">Subject:</strong> ${subject || 'General Inquiry'}
              </div>
              <div style="margin-bottom: 15px;">
                <strong style="color: #374151;">Submitted:</strong> ${new Date().toLocaleString()}
              </div>
            </div>
            
            <div style="margin-top: 25px;">
              <strong style="color: #374151; display: block; margin-bottom: 10px;">Message:</strong>
              <div style="background: #f9fafb; padding: 15px; border-radius: 6px; border-left: 4px solid #2563eb;">
                ${message.replace(/\n/g, '<br>')}
              </div>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #eff6ff; border-radius: 6px;">
              <h3 style="margin: 0 0 10px 0; color: #1e40af;">📋 Next Steps:</h3>
                             <ul style="margin: 0; color: #1e40af;">
                 <li>Target response time: Within 48 hours</li>
                 <li>Reply to customer at: ${email}</li>
                 <li>Reference Case ID: #${caseId} in all communications</li>
               </ul>
            </div>
          </div>
        </body>
        </html>
      `,
      text: `
New Support Case #${caseId}

Customer Details:
- Name: ${fullName}
- Email: ${email}
${phone ? `- Phone: ${phone}` : ''}
- Subject: ${subject || 'General Inquiry'}
- Submitted: ${new Date().toLocaleString()}

Message:
${message}

Next Steps:
- Target response time: Within 48 hours
- Reply to customer at: ${email}
- Reference Case ID: #${caseId} in all communications
      `
    };

    // Send confirmation email to user
    const confirmationEmail = {
      from: 'Oprina Support <hello@oprinaai.com>',
      to: [email],
      subject: `Case #${caseId} - We've received your message`,
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Support Case Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2563eb; margin: 0;">✅ Message Received!</h1>
          </div>
          
          <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 30px;">
            <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
              Hi ${fullName},
            </p>
            
            <p style="color: #4b5563; margin-bottom: 25px;">
              Thank you for contacting Oprina! We've received your message and have assigned it Case ID <strong>#${caseId}</strong>.
            </p>
            
            <div style="background: #f0f9ff; padding: 20px; border-radius: 6px; border-left: 4px solid #2563eb; margin: 25px 0;">
              <h3 style="margin: 0 0 10px 0; color: #1e40af;">📋 Case Summary:</h3>
              <p style="margin: 5px 0; color: #1e40af;"><strong>Case ID:</strong> #${caseId}</p>
              <p style="margin: 5px 0; color: #1e40af;"><strong>Subject:</strong> ${subject || 'General Inquiry'}</p>
              <p style="margin: 5px 0; color: #1e40af;"><strong>Submitted:</strong> ${new Date().toLocaleString()}</p>
            </div>
            
            <div style="background: #fef3c7; padding: 15px; border-radius: 6px; margin: 25px 0;">
              <h3 style="margin: 0 0 10px 0; color: #92400e;">⏰ What happens next?</h3>
              <ul style="margin: 0; color: #92400e;">
                <li>Our support team will review your message</li>
                <li>We'll get back to you within <strong>48 hours</strong></li>
                <li>All replies will reference Case ID #${caseId}</li>
              </ul>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
              Need to add more information to this case? Simply reply to this email and mention Case ID #${caseId}.
            </p>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
              <p style="color: #9ca3af; font-size: 14px; margin: 0;">
                Best regards,<br>
                The Oprina Support Team
              </p>
            </div>
          </div>
        </body>
        </html>
      `,
      text: `
Hi ${fullName},

Thank you for contacting Oprina! We've received your message and have assigned it Case ID #${caseId}.

Case Summary:
- Case ID: #${caseId}
- Subject: ${subject || 'General Inquiry'}
- Submitted: ${new Date().toLocaleString()}

What happens next?
- Our support team will review your message
- We'll get back to you within 48 hours
- All replies will reference Case ID #${caseId}

Need to add more information to this case? Simply reply to this email and mention Case ID #${caseId}.

Best regards,
The Oprina Support Team
      `
    };

    console.log('📤 Sending support notification email...');

    // Send support email
    const supportResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(supportEmail),
    });

    const supportResult = await supportResponse.json();

    if (!supportResponse.ok) {
      console.error('❌ Failed to send support email:', supportResult);
    } else {
      console.log('✅ Support notification sent:', supportResult.id);
    }

    console.log('📤 Sending confirmation email to user...');

    // Send confirmation email
    const confirmResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(confirmationEmail),
    });

    const confirmResult = await confirmResponse.json();

    if (!confirmResponse.ok) {
      console.error('❌ Failed to send confirmation email:', confirmResult);
    } else {
      console.log('✅ Confirmation email sent:', confirmResult.id);
    }

    // Return success response
    return new Response(JSON.stringify({ 
      success: true, 
      caseId: caseId,
      message: `Thank you for contacting us! Your case ID is #${caseId}. We've sent a confirmation email to ${email}.`,
      supportEmailId: supportResult.id,
      confirmationEmailId: confirmResult.id
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });

  } catch (error) {
    console.error('💥 Error in contact form function:', error);
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}); 