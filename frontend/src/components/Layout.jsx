import React, { useState, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabaseClient";
import { api } from "../lib/api";

export default function Layout() {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);

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

  //useEffect(() => {
    //loadNotifications();
    //const interval = setInterval(loadNotifications, 60000); // Refresh every minute
    //return () => clearInterval(interval);
  //}, []);
  useEffect(() => {
    loadNotifications();
  }, []);

  async function loadNotifications() {
    try {
      const [notifs, count] = await Promise.all([
        api.getNotifications(true).catch(() => []),
        api.getUnreadCount().catch(() => ({ count: 0 })),
      ]);
      setNotifications(notifs.slice(0, 5));
      setUnreadCount(count.count || 0);
    } catch (err) {
      // Silently fail
    }
  }

  async function markRead(id) {
    try {
      await api.markNotificationRead(id);
      await loadNotifications();
    } catch (err) {
      // Silently fail
    }
  }

  async function markAllRead() {
    try {
      await api.markAllNotificationsRead();
      await loadNotifications();
    } catch (err) {
      // Silently fail
    }
  }

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

          {!loading && isAdmin && (
            <NavLink to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>Admin</NavLink>
          )}
        </nav>
        <div className="flex-wrap gap-8">
          {/* Notification Bell */}
          <div style={{ position: "relative" }}>
            <button
              className="btn btn-secondary btn-small"
              onClick={() => setShowNotifDropdown(!showNotifDropdown)}
            >
              🔔 {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
            </button>
            {showNotifDropdown && (
              <div style={{
                position: "absolute",
                right: 0,
                top: "100%",
                width: 300,
                maxHeight: 400,
                overflowY: "auto",
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                zIndex: 1000,
              }}>
                <div className="flex-between" style={{ padding: "10px 12px", borderBottom: "1px solid var(--border)" }}>
                  <strong>Notifications</strong>
                  {unreadCount > 0 && (
                    <button className="btn btn-small btn-secondary" onClick={markAllRead}>Mark all read</button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <p className="text-small text-dim" style={{ padding: "12px" }}>No new notifications.</p>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => markRead(n.id)}
                      style={{
                        padding: "10px 12px",
                        borderBottom: "1px solid var(--border)",
                        cursor: "pointer",
                        background: n.read ? "transparent" : "rgba(47, 111, 79, 0.05)",
                      }}
                    >
                      <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>{n.title}</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: 2 }}>{n.message}</div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
          <button className="btn btn-secondary" onClick={handleLogout}>Log out</button>
        </div>
      </div>
      <Outlet />
    </div>
  );
}