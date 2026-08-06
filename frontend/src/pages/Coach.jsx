import React, { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";

const QUICK_PROMPTS = [
  { label: "💪 Motivate me", prompt: "Give me some motivation for today's workout!" },
  { label: "🔄 Suggest rest", prompt: "Am I due for a rest day? Check my recent activity." },
  { label: "📋 Explain my plan", prompt: "Explain my current workout plan and why these exercises were chosen." },
  { label: "🥗 Nutrition tips", prompt: "Give me nutrition tips based on my goals." },
  { label: "⚠️ Overtraining check", prompt: "Check if I'm showing any signs of overtraining." },
  { label: "🏋️ Form tips", prompt: "Give me general workout form tips for my experience level." },
];

export default function Coach() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm your AI fitness coach. I can help with workout questions, form corrections, exercise alternatives, motivation, and adjusting your plan based on progress. What can I help you with today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text) {
    const message = text || input.trim();
    if (!message || loading) return;

    const newMessages = [...messages, { role: "user", content: message }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const { reply } = await api.coachChat(message);
      setMessages([...newMessages, { role: "assistant", content: reply }]);
    } catch (err) {
      setMessages([...newMessages, { role: "assistant", content: `Sorry, I couldn't process that: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="page page-wide">
      <div className="flex-between">
        <h2>🤖 AI Coach</h2>
        <span className="text-small text-dim">Your virtual personal trainer</span>
      </div>

      {/* Quick Prompts */}
      <div className="equipment-grid mb-16">
        {QUICK_PROMPTS.map((qp) => (
          <button
            key={qp.label}
            className="btn btn-secondary equipment-btn"
            onClick={() => sendMessage(qp.prompt)}
            disabled={loading}
          >
            {qp.label}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="card" style={{ minHeight: 400, maxHeight: 500, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "80%",
              padding: "10px 14px",
              borderRadius: 12,
              background: msg.role === "user" ? "var(--primary)" : "var(--surface)",
              color: msg.role === "user" ? "#fff" : "var(--text)",
              border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
            }}
          >
            <div style={{ fontSize: "0.85rem", whiteSpace: "pre-wrap" }}>{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: "flex-start", padding: "10px 14px", borderRadius: 12, background: "var(--surface)", border: "1px solid var(--border)" }}>
            <span style={{ fontSize: "0.85rem" }}>Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-between mt-16" style={{ gap: 12 }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me anything about fitness, nutrition, or your plan..."
          rows={2}
          style={{ flex: 1, padding: "10px 14px", borderRadius: 8, border: "1px solid var(--border)", resize: "none", fontSize: "0.9rem" }}
        />
        <button className="btn" onClick={() => sendMessage()} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}