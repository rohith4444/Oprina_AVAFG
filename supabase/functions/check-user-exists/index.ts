// @ts-ignore: Deno global is available in Supabase Edge Functions
// @ts-ignore: External module import
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3'

console.log("🔍 Check user exists function started");

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

// @ts-ignore: Deno is available globally
Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: corsHeaders
    });
  }

  try {
    const supabaseClient = createClient(
      // @ts-ignore: Deno is available globally
      Deno.env.get('SUPABASE_URL') ?? '', 
      // @ts-ignore: Deno is available globally
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );
    
    const { email } = await req.json();
    
    if (!email) {
      return new Response(JSON.stringify({
        error: 'Email is required'
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    // Check if user exists in our users table
    const { data: user, error } = await supabaseClient
      .from('users')
      .select('id, email')
      .eq('email', email)
      .single();
    
    const userExists = user && !error;
    
    return new Response(JSON.stringify({
      exists: userExists,
      email: email
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
    
  } catch (error) {
    console.error('Error checking user:', error);
    return new Response(JSON.stringify({
      error: 'Internal server error'
    }), {
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
});
