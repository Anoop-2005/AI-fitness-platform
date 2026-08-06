// frontend/src/pages/ProgressPhotos.jsx
import React, { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";

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
  const [comparePhotos, setComparePhotos] = useState([]);
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
    await loadPhotos(); // Refresh gallery
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
      // Convert to base64
      const base64 = await fileToBase64(file);

      // Run MediaPipe analysis
      setAnalyzing(true);
      const analysis = await analyzePosture(base64, selectedView);
      setAnalysisResult(analysis);

      // Upload to backend
      await api.uploadPhoto(selectedView, base64);

      // Reload photos
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
  // Helper to convert base64 data URL into an HTMLImageElement for WebGL compatibility
  function loadImageElement(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => resolve(img);
      img.onerror = (err) => reject(new Error("Failed to load image for analysis"));
      img.src = dataUrl;
    });
  }

  async function analyzePosture(imageData, viewType) {
  try {
    const vision = await import("@mediapipe/tasks-vision");
    const { PoseLandmarker, FilesetResolver } = vision;

    const filesetResolver = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.x/wasm"
    );

    // Use CPU delegate - most reliable
    const pose = await PoseLandmarker.createFromOptions(filesetResolver, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        delegate: "CPU",
      },
      runningMode: "IMAGE",
      numPoses: 1,
    });

    // Load image properly
    const img = await loadImage(imageData);
    
    // Detect pose
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

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Failed to load image"));
    img.src = src;
  });
}

  async function initializePoseLandmarker() {
    // Lazy load MediaPipe Tasks Vision
    const vision = await import("@mediapipe/tasks-vision");
    const { PoseLandmarker, FilesetResolver } = vision;

    const filesetResolver = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.x/wasm"
    );

    return await PoseLandmarker.createFromOptions(filesetResolver, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        delegate: "GPU",
      },
      runningMode: "IMAGE",
      numPoses: 1,
    });
  }

  function calculatePostureScore(landmarks, viewType) {
    // Simple heuristic-based posture scoring
    const scores = {
      symmetry: calculateSymmetry(landmarks, viewType),
      alignment: calculateAlignment(landmarks, viewType),
      balance: calculateBalance(landmarks, viewType),
    };
    return Math.round((scores.symmetry + scores.alignment + scores.balance) / 3);
  }

  function calculateSymmetry(landmarks, viewType) {
    if (viewType === "front") {
      const leftShoulder = landmarks[11];
      const rightShoulder = landmarks[12];
      const leftHip = landmarks[23];
      const rightHip = landmarks[24];
      const shoulderDiff = Math.abs(leftShoulder.y - rightShoulder.y);
      const hipDiff = Math.abs(leftHip.y - rightHip.y);
      return Math.max(0, 100 - (shoulderDiff + hipDiff) * 500);
    }
    return 75; // Default for side/back
  }

  function calculateAlignment(landmarks, viewType) {
    if (viewType === "side") {
      const ear = landmarks[7];
      const shoulder = landmarks[11];
      const hip = landmarks[23];
      const ankle = landmarks[27];
      const verticalDeviation = Math.abs(ear.x - ankle.x) + Math.abs(shoulder.x - hip.x);
      return Math.max(0, 100 - verticalDeviation * 200);
    }
    return 75;
  }

  function calculateBalance(landmarks, viewType) {
    const leftAnkle = landmarks[27];
    const rightAnkle = landmarks[28];
    const centerX = (leftAnkle.x + rightAnkle.x) / 2;
    const nose = landmarks[0];
    return Math.max(0, 100 - Math.abs(nose.x - centerX) * 300);
  }

  function generateObservations(landmarks, viewType) {
    const observations = [];
    const score = calculatePostureScore(landmarks, viewType);

    if (score >= 85) {
      observations.push("✅ Great posture alignment!");
    } else if (score >= 70) {
      observations.push("👍 Good posture with minor areas for improvement.");
    } else {
      observations.push("⚠️ Posture could benefit from targeted exercises.");
    }

    if (viewType === "front") {
      const leftShoulder = landmarks[11];
      const rightShoulder = landmarks[12];
      if (Math.abs(leftShoulder.y - rightShoulder.y) > 0.03) {
        observations.push("📐 Shoulders appear uneven - consider unilateral shoulder work.");
      }
    }

    if (viewType === "side") {
      const ear = landmarks[7];
      const shoulder = landmarks[11];
      if (ear.x < shoulder.x - 0.05) {
        observations.push("🦒 Forward head posture detected - try chin tucks and neck stretches.");
      }
    }

    return observations;
  }

  function estimateMeasurements(landmarks) {
    // Rough proportional estimates based on pose landmarks
    const nose = landmarks[0];
    const leftAnkle = landmarks[27];
    const heightPixels = Math.abs(nose.y - leftAnkle.y);

    return {
      estimatedHeightPx: Math.round(heightPixels * 100),
      shoulderWidth: Math.round(Math.abs(landmarks[11].x - landmarks[12].x) * 100),
      hipWidth: Math.round(Math.abs(landmarks[23].x - landmarks[24].x) * 100),
    };
  }

  function openCompare(viewType, photo) {
    setCompareMode(true);
    setComparePhotos((prev) => {
      const existing = prev.filter((p) => p.view_type !== viewType);
      return [...existing, photo];
    });
  }

  if (loading) return <div className="page">Loading...</div>;

  return (
    <div className="page page-wide">
      <div className="flex-between">
        <h2>📸 Progress Photos</h2>
        <button className="btn btn-secondary btn-small" onClick={() => setCompareMode(!compareMode)}>
          {compareMode ? "Exit Compare" : "🔍 Compare Photos"}
        </button>
      </div>

      {/* Upload Section */}
      <div className="card">
        <h3 className="mb-12">Upload New Photo</h3>
        <div className="field-row mb-12">
          {VIEW_TYPES.map((vt) => (
            <label key={vt.key} style={{ display: "flex", alignItems: "center", gap: 8 }}>
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
        {uploading && <p className="text-small mt-12">{analyzing ? "Analyzing posture..." : "Uploading..."}</p>}
      </div>

      {/* Analysis Result */}
      {analysisResult && (
        <div className="card">
          <h3 className="mb-12">🤖 AI Posture Analysis</h3>
          {analysisResult.detected ? (
            <>
              <div className="stat-value mb-12">Posture Score: {analysisResult.postureScore}/100</div>
              <ul style={{ paddingLeft: 20 }}>
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
                      style={{ maxWidth: "100%", borderRadius: 8, cursor: "pointer" }}
                      onClick={() => openCompare(vt.key, latest)}
                    />
                  ) : (
                    <div className="no-image-msg">No {vt.label} photo yet</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Photo Gallery by View Type */}
      {/* Photo Gallery by View Type */}
        {VIEW_TYPES.map((vt) => (
        <div key={vt.key} className="card">
            <h3 className="mb-12">{vt.icon} {vt.label} View</h3>
            {photos[vt.key]?.length > 0 ? (
            <div style={{ display: "flex", gap: 12, overflowX: "auto", padding: "8px 0" }}>
            {photos[vt.key].map((photo) => (
                <div key={photo.id} style={{ minWidth: 150, textAlign: "center", position: "relative" }}>
                <img
                src={photo.photo_url}
                alt={`${vt.label} ${photo.uploaded_at}`}
                style={{ width: 150, height: 200, objectFit: "cover", borderRadius: 8 }}
                />
                <p className="text-mini text-dim mt-4">
                {new Date(photo.uploaded_at).toLocaleDateString()}
                </p>
                {/* Delete Button */}
                <button
                onClick={() => handleDelete(photo.id)}
                style={{
                    position: "absolute",
                    top: 4,
                    right: 4,
                    background: "rgba(179, 38, 30, 0.9)",
                    color: "#fff",
                    border: "none",
                    borderRadius: "50%",
                    width: 24,
                    height: 24,
                    cursor: "pointer",
                    fontSize: "0.75rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    }}
                    title="Delete photo"
                    >
                    ✕
                    </button>
                </div>
                ))}
            </div>
            ) : (
            <p className="text-small text-dim">No photos uploaded yet.</p>
            )}
        </div>
        ))}
    </div>
  );
}