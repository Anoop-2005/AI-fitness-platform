import React, { useEffect, useState } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { api } from "../lib/api";

export default function Progress() {
  const [logs, setLogs] = useState([]);
  const [review, setReview] = useState(null);
  const [profile, setProfile] = useState(null);
  const [goalPrediction, setGoalPrediction] = useState(null);
  const [bodyComp, setBodyComp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("weekly");

  useEffect(() => {
    Promise.all([
      api.getHabits(90),
      api.getWeeklyReview().catch(() => null),
      api.getProfile().catch(() => null),
      api.getGoalPrediction().catch(() => null),
      api.getBodyComposition().catch(() => null),
    ])
      .then(([l, r, p, g, bc]) => { setLogs(l); setReview(r); setProfile(p); setGoalPrediction(g); setBodyComp(bc); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page">Loading...</div>;

  const heightM = profile?.height_cm ? profile.height_cm / 100 : 1.7;

  // Format chart data arrays from logs
  const formattedLogs = logs.map((l) => ({
    date: l.log_date.slice(5),
    fullDate: l.log_date,
    weight: l.weight_kg || null,
    bmi: l.weight_kg ? +(l.weight_kg / (heightM ** 2)).toFixed(1) : null,
    waist: l.waist_cm || null,
    caloriesConsumed: l.calories_consumed || 0,
    caloriesBurned: l.calories_burned || 0,
    protein: l.protein_g || 0,
    water: l.water_l || 0,
    steps: l.steps || 0,
    workoutDone: l.workout_done ? 1 : 0,
  }));

  // Aggregate into weekly or monthly buckets
  const aggregateByTimeRange = () => {
    const buckets = {};
    logs.forEach((l) => {
      const d = new Date(l.log_date);
      let key;
      if (timeRange === "weekly") {
        const weekStart = new Date(d);
        weekStart.setDate(d.getDate() - d.getDay());
        key = weekStart.toISOString().slice(0, 10);
      } else {
        key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      }
      if (!buckets[key]) {
        buckets[key] = { date: key, count: 0, totalCalories: 0, totalBurned: 0, totalProtein: 0, totalWater: 0, workoutDays: 0, weights: [] };
      }
      buckets[key].count++;
      buckets[key].totalCalories += l.calories_consumed || 0;
      buckets[key].totalBurned += l.calories_burned || 0;
      buckets[key].totalProtein += l.protein_g || 0;
      buckets[key].totalWater += l.water_l || 0;
      if (l.workout_done) buckets[key].workoutDays++;
      if (l.weight_kg) buckets[key].weights.push(l.weight_kg);
    });

    return Object.values(buckets).map((b) => ({
      date: b.date,
      avgCalories: Math.round(b.totalCalories / b.count),
      avgBurned: Math.round(b.totalBurned / b.count),
      avgProtein: Math.round(b.totalProtein / b.count),
      avgWater: +(b.totalWater / b.count).toFixed(1),
      workoutDays: b.workoutDays,
      avgWeight: b.weights.length ? +(b.weights.reduce((a, w) => a + w, 0) / b.weights.length).toFixed(1) : null,
    })).sort((a, b) => a.date.localeCompare(b.date));
  };

  const aggregatedData = aggregateByTimeRange();

  return (
    <div className="page page-wide">
      <div className="flex-between">
        <h2>Progress & Analytics</h2>
        <div className="flex-wrap gap-8">
          <button 
            className="btn btn-secondary btn-small" 
            onClick={() => api.downloadReport("weekly").catch(err => alert(err.message))}
          >
            PDF Weekly
          </button>
          <button 
            className="btn btn-secondary btn-small" 
            onClick={() => api.downloadReport("monthly").catch(err => alert(err.message))}
          >
            PDF Monthly
          </button>
          <button
            className={`btn ${timeRange === "weekly" ? "" : "btn-secondary"}`}
            onClick={() => setTimeRange("weekly")}
          >
            Weekly
          </button>
          <button
            className={`btn ${timeRange === "monthly" ? "" : "btn-secondary"}`}
            onClick={() => setTimeRange("monthly")}
          >
            Monthly
          </button>
        </div>
      </div>
      <p className="page-description">
        Track your trends, measurements, and consistency over time.
      </p>

      {logs.length === 0 ? (
        <div className="card"><p>No logs yet — start logging on the Habits page to view your charts.</p></div>
      ) : (
        <div className="flex-column gap-24">

          {/* 1. BMI Trend Chart */}
          <div className="card">
            <h3 className="chart-title">BMI Trend</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedLogs.filter(l => l.bmi !== null)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" fontSize={12} stroke="#94a3b8" />
                  <YAxis domain={["auto", "auto"]} fontSize={12} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                  <Line type="monotone" dataKey="bmi" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} name="BMI" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 2. Weight Trend Chart */}
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

          {/* 3. Body Measurements (Waist cm) */}
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

          {/* 4. Strength Progression (proxy: workout days per period) */}
          <div className="card">
            <h3 className="chart-title">Workout Consistency ({timeRange})</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aggregatedData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" fontSize={12} stroke="#94a3b8" />
                  <YAxis fontSize={12} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                  <Legend />
                  <Bar dataKey="workoutDays" fill="#3b82f6" name="Workout Days" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 5. Calories Consumed vs Burned */}
          <div className="card">
            <h3 className="chart-title">Calories: Consumed vs Burned ({timeRange})</h3>
            <div className="chart-container-lg">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aggregatedData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" fontSize={12} stroke="#94a3b8" />
                  <YAxis fontSize={12} stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#334155", color: "#fff" }} />
                  <Legend />
                  <Bar dataKey="avgCalories" fill="#f59e0b" name="Avg Consumed (kcal)" />
                  <Bar dataKey="avgBurned" fill="#ef4444" name="Avg Burned (kcal)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 6. Protein & Water Intake */}
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

      {/* Goal Prediction Section */}
      {goalPrediction && !goalPrediction.error && (
        <>
          <div className="stat-label stat-margin-lg">Goal prediction</div>
          <div className="card">
            <div className="card-grid grid-auto-180">
              <div>
                <div className="stat-label">Achievement</div>
                <div className="stat-value stat-value-accent">{goalPrediction.goal_achievement_pct || 0}%</div>
              </div>
              <div>
                <div className="stat-label">Weekly change</div>
                <div className="stat-value">{goalPrediction.weekly_weight_change_kg > 0 ? '+' : ''}{goalPrediction.weekly_weight_change_kg}kg</div>
              </div>
              <div>
                <div className="stat-label">Monthly projection</div>
                <div className="stat-value">{goalPrediction.monthly_projection_kg > 0 ? '+' : ''}{goalPrediction.monthly_projection_kg}kg</div>
              </div>
              <div>
                <div className="stat-label">Est. completion</div>
                <div className="stat-value text-1-3">{goalPrediction.predicted_completion_date || '—'}</div>
              </div>
            </div>
            {goalPrediction.plateau_detected && (
              <div className="error-banner error-banner-margin">Plateau detected — your plan will adjust to break through.</div>
            )}
          </div>
        </>
      )}

      {/* Body Composition Insights */}
      {bodyComp && bodyComp.insights && bodyComp.insights.length > 0 && (
        <>
          <div className="stat-label stat-margin-lg">Body composition insights</div>
          <div className="card">
            <div className="flex-column gap-12">
              {bodyComp.insights.map((insight, i) => (
                <div key={i} className="text-small">
                  <strong>{insight.note}</strong>
                </div>
              ))}
            </div>
            <p className="text-mini text-dim mt-12">
              ⚠️ {bodyComp.disclaimer}
            </p>
          </div>
        </>
      )}

      {/* Weekly Review Summary Section */}
      <div className="stat-label stat-margin-lg">Weekly performance review</div>
      {review && review.stats && Object.keys(review.stats).length > 0 ? (
          <div className="card">
            <div className="card-grid grid-auto-180">
              <div><div className="stat-label">Workout completion</div><div className="stat-value">{review.stats.workout_completion_pct}%</div></div>
              <div><div className="stat-label">Avg water</div><div className="stat-value">{review.stats.avg_water_l}L</div></div>
              <div><div className="stat-label">Weight change</div><div className="stat-value">{review.stats.weight_change_kg}kg</div></div>
              <div><div className="stat-label">Waist change</div><div className="stat-value">{review.stats.waist_change_cm || 0}cm</div></div>
              <div><div className="stat-label">Total burned</div><div className="stat-value">{review.stats.total_calories_burned || 0}</div></div>
              <div><div className="stat-label">Avg sleep</div><div className="stat-value">{review.stats.avg_sleep_hours || 0}h</div></div>
            </div>
            {review.plateau_detected && <div className="error-banner error-banner-margin">Possible plateau detected — your next plan will adjust for this.</div>}
            <p className="review-summary">{review.summary}</p>
          </div>
      ) : (
        <div className="card"><p>Not enough logs yet this week to compile a review.</p></div>
      )}
    </div>
  );
}
