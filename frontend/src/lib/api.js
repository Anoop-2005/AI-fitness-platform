import { supabase } from "./supabaseClient";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, { method = "GET", body } = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  const headers = { "Content-Type": "application/json" };
  if (session) headers.Authorization = `Bearer ${session.access_token}`;

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.error || `Request failed (${resp.status})`);
  return data;
}

export const api = {
  saveOnboarding: (payload) => request("/api/onboarding", { method: "POST", body: payload }),
  getProfile: () => request("/api/onboarding"),
  getAnalysis: () => request("/api/onboarding/analysis"),

  generateWorkoutPlan: () => request("/api/plans/workout", { method: "POST" }),
  getWorkoutPlan: () => request("/api/plans/workout/latest"),
  generateDietPlan: () => request("/api/plans/diet", { method: "POST" }),
  getDietPlan: () => request("/api/plans/diet/latest"),
  getWeeklyReview: () => request("/api/review/weekly"),

  logHabit: (payload) => request("/api/habits", { method: "POST", body: payload }),
  getHabits: (days = 30) => request(`/api/habits?days=${days}`),
  resetOnboarding: () => request("/api/onboarding", { method: "DELETE" }),
  getStreak: () => request("/api/habits/streak"),
  coachChat: (message) => request("/api/coach/chat", { method: "POST", body: { message } }),
  uploadPhoto: (viewType, imageData) => request("/api/photos/upload", { method: "POST", body: { view_type: viewType, image_data: imageData },}),
  listPhotos: (viewType) => request(`/api/photos/list${viewType ? `?view_type=${viewType}` : ""}`),
  getLatestPhotos: () => request("/api/photos/latest"),
  deletePhoto: (photoId) => request(`/api/photos/${photoId}`, { method: "DELETE" }),

  // Admin API
  adminListTrainers: () => request("/api/admin/trainers"),
  adminListClients: () => request("/api/admin/clients"),
  adminListUsers: (role) => request(`/api/admin/users${role ? `?role=${role}` : ""}`),
  adminStats: () => request("/api/admin/stats"),
  adminDeleteUser: (userId) => request(`/api/admin/users/${userId}`, { method: "DELETE" }),

  // Trainer API
  trainerGetClients: () => request("/api/trainer/clients"),
  trainerGetClientProfile: (clientId) => request(`/api/trainer/clients/${clientId}/profile`),
  trainerGetClientWorkout: (clientId) => request(`/api/trainer/clients/${clientId}/workout`),
  trainerGetClientDiet: (clientId) => request(`/api/trainer/clients/${clientId}/diet`),
  trainerGetClientProgress: (clientId, days) => request(`/api/trainer/clients/${clientId}/progress?days=${days || 30}`),
  trainerGetClientAnalysis: (clientId) => request(`/api/trainer/clients/${clientId}/analysis`),
  trainerSendMessage: (clientId, message) => request("/api/trainer/messages", { method: "POST", body: { client_id: clientId, message } }),
  trainerGetMessages: (clientId) => request(`/api/trainer/messages/${clientId}`),
  getMyTrainer: () => request("/api/trainer/my-trainer"),
  getMyMessages: () => request("/api/trainer/my-messages"),
  clientSendMessage: (message) => request("/api/trainer/my-messages", {method: "POST",body: { message },}),
  trainerGetMessages: (clientId) => request(`/api/trainer/messages/${clientId}`),
};
