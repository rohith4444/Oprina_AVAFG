// Add Deno type declarations to fix TypeScript errors
declare global {
  const Deno: {
    env: {
      get(key: string): string | undefined;
    };
    serve(handler: (req: Request) => Promise<Response> | Response): void;
  };
}

// @ts-ignore: External module import
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3'
import { corsHeaders } from '../_shared/cors.ts'

interface DeleteUserRequest {
  userId?: string
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get the authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      throw new Error('No authorization header')
    }

    // Initialize Supabase client with service role key (has admin privileges)
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Initialize regular client to verify the user's session
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    // Set the user's session
    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: userError } = await supabaseClient.auth.getUser(token)

    if (userError || !user) {
      throw new Error('Invalid token or user not found')
    }

    const { userId } = await req.json() as DeleteUserRequest

    // Verify the user is trying to delete their own account
    if (!userId || userId !== user.id) {
      throw new Error('Can only delete your own account')
    }

    // 1. First delete from custom users table
    const { error: userTableError } = await supabaseAdmin
      .from('users')
      .delete()
      .eq('email', user.email)

    if (userTableError) {
      console.log('Warning: Could not delete from users table:', userTableError)
      // Don't throw error here - user might not exist in custom table
    }

    // 2. Clean up other user data (sessions, messages, etc.)
    await Promise.all([
      supabaseAdmin.from('avatar_sessions').delete().eq('user_id', userId),
      supabaseAdmin.from('sessions').delete().eq('user_id', userId),
      supabaseAdmin.from('messages').delete().eq('user_id', userId)
    ])

    // 3. Finally delete the auth user
    const { error: deleteError } = await supabaseAdmin.auth.admin.deleteUser(userId)

    if (deleteError) {
      throw deleteError
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'User account deleted successfully' 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Error deleting user:', error)
    return new Response(
      JSON.stringify({ 
        error: error.message || 'An error occurred while deleting the user account' 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    )
  }
}) 