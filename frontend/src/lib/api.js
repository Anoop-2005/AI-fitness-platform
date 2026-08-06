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
};
