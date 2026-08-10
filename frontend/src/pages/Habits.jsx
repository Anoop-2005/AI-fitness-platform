import React, { useState } from "react";
import { api } from "../lib/api";
import { ClipboardList, CheckCircle2, Save } from "lucide-react";

const today = () => new Date().toISOString().slice(0, 10);

export default function Habits() {
  const [form, setForm] = useState({
    log_date: today(),
    water_l: 2,
    sleep_hours: 7,
    workout_done: false,
    steps: 5000,
    calories_consumed: 2000,
    calories_burned: 400, // Added to match backend schema
    protein_g: 100,
    mood: "good",        // Added to match backend schema
    energy_level: 3,     // Added to match backend schema (1-5 scale)
    stress_level: 2,     // Added to match backend schema (1-5 scale)
    weight_kg: "",
    waist_cm: "",        // Added to match backend schema
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
    setSaved(false);
  }

  async function handleSave() {
    setLoading(true);
    setError("");
    try {
      // Safely parse optional/numeric fields so empty strings become null or numbers
      const payload = {
        ...form,
        weight_kg: form.weight_kg === "" ? null : +form.weight_kg,
        waist_cm: form.waist_cm === "" ? null : +form.waist_cm,
        calories_consumed: +form.calories_consumed || 0,
        calories_burned: +form.calories_burned || 0,
        protein_g: +form.protein_g || 0,
        water_l: +form.water_l || 0,
        sleep_hours: +form.sleep_hours || 0,
        steps: +form.steps || 0,
        energy_level: form.energy_level ? +form.energy_level : null,
        stress_level: form.stress_level ? +form.stress_level : null,
      };

      await api.logHabit(payload);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page page-narrow">
      <div className="section-header">
      <ClipboardList size={22} /> 
      <h2>Log today</h2>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {saved && <div className="info-banner">Successfully saved log for {form.log_date}!</div>}

      <div className="card">
        {/* Date Field */}
        <div className="field">
          <label>Date</label>
          <input type="date" value={form.log_date} onChange={(e) => update("log_date", e.target.value)} />
        </div>

        {/* Core Metrics Row 1 */}
        <div className="field-row">
          <div className="field"><label>Water (L)</label><input type="number" step="0.1" value={form.water_l} onChange={(e) => update("water_l", e.target.value)} /></div>
          <div className="field"><label>Sleep (hrs)</label><input type="number" step="0.5" value={form.sleep_hours} onChange={(e) => update("sleep_hours", e.target.value)} /></div>
          <div className="field"><label>Steps</label><input type="number" value={form.steps} onChange={(e) => update("steps", e.target.value)} /></div>
        </div>

        {/* Workout Checkbox */}
         <div className="checkbox-row checkbox-margin">
          <input type="checkbox" id="wd" checked={form.workout_done} onChange={(e) => update("workout_done", e.target.checked)} />
          <label htmlFor="wd">Completed today's workout</label>
        </div>

        {/* Nutrition & Calories Row */}
        <div className="field-row">
          <div className="field"><label>Calories consumed</label><input type="number" value={form.calories_consumed} onChange={(e) => update("calories_consumed", e.target.value)} /></div>
          <div className="field"><label>Calories burned</label><input type="number" value={form.calories_burned} onChange={(e) => update("calories_burned", e.target.value)} /></div>
          <div className="field"><label>Protein (g)</label><input type="number" value={form.protein_g} onChange={(e) => update("protein_g", e.target.value)} /></div>
        </div>

        {/* Body Measurements Row */}
        <div className="field-row">
          <div className="field"><label>Weight (kg, optional)</label><input type="number" step="0.1" value={form.weight_kg} onChange={(e) => update("weight_kg", e.target.value)} placeholder="e.g. 75" /></div>
          <div className="field"><label>Waist (cm, optional)</label><input type="number" step="0.1" value={form.waist_cm} onChange={(e) => update("waist_cm", e.target.value)} placeholder="e.g. 85" /></div>
        </div>

        {/* Wellbeing & Mood Row */}
        <div className="field-row">
          <div className="field">
            <label>Mood</label>
            <select value={form.mood} onChange={(e) => update("mood", e.target.value)}>
              <option value="great">Great 😁</option>
              <option value="good">Good 🙂</option>
              <option value="neutral">Neutral 😐</option>
              <option value="tired">Tired 🥱</option>
              <option value="stressed">Stressed 😫</option>
            </select>
          </div>
          <div className="field">
            <label>Energy level (1-5)</label>
            <input type="number" min="1" max="5" value={form.energy_level} onChange={(e) => update("energy_level", e.target.value)} />
          </div>
          <div className="field">
            <label>Stress level (1-5)</label>
            <input type="number" min="1" max="5" value={form.stress_level} onChange={(e) => update("stress_level", e.target.value)} />
          </div>
        </div>

         <button className="btn mt-16" onClick={handleSave} disabled={loading}>
          <Save size={16} />
          {loading ? "Saving..." : "Save log"}
        </button>
      </div>
    </div>
  );
}