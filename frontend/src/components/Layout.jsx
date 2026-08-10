import React, { useState, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";
import {
  Dumbbell,
  LayoutDashboard,
  Salad,
  ClipboardList,
  TrendingUp,
  MessageCircle,
  Camera,
  Users,
  ShieldCheck,
  LogOut,
} from "lucide-react";

export default function Layout() {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

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

  const linkClass = ({ isActive }) => (isActive ? "active" : "");
  const closeMenu = () => setMenuOpen(false);
  const iconSize = 16;

  return (
    <div>
      <div className="topbar">
        <div className="brand">
          <Dumbbell size={20} strokeWidth={2.5} />
          AI Fitness Platform 
        </div>

        <button
          className="nav-toggle"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label="Toggle navigation"
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>

        <nav className={menuOpen ? "open" : ""}>
          <NavLink to="/dashboard" className={linkClass} onClick={closeMenu}>
            <LayoutDashboard size={iconSize} /> Dashboard
          </NavLink>
          <NavLink to="/workout" className={linkClass} onClick={closeMenu}>
            <Dumbbell size={iconSize} /> Workout
          </NavLink>
          <NavLink to="/diet" className={linkClass} onClick={closeMenu}>
            <Salad size={iconSize} /> Diet
          </NavLink>
          <NavLink to="/habits" className={linkClass} onClick={closeMenu}>
            <ClipboardList size={iconSize} /> Log
          </NavLink>
          <NavLink to="/progress" className={linkClass} onClick={closeMenu}>
            <TrendingUp size={iconSize} /> Progress
          </NavLink>
          <NavLink to="/coach" className={linkClass} onClick={closeMenu}>
            <MessageCircle size={iconSize} /> Coach
          </NavLink>
          <NavLink to="/photos" className={linkClass} onClick={closeMenu}>
            <Camera size={iconSize} /> Photos
          </NavLink>
          <NavLink to="/trainer" className={linkClass} onClick={closeMenu}>
            <Users size={iconSize} /> Trainer
          </NavLink>

          {!loading && isAdmin && (
            <NavLink to="/admin" className={linkClass} onClick={closeMenu}>
              <ShieldCheck size={iconSize} /> Admin
            </NavLink>
          )}

          <button className="btn btn-secondary btn-small" onClick={handleLogout}>
            <LogOut size={14} /> Log out
          </button>
        </nav>
      </div>
      <Outlet />
    </div>
  );
}
