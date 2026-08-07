import React, { useState, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";

export default function Layout() {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkAdminRole() {
      try {
        const { data: { user }, error: userError } = await supabase.auth.getUser();
        if (userError || !user) {
          setLoading(false);
          return;
        }

        const { data, error } = await supabase
          .from("profiles") 
          .select("role") 
          .eq("user_id", user.id)
          .maybeSingle();

        if (!error && data && data.role === 'admin') {
          setIsAdmin(true);
        } else {
          setIsAdmin(false);
        }
      } catch (err) {
        console.error("Error checking admin status:", err);
      } finally {
        setLoading(false);
      }
    }

    checkAdminRole();
  }, []);

  async function handleLogout() {
    await supabase.auth.signOut();
    navigate("/login");
  }

  return (
    <div>
      <div className="topbar">
        <div className="brand">AI Fitness Platform</div>
        <nav>
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "active" : "")}>Dashboard</NavLink>
          <NavLink to="/workout" className={({ isActive }) => (isActive ? "active" : "")}>Workout</NavLink>
          <NavLink to="/diet" className={({ isActive }) => (isActive ? "active" : "")}>Diet</NavLink>
          <NavLink to="/habits" className={({ isActive }) => (isActive ? "active" : "")}>Log</NavLink>
          <NavLink to="/progress" className={({ isActive }) => (isActive ? "active" : "")}>Progress</NavLink>
          <NavLink to="/coach" className={({ isActive }) => (isActive ? "active" : "")}>Coach</NavLink>
          <NavLink to="/photos" className={({ isActive }) => (isActive ? "active" : "")}>Photos</NavLink>
          <NavLink to="/trainer" className={({ isActive }) => (isActive ? "active" : "")}>Trainer</NavLink>
          
          {/* ONLY this conditional link remains */}
          {!loading && isAdmin && (
            <NavLink to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>Admin</NavLink>
          )}
        </nav>
        <button className="btn btn-secondary" onClick={handleLogout}>Log out</button>
      </div>
      <Outlet />
    </div>
  );
}