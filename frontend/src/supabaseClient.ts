import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://dgjgvhjybomaiigmrehc.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRnamd2aGp5Ym9tYWlpZ21yZWhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwODI1MTQsImV4cCI6MjA2MzY1ODUxNH0.uu3DVwZ1ZBGAWKx74M9kV3WiJQ7bwG1P6oHPLjApSBg';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
