import React, { useEffect, useState } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { api } from "../lib/api";
import { TrendingUp } from "lucide-react";

export default function Progress() {
  const [logs, setLogs] = useState([]);
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch last 60 days of habit logs and latest weekly review
    Promise.all([api.getHabits(60), api.getWeeklyReview().catch(() => null)])
      .then(([l, r]) => { setLogs(l); setReview(r); })
      .finally(() => setLoading(false));
  }, []);

  /*if (loading) return <div className="page">Loading...</div>;*/
  if (loading) {
    return (
      <div className="page page-loading">
        <div className="spinner"></div>
        <p>Loading analytics and progress...</p>
      </div>
    );
  }

  // Format chart data arrays from logs
  const formattedLogs = logs.map((l) => ({
    date: l.log_date.slice(5), // MM-DD format
    weight: l.weight_kg || null,
    waist: l.waist_cm || null,
    caloriesConsumed: l.calories_consumed || 0,
    caloriesBurned: l.calories_burned || 0,
    protein: l.protein_g || 0,
    water: l.water_l || 0,
    steps: l.steps || 0,
    workoutDone: l.workout_done ? 1 : 0
  }));

  return (
    <div className="page page-wide">
      <div className="section-header">
        <TrendingUp size={22} />
        <h2>Progress & Analytics</h2>
      </div>
      <p className="page-description">
        Track your trends, measurements, and consistency over time.
      </p>

      {logs.length === 0 ? (
        <div className="empty-state card"><p>No logs yet — start logging on the Habits page to view your charts.</p></div>
      ) : (
        <div className="flex-column gap-24">

          {/* 1. Weight Trend Chart */}
          <div className="card">
            <h3 className="chart-title">Weight Trend (kg)</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedLogs.filter(l => l.weight !== null)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" fontSize={12} stroke="#94a3b8" />
                  <YAxis domain={["auto", "auto"]} fontSize={12} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                  <Line type="monotone" dataKey="weight" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="Weight (kg)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 2. Body Measurements (Waist cm) */}
          <div className="card">
            <h3 className="chart-title">Body Measurements (Waist cm)</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedLogs.filter(l => l.waist !== null)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" fontSize={12} stroke="#94a3b8" />
                  <YAxis domain={["auto", "auto"]} fontSize={12} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                  <Line type="monotone" dataKey="waist" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} name="Waist (cm)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 3. Calories Consumed vs Burned */}
          <div className="card">
            <h3 className="chart-title">Calories: Consumed vs Burned</h3>
            <div className="chart-container-lg">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={formattedLogs}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" fontSize={12} stroke="#94a3b8" />
                  <YAxis fontSize={12} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                  <Legend />
                  <Bar dataKey="caloriesConsumed" fill="#f59e0b" name="Consumed (kcal)" />
                  <Bar dataKey="caloriesBurned" fill="#ef4444" name="Burned (kcal)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 4. Protein & Water Intake */}
          <div className="card-grid grid-split">
            <div className="card card-no-margin">
              <h3 className="chart-title">Protein Intake (g)</h3>
              <div className="chart-container-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={formattedLogs}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" fontSize={10} stroke="#94a3b8" />
                    <YAxis fontSize={10} stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                    <Line type="monotone" dataKey="protein" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Protein (g)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card card-no-margin">
              <h3 className="chart-title">Water Intake (L)</h3>
              <div className="chart-container-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={formattedLogs}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" fontSize={10} stroke="#94a3b8" />
                    <YAxis fontSize={10} stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                    <Line type="monotone" dataKey="water" stroke="#06b6d4" strokeWidth={2} dot={false} name="Water (L)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* Weekly Review Summary Section */}
      {/*<div className="stat-label stat-margin-lg">Weekly performance review</div>*/}
      <div className="section-header mt-32">
        <div className="stat-label">Weekly performance review</div>
      </div>
      {review && review.stats && Object.keys(review.stats).length > 0 ? (
        <div className="card">
          <div className="card-grid">
            <div><div className="stat-label">Workout completion</div><div className="stat-value">{review.stats.workout_completion_pct}%</div></div>
            <div><div className="stat-label">Avg water</div><div className="stat-value">{review.stats.avg_water_l}L</div></div>
            <div><div className="stat-label">Weight change</div><div className="stat-value">{review.stats.weight_change_kg}kg</div></div>
          </div>
          {review.plateau_detected && <div className="error-banner error-banner-margin">Possible plateau detected — your next plan will adjust for this.</div>}
          <p className="review-summary">{review.summary}</p>
        </div>
      ) : (
        <div className="card">
          <div className="empty-state">
            <p>Not enough logs yet this week to compile a review.</p></div>
          </div>
      )}
    </div>
  );
}