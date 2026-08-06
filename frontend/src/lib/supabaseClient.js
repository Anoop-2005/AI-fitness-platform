// The frontend talks to Supabase directly ONLY for auth (signup/login/
// session). Every other piece of data (profile, plans, habits) goes
// through our own FastAPI backend, which double-checks the Supabase
// access token on every request.
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
