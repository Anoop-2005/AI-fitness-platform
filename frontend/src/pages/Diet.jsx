import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Salad, RefreshCw, X } from "lucide-react";

export default function Diet() {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [selectedMeal, setSelectedMeal] = useState(null); // Modal detail state

  function load() {
    setLoading(true);
    api.getDietPlan().then(setPlan).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function regenerate() {
    setRegenerating(true);
    setError("");
    try {
      setPlan(await api.generateDietPlan());
    } catch (e) {
      setError(e.message);
    } finally {
      setRegenerating(false);
    }
  }

  /*if (loading) return <div className="page">Loading...</div>;*/
  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        Loading your diet plan…
      </div>
    );
  }

  return (
    <div className="page">
      <div className="flex-between">
        <h2 className="title-icon"><Salad size={20} /> Diet plan</h2>
        <button className="btn btn-secondary" onClick={regenerate} disabled={regenerating}>
          <RefreshCw size={14} className={regenerating ? "spin-icon" : ""} />
          {regenerating ? "Generating..." : "Regenerate"}
        </button>
      </div>
      {error && <div className="error-banner">{error}</div>}

      {!plan ? (
        <div className="card empty-state">
        <div className="empty-icon">🥗</div>
        <p>No plan yet. Click regenerate to create one.</p></div>
      ) : (
        <div className="card">
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
              {plan.meals.map((m) => (
                <tr
                  key={m.id}
                  onClick={() => setSelectedMeal(m)}
                  className="clickable-row"
                  title="Click to view full nutritional breakdown & recipe"
                >
                  <td className="text-capitalize">{m.meal_slot.replace("_", " ")}</td>
                  <td>
                    <span className="text-inherit">
                      {m.name}
                    </span>
                  </td>
                  <td>{Math.round(m.calories)} kcal</td>
                  <td>{Math.round(m.protein_g)}g</td>
                  <td>{Math.round(m.carbs_g)}g</td>
                  <td>{Math.round(m.fat_g)}g</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Meal Detail Modal */}
      {selectedMeal && (
        <div className="modal-overlay">
          <div className="card modal-card">
            <div className="modal-header">
              <h3 className="modal-title text-capitalize">
                {selectedMeal.meal_slot.replace("_", " ")}: {selectedMeal.name}
              </h3>
              <button
                onClick={() => setSelectedMeal(null)}
                className="modal-close"
              >
                 <X size={18} />
              </button>
            </div>

            {/* Core Macros Grid */}
            <div className="macro-grid">
              <div>
                <div className="macro-label">Calories</div>
                <div className="macro-value">{Math.round(selectedMeal.calories)} kcal</div>
              </div>
              <div>
                <div className="macro-label">Protein</div>
                <div className="macro-value">{Math.round(selectedMeal.protein_g)}g</div>
              </div>
              <div>
                <div className="macro-label">Carbs</div>
                <div className="macro-value">{Math.round(selectedMeal.carbs_g)}g</div>
              </div>
              <div>
                <div className="macro-label">Fat</div>
                <div className="macro-value">{Math.round(selectedMeal.fat_g)}g</div>
              </div>
              {/*<div>
                <div className="macro-label">Fiber</div>
                <div className="macro-value">{Math.round(selectedMeal.fiber_g || 0)}g</div>
              </div>*/}
            </div>

            {/* Serving Size & Cooking Time */}
            <p className="serving-text">
              <strong>Portion Size:</strong> {selectedMeal.serving_size || "1 serving"} | <strong>Cooking Time:</strong> ~15 mins
            </p>

            {/* Recipe Instructions */}
            <div className="recipe-section">
              <h4 className="recipe-title">Preparation Recipe</h4>
              <p className="modal-recipe">
                Prepare ingredients to match the target portion size. Cook using minimal healthy fats (olive oil or cooking spray) and season with natural herbs and spices according to your personal dietary preference.
              </p>
            </div>

            {/* Healthier Alternatives */}
            <div className="recipe-section">
              <h4 className="recipe-title">Healthier Alternatives / Swaps</h4>
              <p className="modal-recipe">
                Can substitute with lean plant-based proteins, whole-grain alternatives, or lower-calorie variations depending on your daily caloric target.
              </p>
            </div>

            <div className="modal-footer">
              <button className="btn" onClick={() => setSelectedMeal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}