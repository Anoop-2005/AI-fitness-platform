import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";

export default function Layout() {
  const navigate = useNavigate();

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
        </nav>
        <button className="btn btn-secondary" onClick={handleLogout}>Log out</button>
      </div>
      <Outlet />
    </div>
  );
}
