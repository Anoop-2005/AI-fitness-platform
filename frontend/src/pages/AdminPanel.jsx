import React, { useState, useEffect } from "react";
import { api } from "../lib/api";

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState("trainers");
  const [trainers, setTrainers] = useState([]);
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [trainersData, clientsData, statsData] = await Promise.all([
        api.adminListTrainers(),
        api.adminListClients(),
        api.adminStats(),
      ]);
      setTrainers(trainersData);
      setClients(clientsData);
      setStats(statsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(userId, name) {
    if (!window.confirm(`Are you sure you want to delete "${name}"? This will remove all their data and cannot be undone.`)) {
      return;
    }
    try {
      await api.adminDeleteUser(userId);
      await loadData();
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  }

  if (loading) return <div className="page">Loading...</div>;

  return (
    <div className="page page-wide">
      <h2>Admin Panel</h2>

      {error && <div className="error-banner">{error}</div>}

      {/* Stats Cards */}
      {stats && (
        <div className="card-grid grid-auto-180 mb-16">
          <div className="card">
            <div className="stat-label">Total Users</div>
            <div className="stat-value">{stats.total_users}</div>
          </div>
          <div className="card">
            <div className="stat-label">Trainers</div>
            <div className="stat-value">{stats.trainers}</div>
          </div>
          <div className="card">
            <div className="stat-label">Clients</div>
            <div className="stat-value">{stats.clients}</div>
          </div>
          <div className="card">
            <div className="stat-label">Logs (30 days)</div>
            <div className="stat-value">{stats.recent_logs}</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex-between mb-16">
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className={`btn ${activeTab === "trainers" ? "" : "btn-secondary"}`}
            onClick={() => setActiveTab("trainers")}
          >
            Trainers ({trainers.length})
          </button>
          <button
            className={`btn ${activeTab === "clients" ? "" : "btn-secondary"}`}
            onClick={() => setActiveTab("clients")}
          >
            Clients ({clients.length})
          </button>
        </div>
      </div>

      {/* Error for non-admin */}
      {error.includes("Admin access") && (
        <div className="card">
          <p>You don't have admin privileges. Please contact an administrator.</p>
        </div>
      )}

      {/* Trainers List */}
      {activeTab === "trainers" && !error.includes("Admin") && (
        <div className="card">
          <h3 className="mb-12">All Trainers</h3>
          {trainers.length === 0 ? (
            <p className="text-small text-dim">No trainers registered yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Gender</th>
                  <th>Joined</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {trainers.map((trainer) => (
                  <tr key={trainer.user_id}>
                    <td>{trainer.full_name}</td>
                    <td>{trainer.email || "N/A"}</td>
                    <td>{trainer.gender}</td>
                    <td>{new Date(trainer.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-small"
                        style={{ background: "var(--danger)" }}
                        onClick={() => handleDelete(trainer.user_id, trainer.full_name)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Clients List */}
      {activeTab === "clients" && !error.includes("Admin") && (
        <div className="card">
          <h3 className="mb-12">All Clients</h3>
          {clients.length === 0 ? (
            <p className="text-small text-dim">No clients registered yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Goal</th>
                  <th>Joined</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client.user_id}>
                    <td>{client.full_name}</td>
                    <td>{client.email || "N/A"}</td>
                    <td>{client.primary_goal || "N/A"}</td>
                    <td>{new Date(client.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-small"
                        style={{ background: "var(--danger)" }}
                        onClick={() => handleDelete(client.user_id, client.full_name)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
