import React, { useState, useEffect } from "react";
import { api } from "../lib/api";

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState("trainers");
  const [trainers, setTrainers] = useState([]);
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [foods, setFoods] = useState([]);
  const [libSearch, setLibSearch] = useState("");
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

  async function loadLibrary(type, search) {
    try {
      if (type === "exercises") {
        const data = await api.adminListExercises(search);
        setExercises(data);
      } else {
        const data = await api.adminListFoods(search);
        setFoods(data);
      }
    } catch (err) {
      alert("Failed to load: " + err.message);
    }
  }

  async function handleLibraryDelete(type, id, name) {
    if (!window.confirm(`Delete "${name}" from the library?`)) return;
    try {
      if (type === "exercises") {
        await api.adminDeleteExercise(id);
        loadLibrary("exercises", libSearch);
      } else {
        await api.adminDeleteFood(id);
        loadLibrary("foods", libSearch);
      }
    } catch (err) {
      alert("Failed to delete: " + err.message);
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
        </div>
      )}

      {/* Tabs */}
      <div className="flex-between mb-16">
        <div className="flex-wrap gap-8">
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
          <button
            className={`btn ${activeTab === "library" ? "" : "btn-secondary"}`}
            onClick={() => { setActiveTab("library"); loadLibrary("exercises", ""); }}
          >
            Library
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
            <div className="table-responsive">
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
                      <td className="hide-mobile">{trainer.gender}</td>
                      <td>{new Date(trainer.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          className="btn btn-small btn-danger"
                          onClick={() => handleDelete(trainer.user_id, trainer.full_name)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th className="hide-mobile">Goal</th>
                    <th>Joined</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((client) => (
                    <tr key={client.user_id}>
                      <td>{client.full_name}</td>
                      <td>{client.email || "N/A"}</td>
                      <td className="hide-mobile">{client.primary_goal || "N/A"}</td>
                      <td>{new Date(client.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          className="btn btn-small btn-danger"
                          onClick={() => handleDelete(client.user_id, client.full_name)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Library Management Tab */}
      {activeTab === "library" && !error.includes("Admin") && (
        <div className="flex-column gap-16">
          <div className="card">
            <h3 className="mb-12">Exercise & Food Library</h3>
            <div className="field-row mb-12">
              <input
                type="text"
                placeholder="Search exercises or foods..."
                value={libSearch}
                onChange={(e) => setLibSearch(e.target.value)}
                style={{ padding: "8px 10px", borderRadius: 6, border: "1px solid var(--border)", fontSize: "0.9rem" }}
              />
              <button className="btn" onClick={() => loadLibrary("exercises", libSearch)}>Search Exercises</button>
              <button className="btn btn-secondary" onClick={() => loadLibrary("foods", libSearch)}>Search Foods</button>
            </div>
          </div>

          {/* Exercises Table */}
          {exercises.length > 0 && (
            <div className="card">
              <h4 className="mb-12">Exercises ({exercises.length})</h4>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Muscle</th>
                      <th>Equipment</th>
                      <th>Difficulty</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exercises.map((ex) => (
                      <tr key={ex.wger_id}>
                        <td>{ex.name}</td>
                        <td>{ex.muscle_group || "—"}</td>
                        <td className="hide-mobile">{ex.equipment?.length ? (typeof ex.equipment === 'string' ? JSON.parse(ex.equipment).join(", ") : ex.equipment.join(", ")) : "—"}</td>
                        <td>{ex.difficulty || "—"}</td>
                        <td>
                          <button
                            className="btn btn-small btn-danger"
                            onClick={() => handleLibraryDelete("exercises", ex.wger_id, ex.name)}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Foods Table */}
          {foods.length > 0 && (
            <div className="card">
              <h4 className="mb-12">Foods ({foods.length})</h4>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Calories</th>
                      <th>Protein</th>
                      <th>Carbs</th>
                      <th>Fat</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {foods.map((food) => (
                      <tr key={food.fdc_id}>
                        <td>{food.name}</td>
                        <td>{food.calories || "—"}</td>
                        <td>{food.protein_g ? `${food.protein_g}g` : "—"}</td>
                        <td>{food.carbs_g ? `${food.carbs_g}g` : "—"}</td>
                        <td>{food.fat_g ? `${food.fat_g}g` : "—"}</td>
                        <td>
                          <button
                            className="btn btn-small btn-danger"
                            onClick={() => handleLibraryDelete("foods", food.fdc_id, food.name)}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
