// @ts-ignore: Deno global is available in Supabase Edge Functions
// @ts-ignore: External module import
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3'

console.log("🗑️ Delete auth user function started");

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
    
    const { userId } = await req.json();
    
    if (!userId) {
      return new Response(JSON.stringify({
        error: 'User ID is required'
      }), {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    // Delete the auth user using service role key
    const { error } = await supabaseClient.auth.admin.deleteUser(userId);
    
    if (error) {
      console.error('Error deleting auth user:', error);
      return new Response(JSON.stringify({
        error: 'Failed to delete user'
      }), {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    return new Response(JSON.stringify({
      success: true,
      message: 'User deleted successfully'
    }), {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
    
  } catch (error) {
    console.error('Error in delete-auth-user function:', error);
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
