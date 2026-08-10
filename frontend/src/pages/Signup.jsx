import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";
import { Dumbbell } from "lucide-react";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    const { data, error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) return setError(error.message);

    if (data.session) {
      // Email confirmation is off — user is logged in immediately
      navigate("/onboarding");
    } else {
      // Email confirmation is on (Supabase default) — they must check their inbox first
      setInfo("Account created! Check your email to confirm, then log in.");
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon"><Dumbbell size={20} strokeWidth={2.5} /></div>
          <div className="auth-logo-text">Iron Ledger</div>
        </div>
        <h2>Create your account</h2>
        <p className="page-subtitle">Set up your profile and get a personalized plan.</p>
        {error && <div className="error-banner">{error}</div>}
        {info && <div className="info-banner">{info}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Password (min 6 characters)</label>
            <input type="password" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button className="btn btn-full" disabled={loading}>
            {loading ? "Creating account..." : "Sign up"}
          </button>
        </form>
        <p className="auth-link-text">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
