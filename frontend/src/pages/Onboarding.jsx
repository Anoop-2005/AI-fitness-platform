import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

const STEPS = ["Personal", "Health", "Fitness", "Diet"];
const EQUIPMENT_OPTIONS = ["dumbbell", "barbell", "bench", "cable machine", "squat rack", "jump rope", "machine"];

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    age: 28,
    gender: "male",
    height_cm: 175,
    current_weight_kg: 75,
    target_weight_kg: 70,
    occupation: "",
    activity_level: "moderate",
    sleep_hours: 7,
    diabetes: false,
    blood_pressure: "",
    heart_disease: false,
    thyroid: false,
    asthma: false,
    joint_pain: false,
    knee_problems: false,
    back_pain: false,
    injuries: "",
    allergies: "",
    medications: "",
    smoking: false,
    alcohol: false,
    primary_goal: "fat_loss",
    experience_level: "Beginner",
    gym_availability: "Home Workout",
    equipment_available: [],
    days_per_week: 4,
    session_minutes: 45,
    diet_type: "non_vegetarian",
    food_allergies: "",
    meals_per_day: 5,
    budget_tier: "medium",
  });

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleEquipment(item) {
    setForm((f) => ({
      ...f,
      equipment_available: f.equipment_available.includes(item)
        ? f.equipment_available.filter((e) => e !== item)
        : [...f.equipment_available, item],
    }));
  }

  async function handleFinish(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        ...form,
        food_allergies: form.food_allergies ? form.food_allergies.split(",").map((s) => s.trim()) : [],
      };
      await api.saveOnboarding(payload);
      await api.generateWorkoutPlan().catch(() => { });
      await api.generateDietPlan().catch(() => { });
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page page-medium">
      <h2>Tell us about you</h2>
      <p className="page-subtitle">
        This takes about two minutes and shapes every plan we generate.
      </p>

      {/* Step Indicator Bar */}
      <div className="step-bar">
        {STEPS.map((s, i) => (
          <div
            key={s}
            className={`step-item ${i === step ? "step-item-active" : "step-item-inactive"}`}
          >
            {i + 1}. {s}
          </div>
        ))}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleFinish} className="card">
        {step === 0 && (
          <>
             <h3 className="personal-title">Personal information</h3>

             <div className="field field-margin">
              <label>Full name</label>
              <input
                value={form.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                placeholder="e.g. Narender Modi"
                required
              />
            </div>

            <div className="field-row">
              <div className="field">
                <label>Age</label>
                <input type="number" value={form.age} onChange={(e) => update("age", +e.target.value)} />
              </div>
              <div className="field">
                <label>Gender</label>
                <select value={form.gender} onChange={(e) => update("gender", e.target.value)}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="field">
                <label>Height (cm)</label>
                <input type="number" value={form.height_cm} onChange={(e) => update("height_cm", +e.target.value)} />
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>Current weight (kg)</label>
                <input type="number" value={form.current_weight_kg} onChange={(e) => update("current_weight_kg", +e.target.value)} />
              </div>
              <div className="field">
                <label>Target weight (kg)</label>
                <input type="number" value={form.target_weight_kg} onChange={(e) => update("target_weight_kg", +e.target.value)} />
              </div>
              <div className="field">
                <label>Sleep (hours/night)</label>
                <input type="number" value={form.sleep_hours} onChange={(e) => update("sleep_hours", +e.target.value)} />
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>Occupation</label>
                <input value={form.occupation} onChange={(e) => update("occupation", e.target.value)} placeholder="e.g. Software Engineer" />
              </div>
              <div className="field">
                <label>Daily activity level</label>
                <select value={form.activity_level} onChange={(e) => update("activity_level", e.target.value)}>
                  <option value="sedentary">Sedentary (desk job)</option>
                  <option value="light">Light (1-3 days/week)</option>
                  <option value="moderate">Moderate (3-5 days/week)</option>
                  <option value="active">Active (6-7 days/week)</option>
                  <option value="very_active">Very active (physical job + training)</option>
                </select>
              </div>
            </div>
          </>
        )}

        {step === 1 && (
          <>
             <h3 className="health-title">Health assessment</h3>
             <p className="info-text-small">
               We use this only to filter out unsafe exercises — never to diagnose.
             </p>
             <div className="stat-label stat-label-margin">Conditions & Habits</div>
            {[
              ["diabetes", "Diabetes"],
              ["heart_disease", "Heart disease"],
              ["thyroid", "Thyroid issues"],
              ["asthma", "Asthma"],
              ["joint_pain", "Joint / shoulder pain"],
              ["knee_problems", "Knee problems"],
              ["back_pain", "Back pain"],
              ["smoking", "Smoking"],
              ["alcohol", "Regular alcohol consumption"],
            ].map(([key, label]) => (
              <div className="checkbox-row" key={key}>
                <input type="checkbox" id={key} checked={form[key]} onChange={(e) => update(key, e.target.checked)} />
                <label htmlFor={key}>{label}</label>
              </div>
            ))}

             <div className="field field-margin-sm">
               <label>Blood pressure (e.g. 120/80, or "unknown")</label>
              <input value={form.blood_pressure} onChange={(e) => update("blood_pressure", e.target.value)} />
            </div>
            <div className="field">
              <label>Previous injuries / surgeries</label>
              <textarea rows={2} value={form.injuries} onChange={(e) => update("injuries", e.target.value)} />
            </div>
            <div className="field">
              <label>Allergies / current medications</label>
              <textarea rows={2} value={form.medications} onChange={(e) => update("medications", e.target.value)} />
            </div>
          </>
        )}

        {step === 2 && (
          <>
             <h3 className="fitness-title">Fitness assessment</h3>
            <div className="field-row">
              <div className="field">
                <label>Primary goal</label>
                <select value={form.primary_goal} onChange={(e) => update("primary_goal", e.target.value)}>
                  <option value="weight_loss">Weight loss</option>
                  <option value="fat_loss">Fat loss</option>
                  <option value="muscle_gain">Muscle gain</option>
                  <option value="strength">Strength</option>
                  <option value="body_recomposition">Body recomposition</option>
                  <option value="athletic_performance">Athletic performance</option>
                  <option value="general_fitness">General fitness</option>
                </select>
              </div>
              <div className="field">
                <label>Experience level</label>
                <select value={form.experience_level} onChange={(e) => update("experience_level", e.target.value)}>
                  <option>Beginner</option>
                  <option>Intermediate</option>
                  <option>Advanced</option>
                </select>
              </div>
              <div className="field">
                <label>Where you train</label>
                <select value={form.gym_availability} onChange={(e) => update("gym_availability", e.target.value)}>
                  <option>Home Workout</option>
                  <option>Commercial Gym</option>
                  <option>Hybrid</option>
                </select>
              </div>
            </div>

            <div className="field-row">
              <div className="field">
                <label>Workout days / week</label>
                <input type="number" min={1} max={7} value={form.days_per_week} onChange={(e) => update("days_per_week", +e.target.value)} />
              </div>
              <div className="field">
                <label>Session length (minutes)</label>
                <input type="number" value={form.session_minutes} onChange={(e) => update("session_minutes", +e.target.value)} />
              </div>
            </div>

            {form.gym_availability !== "Commercial Gym" && (
               <div className="field field-margin-xs">
                 <label>Equipment available at home</label>
                 <div className="equipment-grid">
                   {EQUIPMENT_OPTIONS.map((eq) => {
                     const isSelected = form.equipment_available.includes(eq);
                     return (
                       <button
                         type="button"
                         key={eq}
                         className={`btn ${isSelected ? "equipment-btn-selected" : "equipment-btn"}`}
                         onClick={() => toggleEquipment(eq)}
                       >
                         {eq}
                       </button>
                     );
                   })}
                 </div>
               </div>
            )}
          </>
        )}

        {step === 3 && (
          <>
             <h3 className="diet-title">Dietary preferences</h3>
            <div className="field-row">
              <div className="field">
                <label>Food preference</label>
                <select value={form.diet_type} onChange={(e) => update("diet_type", e.target.value)}>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="vegan">Vegan</option>
                  <option value="eggetarian">Eggetarian</option>
                  <option value="non_vegetarian">Non-vegetarian</option>
                </select>
              </div>
              <div className="field">
                <label>Meals per day</label>
                <input type="number" min={3} max={8} value={form.meals_per_day} onChange={(e) => update("meals_per_day", +e.target.value)} />
              </div>
            </div>

             <div className="field field-margin-sm">
               <label>Budget tier</label>
              <select value={form.budget_tier} onChange={(e) => update("budget_tier", e.target.value)}>
                <option value="budget">Budget-friendly</option>
                <option value="medium">Medium</option>
                <option value="premium">Premium</option>
              </select>
            </div>

            <div className="field">
              <label>Food allergies (comma separated)</label>
              <input value={form.food_allergies} onChange={(e) => update("food_allergies", e.target.value)} placeholder="e.g. peanut, shellfish" />
            </div>
          </>
        )}

        
        {/* Wizard Navigation */}
        <div className="wizard-nav">
          <button
            type="button"
            className={`btn ${step === 0 ? "wizard-back" : "wizard-back-enabled"}`}
            disabled={step === 0}
            onClick={() => setStep((s) => s - 1)}
          >
            Back
          </button>

          {step < STEPS.length - 1 ? (
            <button type="button" className="btn" onClick={() => setStep((s) => s + 1)} disabled={loading}>
              Continue
            </button>
          ) : (
            <button type="submit" className={`btn ${loading ? "cursor-not-allowed" : "cursor-pointer"}`} disabled={loading}>
              {loading ? "Building your plan…" : "Generate my plan"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}