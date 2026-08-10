import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Dumbbell, RefreshCw, X, PlayCircle } from "lucide-react";

export default function Workout() {
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState(null);

  function load() {
    setLoading(true);
    api.getWorkoutPlan()
      .then(setPlan)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function regenerate() {
    setRegenerating(true);
    setError("");
    try {
      setPlan(await api.generateWorkoutPlan());
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
        Loading your workout plan…
      </div>
    );
  }

  return (
    <div className="page">
      <div className="flex-between">
        <h2 className="title-icon"><Dumbbell size={20} />Workout plan</h2>
        <button className="btn btn-secondary" onClick={regenerate} disabled={regenerating}>
          <RefreshCw size={14} className={regenerating ? "spin-icon" : ""} />
          {regenerating ? "Generating..." : "Regenerate"}
        </button>
      </div>
      {error && <div className="error-banner">{error}</div>}

      {!plan ? (
        <div className="card empty-state">
          <div className="empty-icon">🏋️</div>
          <p>No plan yet. Click regenerate to create one.</p></div>
      ) : (
        plan.days.map((day) => (
          <div className="card" key={day.day_number}>
            <h3><span className="badge">Day {day.day_number}</span></h3>
            
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
                {day.exercises.map((ex) => (
                  <tr
                    key={ex.id}
                    onClick={() => setSelectedExercise(ex)}
                    className="clickable-row"
                    title="Click to view details & instructions"
                  >
                    <td>
                      <span className="text-inherit">
                        {ex.name}
                      </span>
                    </td>
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
      )}

      {/* Exercise Detail Modal */}
      {selectedExercise && (
        <div className="modal-overlay">
          <div className="card modal-card">
            <div className="modal-header">
              <h3 className="modal-title">{selectedExercise.name}</h3>
              <button
                onClick={() => setSelectedExercise(null)}
                className="modal-close"
              >
                <X size={18} />
              </button>
            </div>

            <p className="prescription-text">
              <strong>Muscle Group:</strong> {selectedExercise.muscle_group} | <strong>Prescription:</strong> {selectedExercise.sets} sets × {selectedExercise.reps} reps ({selectedExercise.rest_seconds}s rest)
            </p>

            {/* Exercise Image */}
            {selectedExercise.image_url ? (
              <div className="exercise-image-container">
                <img
                  src={selectedExercise.image_url}
                  alt={selectedExercise.name}
                  className="exercise-image"
                />
              </div>
            ) : (
              <div className="no-image-msg">
                No image available for this exercise.
              </div>
            )}

            <div className="how-to-section">
              <h4 className="how-to-title">How to do it</h4>
              <p className="how-to-text">
                Watch a detailed form tutorial video for {selectedExercise.name}:
              </p>
              <a
                href={`https://www.youtube.com/results?search_query=${encodeURIComponent(selectedExercise.name + " exercise form tutorial")}`}
                target="_blank" x
                rel="noopener noreferrer"
                className="btn btn-youtube"
              >
                <PlayCircle size={16} /> Watch Form Tutorial on YouTube
                {/*▶ Watch Form Tutorial on YouTube*/}
              </a>
            </div>

            {/* Instructions */}
            <div className="instructions-section">
              <h4 className="instructions-title">Instructions</h4>
              <div
                className="modal-instructions"
                dangerouslySetInnerHTML={{
                  __html: selectedExercise.instructions || "Detailed textual instructions are currently unavailable for this exercise. Follow the video guide above for correct form."
                }}
              />
            </div>

            <div className="modal-footer">
              <button className="btn" onClick={() => setSelectedExercise(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}