import React, { useState, useEffect } from "react";
import { api } from "../lib/api";

function ClientInbox({ trainer, availableTrainers, onSelectTrainer, messages, newMessage, setNewMessage, onSend, sending, currentUserId }) {
  const [selectingId, setSelectingId] = useState(null);

  async function handleSelect(trainerId) {
    setSelectingId(trainerId);
    await onSelectTrainer(trainerId);
    setSelectingId(null);
  }

  return (
    <div className="page page-wide">
      <h2>💬 Messages with Your Trainer</h2>

      {!trainer ? (
        <div className="flex-column gap-24">
          <div className="card">
            <p className="text-dim">No trainer has been assigned to you yet. Choose a professional trainer below to get started!</p>
          </div>

          <div className="card">
            <h3 className="mb-12">Available Trainers</h3>
            {availableTrainers.length === 0 ? (
              <p className="text-small text-dim">No trainers are currently available.</p>
            ) : (
              <div className="card-grid gap-16" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))" }}>
                {availableTrainers.map((t) => (
                  <div key={t.user_id} className="card flex-column justify-between gap-12">
                    <div>
                      <h4 className="mb-4">{t.full_name}</h4>
                      <p className="text-small text-dim">
                        {t.age}y | {t.gender} | {t.activity_level || "Fitness Pro"}
                      </p>
                    </div>
                    <button
                      className="btn btn-full"
                      disabled={selectingId === t.user_id}
                      onClick={() => handleSelect(t.user_id)}
                    >
                      {selectingId === t.user_id ? "Selecting..." : "Select Trainer"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
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

          <div className="card chat-container">
            {messages.length === 0 ? (
              <p className="text-dim text-center">No messages yet. Start a conversation!</p>
            ) : (
              messages.map((msg) => {
                const isFromClient = msg.client_id === currentUserId && msg.trainer_id === trainer.user_id;
                return (
                  <div
                    key={msg.id}
                    className={`chat-message ${isFromClient ? "chat-message-user" : "chat-message-assistant"}`}
                  >
                    <div>{msg.message}</div>
                    <div className="chat-message-time">
                      {new Date(msg.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="card">
            <div className="chat-input-area">
              <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your reply..."
                rows={3}
                className="chat-textarea"
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
  const [assigning, setAssigning] = useState(false);
  const [clientPhotos, setClientPhotos] = useState({});
  const [pendingRequests, setPendingRequests] = useState([]);

  // Client States
  const [trainer, setTrainer] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [availableTrainers, setAvailableTrainers] = useState([]);

  useEffect(() => {
    detectRole();
  }, []);

  async function detectRole() {
    setLoading(true);
    try {
      const profile = await api.getProfile();
      const role = profile.role || "client";
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

  async function loadTrainerDashboard() {
    try {
      const [clientsData, requestsData] = await Promise.all([
        api.trainerGetClients(),
        api.trainerGetPendingRequests().catch(() => []),
      ]);
      setClients(clientsData);
      setPendingRequests(requestsData);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRequestAction(clientId, action) {
    try {
      await api.trainerRespondRequest(clientId, action);
      alert(`Request ${action}ed!`);
      await loadTrainerDashboard();
    } catch (err) {
      alert("Failed to process request: " + err.message);
    }
  }

  async function selectClient(client) {
    setSelectedClient(client);
    setDataLoading(true);
    setActiveTab("workout");
    setClientPhotos({});
    try {
      const [profile, workout, diet, analysis, messages, photos] = await Promise.all([
        api.trainerGetClientProfile(client.user_id),
        api.trainerGetClientWorkout(client.user_id),
        api.trainerGetClientDiet(client.user_id),
        api.trainerGetClientAnalysis(client.user_id).catch(() => null),
        api.trainerGetMessages(client.user_id).catch(() => []),
        api.trainerGetClientPhotos(client.user_id).catch(() => ({})),
      ]);
      setClientData({ profile, workout, diet, analysis, messages });
      setClientPhotos(photos);
    } catch (err) {
      setError(err.message);
    } finally {
      setDataLoading(false);
    }
  }

  function renderClientPhotos() {
    const viewTypes = [
      { key: "front", label: "Front", icon: "🧍" },
      { key: "side", label: "Side", icon: "🚶" },
      { key: "back", label: "Back", icon: "🔙" },
    ];

    return (
      <div className="flex-column gap-16">
        {viewTypes.map((vt) => {
          const photos = clientPhotos[vt.key] || [];
          return (
            <div key={vt.key}>
              <h4 className="mb-12">{vt.icon} {vt.label} View</h4>
              {photos.length > 0 ? (
                <div className="photo-gallery">
                  {photos.map((photo) => (
                    <div key={photo.id} className="photo-item">
                      <img
                        src={photo.photo_url}
                        alt={`${vt.label} ${photo.uploaded_at}`}
                      />
                      <p className="text-mini text-dim mt-4">
                        {new Date(photo.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-small text-dim">No {vt.label} photos uploaded.</p>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  async function sendTrainerMessage() {
    if (!trainerMessage.trim() || !selectedClient) return;
    setSending(true);
    try {
      await api.trainerSendMessage(selectedClient.user_id, trainerMessage);
      setTrainerMessage("");
      alert("Message sent successfully!");
      const updatedMessages = await api.trainerGetMessages(selectedClient.user_id);
      setClientData((prev) => ({ ...prev, messages: updatedMessages }));
    } catch (err) {
      alert("Failed to send: " + err.message);
    } finally {
      setSending(false);
    }
  }

  async function assignWorkout() {
    if (!selectedClient) return;
    setAssigning(true);
    try {
      const result = await api.trainerCreateWorkout(selectedClient.user_id);
      setClientData((prev) => ({ ...prev, workout: result }));
      alert("Workout plan assigned successfully!");
    } catch (err) {
      alert("Failed to assign workout: " + err.message);
    } finally {
      setAssigning(false);
    }
  }

  async function assignDiet() {
    if (!selectedClient) return;
    setAssigning(true);
    try {
      const result = await api.trainerCreateDiet(selectedClient.user_id);
      setClientData((prev) => ({ ...prev, diet: result }));
      alert("Diet plan assigned successfully!");
    } catch (err) {
      alert("Failed to assign diet: " + err.message);
    } finally {
      setAssigning(false);
    }
  }

  async function loadClientInbox() {
    try {
      const [trainerData, msgs, trainersList] = await Promise.all([
        api.getMyTrainer().catch(() => null),
        api.getMyMessages().catch(() => []),
        api.getAvailableTrainers().catch(() => []),
      ]);
      setTrainer(trainerData);
      setMessages(msgs);
      setAvailableTrainers(trainersList);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSelectTrainer(trainerId) {
    try {
      await api.requestTrainer(trainerId);
      alert("Trainer selected successfully!");
      await loadClientInbox();
    } catch (err) {
      alert("Failed to select trainer: " + err.message);
    }
  }

  async function sendReply() {
    if (!newMessage.trim()) return;
    setSending(true);
    try {
      await api.clientSendMessage(newMessage);
      setNewMessage("");
      await loadClientInbox();
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

  if (userRole !== "trainer") {
    return (
      <ClientInbox
        trainer={trainer}
        availableTrainers={availableTrainers}
        onSelectTrainer={handleSelectTrainer}
        messages={messages}
        newMessage={newMessage}
        setNewMessage={setNewMessage}
        onSend={sendReply}
        sending={sending}
        currentUserId={currentUserId}
      />
    );
  }

  return (
    <div className="page page-wide">
      <h2>Trainer Dashboard</h2>

      {/* Pending Client Requests */}
      {pendingRequests.length > 0 && (
        <div className="card mb-16 bg-primary-light">
          <h3 className="mb-12">🔔 Pending Client Requests ({pendingRequests.length})</h3>
          <div className="card-grid gap-16" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
            {pendingRequests.map((req) => (
              <div key={req.client_id} className="card flex-column justify-between gap-12">
                <div>
                  <h4 className="mb-4">{req.full_name}</h4>
                  <p className="text-small text-dim">
                    {req.age}y | {req.gender} | Goal: {req.primary_goal?.replace("_", " ") || "General"}
                  </p>
                  <p className="text-small text-dim mt-4">
                    Activity: {req.activity_level || "Not specified"}
                  </p>
                </div>
                <div className="flex-wrap gap-8">
                  <button
                    className="btn flex-1"
                    style={{ background: "green" }}
                    onClick={() => handleRequestAction(req.client_id, "accept")}
                  >
                    Accept
                  </button>
                  <button
                    className="btn btn-secondary flex-1"
                    style={{ color: "var(--danger)", borderColor: "var(--danger)" }}
                    onClick={() => handleRequestAction(req.client_id, "declined")}
                  >
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="sidebar-layout mt-16">
        {/* Client List Sidebar */}
        <div className="sidebar">
          <div className="card">
            <h3 className="mb-12">My Clients</h3>
            {clients.length === 0 ? (
              <p className="text-small text-dim">No clients assigned yet.</p>
            ) : (
              <div className="flex-column gap-8">
                {clients.map((client) => (
                  <button
                    key={client.user_id}
                    className={`btn ${selectedClient?.user_id === client.user_id ? "" : "btn-secondary"}`}
                    style={{ textAlign: "left", width: "100%" }}
                    onClick={() => selectClient(client)}
                  >
                    <div className="fw-600">{client.full_name}</div>
                    <div className="text-mini opacity-80">
                      {client.age}y | {client.gender}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Client Details */}
        <div className="sidebar-content">
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
              <div className="flex-wrap gap-8 mt-16 mb-16">
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
                <button
                  className={`btn ${activeTab === "photos" ? "" : "btn-secondary"}`}
                  onClick={() => setActiveTab("photos")}
                >
                  Photos
                </button>
              </div>

              {/* Workout Tab */}
              {activeTab === "workout" && (
                <div className="card">
                  <div className="flex-between mb-12">
                    <h3>Current Workout Plan</h3>
                    <button className="btn btn-small" onClick={assignWorkout} disabled={assigning}>
                      {assigning ? "Generating..." : "↻ Assign New"}
                    </button>
                  </div>
                  {clientData.workout.days?.length > 0 ? (
                    clientData.workout.days.map((day) => (
                      <div key={day.day_number} className="mb-16">
                        <h4 className="mb-12">Day {day.day_number}</h4>
                        <div className="table-responsive">
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
                  <div className="flex-between mb-12">
                    <h3>Current Diet Plan</h3>
                    <button className="btn btn-small" onClick={assignDiet} disabled={assigning}>
                      {assigning ? "Generating..." : "↻ Assign New"}
                    </button>
                  </div>
                  {clientData.diet.meals?.length > 0 ? (
                    <div className="table-responsive">
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
                    </div>
                  ) : (
                    <p className="text-small text-dim">No diet plan generated yet.</p>
                  )}
                </div>
              )}

              {/* Message Tab */}
              {activeTab === "message" && (
                <div className="card">
                  <h3 className="mb-12">Conversation with {selectedClient.full_name}</h3>

                  <div className="chat-container mb-16 bg-dim p-8">
                    {clientData.messages?.length === 0 ? (
                      <p className="text-dim text-center">No messages yet with this client.</p>
                    ) : (
                      clientData.messages.map((msg) => {
                        const isFromTrainer = msg.trainer_id === currentUserId;
                        return (
                          <div
                            key={msg.id}
                            className={`chat-message ${isFromTrainer ? "chat-message-user" : "chat-message-assistant"}`}
                          >
                            <div>{msg.message}</div>
                            <div className="chat-message-time">
                              {new Date(msg.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>

                  <div className="chat-input-area">
                    <textarea
                      value={trainerMessage}
                      onChange={(e) => setTrainerMessage(e.target.value)}
                      placeholder="Type your message here..."
                      rows={3}
                      className="chat-textarea"
                    />
                    <button
                      className="btn"
                      onClick={sendTrainerMessage}
                      disabled={sending || !trainerMessage.trim()}
                    >
                      {sending ? "Sending..." : "Send Message"}
                    </button>
                  </div>
                </div>
              )}

              {/* Photos Tab */}
              {activeTab === "photos" && (
                <div className="card">
                  <h3 className="mb-12">Progress Photos: {selectedClient.full_name}</h3>
                  {renderClientPhotos()}
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
