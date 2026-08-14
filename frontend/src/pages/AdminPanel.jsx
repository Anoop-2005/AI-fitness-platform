import React, { useState, useEffect } from "react";
import { api } from "../lib/api";
import { ShieldAlert } from "lucide-react";

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState("trainers");
  const [trainers, setTrainers] = useState([]);
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exercises, setExercises] = useState([]);
  const [foods, setFoods] = useState([]);
  const [librarySubTab, setLibrarySubTab] = useState("exercises");
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [exerciseSearch, setExerciseSearch] = useState("");
  const [foodSearch, setFoodSearch] = useState("");

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
      await loadLibrary(); 
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

  async function loadLibrary(exSearch = exerciseSearch, fdSearch = foodSearch) {
  try {
    const [exercisesData, foodsData] = await Promise.all([
      api.adminListExercises(exSearch),
      api.adminListFoods(fdSearch),
    ]);
    setExercises(exercisesData);
    setFoods(foodsData);
  } catch (err) {
    setError(err.message);
  }
  }
  function handleExerciseSearch(e) {
    e.preventDefault();
    loadLibrary(exerciseSearch, foodSearch);
  }

  function handleFoodSearch(e) {
    e.preventDefault();
    loadLibrary(exerciseSearch, foodSearch);
  }

  function startEdit(item, idKey) {
    setEditingId(item[idKey]);
    setEditForm({ ...item });
  }

  async function saveExercise(wgerId) {
    try {
      await api.adminUpdateExercise(wgerId, editForm);
      setEditingId(null);
      await loadLibrary();
    } catch (err) {
      alert("Failed to update: " + err.message);
    }
  }

  async function saveFood(fdcId) {
    try {
      await api.adminUpdateFood(fdcId, editForm);
      setEditingId(null);
      await loadLibrary();
    } catch (err) {
      alert("Failed to update: " + err.message);
    }
  }

  async function handleDeleteExercise(wgerId, name) {
    if (!window.confirm(`Delete exercise "${name}"? This cannot be undone.`)) return;
    try {
      await api.adminDeleteExercise(wgerId);
      await loadLibrary();
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  }

  async function handleDeleteFood(fdcId, name) {
    if (!window.confirm(`Delete food "${name}"? This cannot be undone.`)) return;
    try {
      await api.adminDeleteFood(fdcId);
      await loadLibrary();
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  }

  /*if (loading) return <div className="page">Loading...</div>;*/
  if (loading) {
    return (
      <div className="page page-loading">
        <div className="spinner"></div>
        <p>Loading admin panel...</p>
      </div>
    );
  }

  return (
    <div className="page page-wide">
      <div className="section-header">
      <ShieldAlert size={22} />
      <h2>Admin Panel</h2>
    </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Stats Cards */}
      {stats && (
        <div className="card-grid grid-auto-180 mb-16">
          <div className="card card-no-margin">
            <div className="stat-label">Total Users</div>
            <div className="stat-value">{stats.total_users}</div>
          </div>
          <div className="card card-no-margin">
            <div className="stat-label">Trainers</div>
            <div className="stat-value">{stats.trainers}</div>
          </div>
          <div className="card card-no-margin">
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
            onClick={() => setActiveTab("library")}
          >
            Library
          </button>
        </div>
      </div>

      {/* Error for non-admin 
      {error.includes("Admin access") && (
        <div className="card">
          <p>You don't have admin privileges. Please contact an administrator.</p>
        </div>
      )}*/}

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
            <div className="empty-state">
            <p>No clients registered yet.</p>
            </div>
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

      {/* Library Management */}
      {activeTab === "library" && !error.includes("Admin") && (
        <div className="card">
          <div className="flex-wrap gap-8 mb-12">
            <button
              className={`btn btn-small ${librarySubTab === "exercises" ? "" : "btn-secondary"}`}
              onClick={() => setLibrarySubTab("exercises")}
            >
              Exercises ({exercises.length})
            </button>
            <button
              className={`btn btn-small ${librarySubTab === "foods" ? "" : "btn-secondary"}`}
              onClick={() => setLibrarySubTab("foods")}
            >
              Foods ({foods.length})
            </button>
          </div>

          {librarySubTab === "exercises" && (
          <>
            <form onSubmit={handleExerciseSearch} className="flex-wrap gap-8 mb-12">
              <input
                type="text"
                placeholder="Search exercises by name..."
                value={exerciseSearch}
                onChange={(e) => setExerciseSearch(e.target.value)}
              />
              <button type="submit" className="btn btn-small">Search</button>
              {exerciseSearch && (
                <button
                  type="button"
                  className="btn btn-small btn-secondary"
                  onClick={() => { setExerciseSearch(""); loadLibrary("", foodSearch); }}
                >
                  Clear
                </button>
              )}
            </form>
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Muscle Group</th>
                    {/*<th>Difficulty</th>*/}
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {exercises.map((ex) => (
                    <tr key={ex.wger_id}>
                      {editingId === ex.wger_id ? (
                        <>
                          <td><input value={editForm.name || ""} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /></td>
                          <td><input value={editForm.muscle_group || ""} onChange={(e) => setEditForm({ ...editForm, muscle_group: e.target.value })} /></td>
                          {/*<td><input value={editForm.difficulty || ""} onChange={(e) => setEditForm({ ...editForm, difficulty: e.target.value })} /></td>*/}
                          <td>
                            <button className="btn btn-small" onClick={() => saveExercise(ex.wger_id)}>Save</button>
                            <button className="btn btn-small btn-secondary" onClick={() => setEditingId(null)}>Cancel</button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{ex.name}</td>
                          <td>{ex.muscle_group}</td>
                          {/*<td>{ex.difficulty}</td>*/}
                          <td>
                            <button className="btn btn-small btn-secondary" onClick={() => startEdit(ex, "wger_id")}>Edit</button>
                            <button className="btn btn-small btn-danger" onClick={() => handleDeleteExercise(ex.wger_id, ex.name)}>Delete</button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {librarySubTab === "foods" && (
        <>
          <form onSubmit={handleFoodSearch} className="flex-wrap gap-8 mb-12">
            <input
              type="text"
              placeholder="Search foods by name..."
              value={foodSearch}
              onChange={(e) => setFoodSearch(e.target.value)}
            />
            <button type="submit" className="btn btn-small">Search</button>
            {foodSearch && (
              <button
                type="button"
                className="btn btn-small btn-secondary"
                onClick={() => { setFoodSearch(""); loadLibrary(exerciseSearch, ""); }}
              >
                Clear
              </button>
            )}
          </form>
          <div className="table-responsive">
            <table>
              <thead>
                  <tr>
                    <th>Name</th>
                    <th>Calories</th>
                    <th>Protein (g)</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {foods.map((food) => (
                    <tr key={food.fdc_id}>
                      {editingId === food.fdc_id ? (
                        <>
                          <td><input value={editForm.name || ""} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /></td>
                          <td><input type="number" value={editForm.calories || ""} onChange={(e) => setEditForm({ ...editForm, calories: e.target.value })} /></td>
                          <td><input type="number" value={editForm.protein_g || ""} onChange={(e) => setEditForm({ ...editForm, protein_g: e.target.value })} /></td>
                          <td>
                            <button className="btn btn-small" onClick={() => saveFood(food.fdc_id)}>Save</button>
                            <button className="btn btn-small btn-secondary" onClick={() => setEditingId(null)}>Cancel</button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{food.name}</td>
                          <td>{food.calories}</td>
                          <td>{food.protein_g}</td>
                          <td>
                            <button className="btn btn-small btn-secondary" onClick={() => startEdit(food, "fdc_id")}>Edit</button>
                            <button className="btn btn-small btn-danger" onClick={() => handleDeleteFood(food.fdc_id, food.name)}>Delete</button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
            </table>
          </div>
        </>
      )}
        </div>
      )}
    </div>
  );
}
