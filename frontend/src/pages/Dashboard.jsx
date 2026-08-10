import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Flame, Activity, Zap, Gauge, Target, Scale, Wheat, Beef, Droplet, Droplets, CalendarClock, Dumbbell, Salad, ClipboardList, TrendingUp, ChevronRight,} from "lucide-react";

export default function Dashboard() {
  const [analysis, setAnalysis] = useState(null);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [streak, setStreak] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.getProfile(),
      api.getAnalysis().catch(() => null),
      api.getStreak().catch(() => ({ current_streak: 0 })),
      api.getProgressLogs ? api.getProgressLogs().catch(() => []) : Promise.resolve([])
    ])
      .then(([p, a, s, logs]) => {
        setProfile(p);
        setAnalysis(a);
        setStreak(s.current_streak || 0);

        // If you have recent logs, override current weight with the latest logged weight
        if (logs && logs.length > 0) {
          const latestLog = logs[0]; // Assuming newest log is first
          if (latestLog.weight_kg) {
            setProfile(prev => ({ ...prev, current_weight_kg: latestLog.weight_kg }));
          }
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleReset() {
    if (!window.confirm("Are you sure you want to reset your onboarding data?")) return;
    setResetting(true);
    try {
      await api.resetOnboarding();
      navigate("/onboarding");
    } catch (err) {
      alert("Failed to reset: " + err.message);
      setResetting(false);
    }
  }

  if (loading) {
    return (
      <div className="page page-wide">
        <div className="skeleton skeleton-text" style={{ width: "220px", height: "1.4rem" }} />
        <div className="card-grid grid-auto-180 mt-24">
          {[0, 1, 2, 3].map((i) => (
            <div className="card skeleton-card" key={i}>
              <div className="skeleton skeleton-text" />
              <div className="skeleton skeleton-value" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="card empty-state">
          <div className="empty-icon">🏁</div>
          <p className="mb-16">No profile yet — complete onboarding first.</p>
          <Link to="/onboarding" className="btn">Start onboarding</Link>
        </div>
      </div>
    );
  }

  // If profile exists but the AI plan is still building in the background
  if (!analysis) {
    return (
      <div className="page">
        <div className="card text-center p-40">
          <h2>🏗️ Building your personalized plan...</h2>
          <p className="text-dim mb-16">Your AI coach is calculating your optimal workouts, macros, and goals. This takes just a moment.</p>
          <button className="btn" onClick={() => window.location.reload()}>Refresh Page</button>
        </div>
      </div>
    );
  }

  // Derive ideal weight range from height using standard BMI healthy limits (18.5 - 24.9 kg/m²)
  const heightM = profile?.height_cm ? profile.height_cm / 100 : 1.7;
  const idealWeightMin = Math.round(18.5 * (heightM ** 2));
  const idealWeightMax = Math.round(24.9 * (heightM ** 2));

  return (
    <div className="page page-wide">
      <div className="flex-between">
        <h2>Welcome back, {profile?.full_name ? profile.full_name.split(" ")[0] : "User"}</h2>
        <button
          onClick={handleReset}
          disabled={resetting}
          className="btn btn-secondary btn-small"
        >
          {resetting ? "Resetting..." : "Retake Onboarding"}
        </button>
      </div>

      {/* Streak Widget Banner */}
      <div className="card streak-banner">
        <div className="flex-center gap-12">
          <div className="stat-icon"><Flame size={18} /></div>
          <div>
            <div className="stat-label">Workout Streak</div>
            <div className="streak-value">
              {streak} {streak === 1 ? "Day" : "Days"}
            </div>
          </div>
        </div>
        <Link to="/habits" className="btn btn-small">
          Log Today <ChevronRight size={14} />
        </Link>
      </div>

      {/* Core Body & Metabolism Metrics */}
      <div className="section-header">
        <Activity size={16} />
        <div className="stat-label">Metabolic profile</div>
      </div>
      <div className="card-grid grid-auto-180">
        <div className="card">
          <div className="stat-icon"><Gauge size={16} /></div>
          <div className="stat-label">BMI</div>
          <div className="stat-value">{analysis?.bmi}</div>
          <div className="text-tiny text-dim">{analysis?.bmi_category}</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Zap size={16} /></div>
          <div className="stat-label">BMR (Basal)</div>
          <div className="stat-value">{analysis?.bmr ? Math.round(analysis.bmr) : 0}</div>
          <div className="text-tiny text-dim">kcal / day</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Activity size={16} /></div>
          <div className="stat-label">TDEE (Maintenance)</div>
          <div className="stat-value">{analysis?.tdee ? Math.round(analysis.tdee) : 0}</div>
          <div className="text-tiny text-dim">kcal / day</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Target size={16} /></div>
          <div className="stat-label">Target Calories</div>
          <div className="stat-value stat-value-accent">
            {analysis?.target_calories ? Math.round(analysis.target_calories) : 0}
          </div>
          <div className="text-tiny text-dim">kcal / day</div>
        </div>
      </div>

      {/* Targets & Body Goals */}
      <div className="section-header">
        <Target size={16} />
        <div className="stat-label">Goals & Targets</div>
      </div>
      <div className="card-grid grid-auto-210">
        <div className="card">
          <div className="stat-icon"><Scale size={16} /></div>
          <div className="stat-label">Ideal Weight Range</div>
          <div className="stat-value stat-value-large">{idealWeightMin}kg – {idealWeightMax}kg</div>
          <div className="text-tiny text-dim">Based on healthy BMI bounds</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Target size={16} /></div>
          <div className="stat-label">Primary Goal Target</div>
          <div className="stat-value stat-value-capitalize">
            {profile?.primary_goal ? profile.primary_goal.replace("_", " ") : "General Fitness"}
          </div>
          <div className="text-tiny text-dim">Goal Weight: {profile?.target_weight_kg || profile?.current_weight_kg}kg</div>
        </div>
      </div>

      {/* Macro & Hydration Breakdown */}
      <div className="section-header">
        <Salad size={16} />
        <div className="stat-label">Daily nutrition breakdown</div>
      </div>
      <div className="card-grid grid-auto-140">
        <div className="card">
          <div className="stat-icon"><Beef size={16} /></div>
          <div className="stat-label">Protein</div>
          <div className="stat-value">{analysis?.macros?.protein_g || 0}g</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Wheat size={16} /></div>
          <div className="stat-label">Carbs</div>
          <div className="stat-value">{analysis?.macros?.carbs_g || 0}g</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Droplet size={16} /></div>
          <div className="stat-label">Fats</div>
          <div className="stat-value">{analysis?.macros?.fat_g || 0}g</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Wheat size={16} /></div>
          <div className="stat-label">Fiber</div>
          <div className="stat-value">{analysis?.macros?.fiber_g || 0}g</div>
        </div>
        <div className="card">
          <div className="stat-icon"><Droplets size={16} /></div>
          <div className="stat-label">Water Intake</div>
          <div className="stat-value">{analysis?.water_l || 0}L</div>
        </div>
      </div>

      {/* Timeline Estimate */}
      <div className="section-header">
        <CalendarClock size={16} />
        <div className="stat-label">Expected timeline to goal</div>
      </div>
      <div className="card">
        <p className="timeline-text">
          Best case: <b>{analysis?.timeline_weeks?.best_case_weeks} weeks</b> ·
          Expected: <b>{analysis?.timeline_weeks?.expected_weeks} weeks</b> ·
          Conservative: <b>{analysis?.timeline_weeks?.conservative_weeks} weeks</b>
        </p>
      </div>

      {/* Quick Navigation Links */}
      <div className="section-header">
        <div className="stat-label">Quick links</div>
      </div>
      <div className="card-grid">
        <Link to="/workout" className="card card-link quick-link-card">
          <div className="quick-link-icon"><Dumbbell size={18} /></div>
          <div className="quick-link-label">Workout plan</div>
          <ChevronRight size={16} className="quick-link-arrow" />
        </Link>
        <Link to="/diet" className="card card-link quick-link-card">
          <div className="quick-link-icon"><Salad size={18} /></div>
          <div className="quick-link-label">Diet plan</div>
          <ChevronRight size={16} className="quick-link-arrow" />
        </Link>
        <Link to="/habits" className="card card-link quick-link-card">
          <div className="quick-link-icon"><ClipboardList size={18} /></div>
          <div className="quick-link-label">Log today</div>
          <ChevronRight size={16} className="quick-link-arrow" />
        </Link>
        <Link to="/progress" className="card card-link quick-link-card">
          <div className="quick-link-icon"><TrendingUp size={18} /></div>
          <div className="quick-link-label">Progress</div>
          <ChevronRight size={16} className="quick-link-arrow" />
        </Link>
      </div>
    </div>
  );
}
