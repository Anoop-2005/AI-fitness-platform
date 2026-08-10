import React, { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";
import { Camera } from "lucide-react";

const VIEW_TYPES = [
  { key: "front", label: "Front", icon: "🧍", description: "Face the camera directly" },
  { key: "side", label: "Side", icon: "🚶", description: "Stand in profile view" },
  { key: "back", label: "Back", icon: "🔙", description: "Turn your back to the camera" },
];

export default function ProgressPhotos() {
  const [photos, setPhotos] = useState({ front: [], side: [], back: [] });
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedView, setSelectedView] = useState("front");
  const [compareMode, setCompareMode] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadPhotos();
  }, []);

  async function loadPhotos() {
    try {
      const allPhotos = await api.listPhotos();
      const grouped = { front: [], side: [], back: [] };
      allPhotos.forEach((p) => {
        if (grouped[p.view_type]) {
          grouped[p.view_type].push(p);
        }
      });
      setPhotos(grouped);
    } catch (err) {
      console.error("Failed to load photos:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(photoId) {
    if (!window.confirm("Delete this photo? This cannot be undone.")) return;
    try {
      await api.deletePhoto(photoId);
      await loadPhotos();
    } catch (err) {
      alert("Failed to delete: " + err.message);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setAnalysisResult(null);

    try {
      const base64 = await fileToBase64(file);
      setAnalyzing(true);
      const analysis = await analyzePosture(base64, selectedView);
      setAnalysisResult(analysis);
      await api.uploadPhoto(selectedView, base64);
      await loadPhotos();
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploading(false);
      setAnalyzing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("Failed to load image"));
      img.src = src;
    });
  }

  async function analyzePosture(imageData, viewType) {
    try {
      const vision = await import("@mediapipe/tasks-vision");
      const { PoseLandmarker, FilesetResolver } = vision;

      const filesetResolver = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.x/wasm"
      );

      const pose = await PoseLandmarker.createFromOptions(filesetResolver, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
          delegate: "CPU",
        },
        runningMode: "IMAGE",
        numPoses: 1,
      });

      const img = await loadImage(imageData);
      const result = pose.detect(img);

      if (!result?.landmarks?.[0]) {
        return { detected: false, message: "No pose detected. Stand further back so your full body is visible." };
      }

      const landmarks = result.landmarks[0];
      return {
        detected: true,
        viewType,
        postureScore: calculatePostureScore(landmarks, viewType),
        observations: generateObservations(landmarks, viewType),
        measurements: estimateMeasurements(landmarks),
      };
    } catch (err) {
      return { detected: false, message: "Analysis failed: " + err.message };
    }
  }

  function calculatePostureScore(landmarks, viewType) {
    const scores = {
      symmetry: calculateSymmetry(landmarks, viewType),
      alignment: calculateAlignment(landmarks, viewType),
      balance: calculateBalance(landmarks, viewType),
    };
    return Math.round((scores.symmetry + scores.alignment + scores.balance) / 3);
  }

  function calculateSymmetry(landmarks, viewType) {
    if (viewType === "front") {
      const shoulderDiff = Math.abs(landmarks[11].y - landmarks[12].y);
      const hipDiff = Math.abs(landmarks[23].y - landmarks[24].y);
      return Math.max(0, 100 - (shoulderDiff + hipDiff) * 500);
    }
    return 75;
  }

  function calculateAlignment(landmarks, viewType) {
    if (viewType === "side") {
      const verticalDeviation = Math.abs(landmarks[7].x - landmarks[27].x) + Math.abs(landmarks[11].x - landmarks[23].x);
      return Math.max(0, 100 - verticalDeviation * 200);
    }
    return 75;
  }

  function calculateBalance(landmarks) {
    const centerX = (landmarks[27].x + landmarks[28].x) / 2;
    return Math.max(0, 100 - Math.abs(landmarks[0].x - centerX) * 300);
  }

  function generateObservations(landmarks, viewType) {
    const observations = [];
    const score = calculatePostureScore(landmarks, viewType);

    if (score >= 85) observations.push("✅ Great posture alignment!");
    else if (score >= 70) observations.push("👍 Good posture with minor areas for improvement.");
    else observations.push("⚠️ Posture could benefit from targeted exercises.");

    if (viewType === "front" && Math.abs(landmarks[11].y - landmarks[12].y) > 0.03) {
      observations.push("📐 Shoulders appear uneven - consider unilateral shoulder work.");
    }
    if (viewType === "side" && landmarks[7].x < landmarks[11].x - 0.05) {
      observations.push("🦒 Forward head posture detected - try chin tucks and neck stretches.");
    }
    return observations;
  }

  function estimateMeasurements(landmarks) {
    return {
      estimatedHeightPx: Math.round(Math.abs(landmarks[0].y - landmarks[27].y) * 100),
      shoulderWidth: Math.round(Math.abs(landmarks[11].x - landmarks[12].x) * 100),
      hipWidth: Math.round(Math.abs(landmarks[23].x - landmarks[24].x) * 100),
    };
  }

  /*if (loading) return <div className="page">Loading...</div>;*/
  if (loading) {
    return (
      <div className="page page-loading">
        <div className="spinner"></div>
        <p>Loading progress photos...</p>
      </div>
    );
  }

  return (
    <div className="page page-wide">
      <div className="section-header flex-between">
        <div className="flex-center gap-8">
          <Camera size={22} />
          <h2>Progress Photos</h2>
        </div>
        <button className="btn btn-secondary btn-small" onClick={() => setCompareMode(!compareMode)}>
          {compareMode ? "Exit Compare" : "🔍 Compare Photos"}
        </button>
      </div>

      {/* Upload Section */}
      <div className="card">
        <h3 className="mb-12">Upload New Photo</h3>
        <div className="field-row mb-12">
          {VIEW_TYPES.map((vt) => (
            <label key={vt.key} className="checkbox-row">
              <input
                type="radio"
                name="viewType"
                value={vt.key}
                checked={selectedView === vt.key}
                onChange={(e) => setSelectedView(e.target.value)}
              />
              <span>{vt.icon} {vt.label}</span>
            </label>
          ))}
        </div>
        <p className="text-small text-dim mb-12">
          {VIEW_TYPES.find((v) => v.key === selectedView)?.description}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleUpload}
          disabled={uploading}
        />
        {uploading && (
          <div className="flex-center gap-8 mt-12">
            <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }}></div>
            <p className="text-small">{analyzing ? "Analyzing posture..." : "Uploading..."}</p>
          </div>
        )}
      </div>

      {/* Analysis Result */}
      {analysisResult && (
        <div className="card">
          <h3 className="mb-12"> AI Posture Analysis</h3>
          {analysisResult.detected ? (
            <>
              <div className="stat-value mb-12">Posture Score: {analysisResult.postureScore}/100</div>
              <ul className="pl-20">
                {analysisResult.observations.map((obs, i) => (
                  <li key={i} className="mb-12">{obs}</li>
                ))}
              </ul>
              <p className="text-small text-dim mt-12">
                ⚠️ This is informational only and not a medical diagnosis.
              </p>
            </>
          ) : (
            <p>{analysisResult.message}</p>
          )}
        </div>
      )}

      {/* Compare Mode */}
      {compareMode && (
        <div className="card">
          <h3 className="mb-12">Side-by-Side Comparison</h3>
          <div className="card-grid grid-split">
            {VIEW_TYPES.map((vt) => {
              const latest = photos[vt.key]?.[0];
              return (
                <div key={vt.key} className="text-center">
                  <h4 className="mb-12">{vt.icon} {vt.label}</h4>
                  {latest ? (
                    <img
                      src={latest.photo_url}
                      alt={`${vt.label} view`}
                      className="exercise-image"
                    />
                  ) : (
                    <div className="empty-state">
                      <p>No photos uploaded yet.</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Photo Gallery by View Type */}
      {VIEW_TYPES.map((vt) => (
        <div key={vt.key} className="card">
          <h3 className="mb-12">{vt.icon} {vt.label} View</h3>
          {photos[vt.key]?.length > 0 ? (
            <div className="photo-gallery">
              {photos[vt.key].map((photo) => (
                <div key={photo.id} className="photo-item">
                  <img
                    src={photo.photo_url}
                    alt={`${vt.label} ${photo.uploaded_at}`}
                  />
                  <p className="text-mini text-dim mt-4">
                    {new Date(photo.uploaded_at).toLocaleDateString()}
                  </p>
                  <button
                    className="photo-delete-btn"
                    onClick={() => handleDelete(photo.id)}
                    title="Delete photo"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p>No photos uploaded yet.</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
