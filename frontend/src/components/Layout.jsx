import React, { useState, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";
import { api } from "../lib/api";
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
  Bell,
} from "lucide-react";

export default function Layout() {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);

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

  useEffect(() => {
  async function loadNotifications() {
    try {
      await api.checkNotifications();
      const data = await api.getNotifications();
      setNotifications(data);
      const { count } = await api.getUnreadNotificationCount();
      setUnreadCount(count);
    } catch (err) {
      console.error("Error loading notifications:", err);
    }
  }
  loadNotifications();
}, []);

async function handleMarkRead(id) {
  try {
    await api.markNotificationRead(id);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
  } catch (err) {
    console.error("Error marking notification read:", err);
  }
}

async function handleMarkAllRead() {
  try {
    await api.markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
  } catch (err) {
    console.error("Error marking all read:", err);
  }
}

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

          <div className="notif-wrapper">
          <button
            className="btn btn-secondary btn-small"
            onClick={() => setNotifOpen((v) => !v)}
            aria-label="Notifications"
            style={{ position: "relative" }}
          >
            <Bell size={16} />
            {unreadCount > 0 && (
              <span className="notif-badge">
                {unreadCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="card notif-dropdown">
              <div className="flex-between mb-12">
                <h4 style={{ margin: 0 }}>Notifications</h4>
                {unreadCount > 0 && (
                  <button className="btn btn-small btn-secondary" onClick={handleMarkAllRead}>
                    Mark all read
                  </button>
                )}
              </div>
              {notifications.length === 0 ? (
                <p className="text-small text-dim">No notifications yet.</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => !n.read && handleMarkRead(n.id)}
                    className={`notif-item ${n.read ? "read" : "unread"}`}
                  >
                    <div className="notif-title">{n.title}</div>
                    <div className="notif-message">{n.message}</div>
                    <div className="text-tiny text-dim mt-4">
                      {new Date(n.created_at).toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

          <button className="btn btn-secondary btn-small" onClick={handleLogout}>
            <LogOut size={14} /> Log out
          </button>
        </nav>
      </div>
      <Outlet />
    </div>
  );
}
