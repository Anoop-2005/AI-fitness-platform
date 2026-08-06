import React, { useState, useEffect } from "react";
import { api } from "../lib/api";

// --- Sub-component: Client Messaging View ---
function ClientInbox({ trainer, messages, newMessage, setNewMessage, onSend, sending, currentUserId }) {
  return (
    <div className="page page-wide">
      <h2>💬 Messages with Your Trainer</h2>

      {!trainer ? (
        <div className="card">
          <p className="text-dim">No trainer has been assigned to you yet.</p>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="flex-between">
              <div>
                <h3>{trainer.full_name}</h3>
                <p className="text-small text-dim">Your Trainer</p>
              </div>
            </div>
          </div>

          {/* Message List */}
          <div className="card" style={{ minHeight: 300, maxHeight: 400, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
            {messages.length === 0 ? (
              <p className="text-dim text-center">No messages yet. Start a conversation!</p>
            ) : (
              messages.map((msg) => {
                const isFromClient = msg.client_id === currentUserId && msg.trainer_id === trainer.user_id;
                return (
                  <div
                    key={msg.id}
                    style={{
                      alignSelf: isFromClient ? "flex-end" : "flex-start",
                      maxWidth: "80%",
                      padding: "10px 14px",
                      borderRadius: 12,
                      background: isFromClient ? "var(--primary)" : "var(--surface)",
                      color: isFromClient ? "#fff" : "var(--text)",
                      border: isFromClient ? "none" : "1px solid var(--border)",
                    }}
                  >
                    <div style={{ fontSize: "0.85rem" }}>{msg.message}</div>
                    <div style={{ fontSize: "0.7rem", opacity: 0.7, marginTop: 4, textAlign: "right" }}>
                      {new Date(msg.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Reply Box */}
          <div className="card">
            <div style={{ display: "flex", gap: 12 }}>
              <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your reply..."
                rows={3}
                style={{ flex: 1, padding: "10px 14px", borderRadius: 8, border: "1px solid var(--border)", resize: "none" }}
              />
              <button className="btn" onClick={onSend} disabled={sending || !newMessage.trim()}>
                {sending ? "Sending..." : "Reply"}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// --- Main Component ---
export default function TrainerDashboard() {
  const [userRole, setUserRole] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Trainer States
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientData, setClientData] = useState(null);
  const [activeTab, setActiveTab] = useState("workout");
  const [dataLoading, setDataLoading] = useState(false);
  const [trainerMessage, setTrainerMessage] = useState("");
  const [sending, setSending] = useState(false);

  // Client States
  const [trainer, setTrainer] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");

  useEffect(() => {
    detectRole();
  }, []);

  async function detectRole() {
    setLoading(true);
    try {
      const profile = await api.getProfile();
      const role = profile.role || "client"; // null/undefined treated as client
      setUserRole(role);
      setCurrentUserId(profile.user_id);

      if (role === "trainer") {
        await loadTrainerDashboard();
      } else {
        await loadClientInbox();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // --- Trainer Logic ---
  async function loadTrainerDashboard() {
    try {
      const data = await api.trainerGetClients();
      setClients(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function selectClient(client) {
    setSelectedClient(client);
    setDataLoading(true);
    setActiveTab("workout");
    try {
      const [profile, workout, diet, analysis, messages] = await Promise.all([
        api.trainerGetClientProfile(client.user_id),
        api.trainerGetClientWorkout(client.user_id),
        api.trainerGetClientDiet(client.user_id),
        api.trainerGetClientAnalysis(client.user_id).catch(() => null),
        api.trainerGetMessages(client.user_id).catch(() => [])
      ]);
      setClientData({ profile, workout, diet, analysis, messages });
    } catch (err) {
      setError(err.message);
    } finally {
      setDataLoading(false);
    }
  }

  async function sendTrainerMessage() {
    if (!trainerMessage.trim() || !selectedClient) return;
    setSending(true);
    try {
      await api.trainerSendMessage(selectedClient.user_id, trainerMessage);
      setTrainerMessage("");
      alert("Message sent successfully!");
      
      const updatedMessages = await api.trainerGetMessages(selectedClient.user_id);
      setClientData(prev => ({ ...prev, messages: updatedMessages }));
    } catch (err) {
      alert("Failed to send: " + err.message);
    } finally {
      setSending(false);
    }
  }

  // --- Client Logic ---
  async function loadClientInbox() {
    try {
      const [trainerData, msgs] = await Promise.all([
        api.getMyTrainer().catch(() => null),
        api.getMyMessages().catch(() => []),
      ]);
      setTrainer(trainerData);
      setMessages(msgs);
    } catch (err) {
      setError(err.message);
    }
  }

  async function sendReply() {
    if (!newMessage.trim()) return;
    setSending(true);
    try {
      await api.clientSendMessage(newMessage);
      setNewMessage("");
      await loadClientInbox(); // Refresh messages
    } catch (err) {
      alert("Failed to send: " + err.message);
    } finally {
      setSending(false);
    }
  }

  if (loading) return <div className="page">Loading...</div>;

  if (error) {
    return (
      <div className="page">
        <div className="error-banner">{error}</div>
      </div>
    );
  }

  // Render based on role
  if (userRole !== "trainer") {
    return (
      <ClientInbox
        trainer={trainer}
        messages={messages}
        newMessage={newMessage}
        setNewMessage={setNewMessage}
        onSend={sendReply}
        sending={sending}
        currentUserId={currentUserId}
      />
    );
  }

  // --- Trainer Dashboard View ---
  return (
    <div className="page page-wide">
      <h2>Trainer Dashboard</h2>

      <div style={{ display: "flex", gap: 24, marginTop: 16 }}>
        {/* Client List Sidebar */}
        <div style={{ width: 280, minWidth: 200 }}>
          <div className="card">
            <h3 className="mb-12">My Clients</h3>
            {clients.length === 0 ? (
              <p className="text-small text-dim">No clients assigned yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {clients.map((client) => (
                  <button
                    key={client.user_id}
                    className={`btn ${selectedClient?.user_id === client.user_id ? "" : "btn-secondary"}`}
                    style={{ textAlign: "left", width: "100%" }}
                    onClick={() => selectClient(client)}
                  >
                    <div style={{ fontWeight: 600 }}>{client.full_name}</div>
                    <div style={{ fontSize: "0.75rem", opacity: 0.8 }}>
                      {client.age}y | {client.gender}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Client Details */}
        <div style={{ flex: 1 }}>
          {!selectedClient ? (
            <div className="card">
              <p className="text-dim">Select a client to view their details.</p>
            </div>
          ) : dataLoading ? (
            <div className="card">
              <p>Loading client data...</p>
            </div>
          ) : clientData ? (
            <>
              {/* Client Header */}
              <div className="card">
                <div className="flex-between">
                  <div>
                    <h3>{clientData.profile.full_name}</h3>
                    <p className="text-small text-dim">
                      {clientData.profile.age} years | {clientData.profile.gender} | {clientData.profile.activity_level}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-small text-dim">Goal</div>
                    <div className="fw-600 text-capitalize">
                      {clientData.profile.primary_goal?.replace("_", " ")}
                    </div>
                  </div>
                </div>

                {/* Body Stats */}
                {clientData.analysis && (
                  <div className="card-grid grid-auto-180 mt-16">
                    <div>
                      <div className="stat-label">BMI</div>
                      <div className="stat-value">{clientData.analysis.bmi}</div>
                    </div>
                    <div>
                      <div className="stat-label">Target Calories</div>
                      <div className="stat-value">{Math.round(clientData.analysis.target_calories)}</div>
                    </div>
                    <div>
                      <div className="stat-label">Weight</div>
                      <div className="stat-value">{clientData.profile.current_weight_kg}kg</div>
                    </div>
                    <div>
                      <div className="stat-label">Target Weight</div>
                      <div className="stat-value">{clientData.profile.target_weight_kg}kg</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Tabs */}
              <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                <button
                  className={`btn ${activeTab === "workout" ? "" : "btn-secondary"}`}
                  onClick={() => setActiveTab("workout")}
                >
                  Workout Plan
                </button>
                <button
                  className={`btn ${activeTab === "diet" ? "" : "btn-secondary"}`}
                  onClick={() => setActiveTab("diet")}
                >
                  Diet Plan
                </button>
                <button
                  className={`btn ${activeTab === "message" ? "" : "btn-secondary"}`}
                  onClick={() => setActiveTab("message")}
                >
                  Message
                </button>
              </div>

              {/* Workout Tab */}
              {activeTab === "workout" && (
                <div className="card">
                  <h3 className="mb-12">Current Workout Plan</h3>
                  {clientData.workout.days?.length > 0 ? (
                    clientData.workout.days.map((day) => (
                      <div key={day.day_number} className="mb-16">
                        <h4 className="mb-12">Day {day.day_number}</h4>
                        <table>
                          <thead>
                            <tr>
                              <th>Exercise</th>
                              <th>Muscle</th>
                              <th>Sets</th>
                              <th>Reps</th>
                              <th>Rest</th>
                            </tr>
                          </thead>
                          <tbody>
                            {day.exercises.map((ex, i) => (
                              <tr key={i}>
                                <td>{ex.name}</td>
                                <td>{ex.muscle_group}</td>
                                <td>{ex.sets}</td>
                                <td>{ex.reps}</td>
                                <td>{ex.rest_seconds}s</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ))
                  ) : (
                    <p className="text-small text-dim">No workout plan generated yet.</p>
                  )}
                </div>
              )}

              {/* Diet Tab */}
              {activeTab === "diet" && (
                <div className="card">
                  <h3 className="mb-12">Current Diet Plan</h3>
                  {clientData.diet.meals?.length > 0 ? (
                    <table>
                      <thead>
                        <tr>
                          <th>Meal</th>
                          <th>Food</th>
                          <th>Calories</th>
                          <th>Protein</th>
                          <th>Carbs</th>
                          <th>Fat</th>
                        </tr>
                      </thead>
                      <tbody>
                        {clientData.diet.meals.map((meal, i) => (
                          <tr key={i}>
                            <td className="text-capitalize">{meal.meal_slot.replace("_", " ")}</td>
                            <td>{meal.name}</td>
                            <td>{Math.round(meal.calories)} kcal</td>
                            <td>{Math.round(meal.protein_g)}g</td>
                            <td>{Math.round(meal.carbs_g)}g</td>
                            <td>{Math.round(meal.fat_g)}g</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-small text-dim">No diet plan generated yet.</p>
                  )}
                </div>
              )}

              {/* Message Tab */}
              {/* Message Tab */}
              {activeTab === "message" && (
                <div className="card">
                  <h3 className="mb-12">Conversation with {selectedClient.full_name}</h3>
                  
                  {/* Message History Feed */}
                  <div style={{ minHeight: 250, maxHeight: 350, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, marginBottom: 16, padding: 8, background: "rgba(0,0,0,0.02)", borderRadius: 8 }}>
                    {clientData.messages?.length === 0 ? (
                      <p className="text-dim text-center">No messages yet with this client.</p>
                    ) : (
                      clientData.messages.map((msg) => {
                        const isFromTrainer = msg.trainer_id === currentUserId;
                        return (
                          <div
                            key={msg.id}
                            style={{
                              alignSelf: isFromTrainer ? "flex-end" : "flex-start",
                              maxWidth: "80%",
                              padding: "10px 14px",
                              borderRadius: 12,
                              background: isFromTrainer ? "var(--primary)" : "var(--surface)",
                              color: isFromTrainer ? "#fff" : "var(--text)",
                              border: isFromTrainer ? "none" : "1px solid var(--border)",
                            }}
                          >
                            <div style={{ fontSize: "0.9rem" }}>{msg.message}</div>
                            <div style={{ fontSize: "0.65rem", opacity: 0.7, marginTop: 4, textAlign: "right" }}>
                              {new Date(msg.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  {/* Send Box */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <textarea
                      value={trainerMessage}
                      onChange={(e) => setTrainerMessage(e.target.value)}
                      placeholder="Type your message here..."
                      rows={3}
                      style={{
                        padding: "10px 14px",
                        borderRadius: 8,
                        border: "1px solid var(--border)",
                        resize: "none",
                        fontSize: "0.9rem",
                      }}
                    />
                    <button
                      className="btn"
                      onClick={sendTrainerMessage}
                      disabled={sending || !trainerMessage.trim()}
                      style={{ alignSelf: "flex-start" }}
                    >
                      {sending ? "Sending..." : "Send Message"}
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}