"use client";

import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

type VoiceChatProps = {
  propertyId: number | null;
};

export default function VoiceChat({ propertyId }: VoiceChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // A conversation is tied to one property. Clear old messages when a new
  // search selects a different property so its facts never leak into Q&A.
  useEffect(() => {
    setMessages([]);
    setQuestion("");
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  }, [propertyId]);

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
  };

  // Play AI Briefing using browser TTS (FREE!)
  const playBriefing = async () => {
    if (!propertyId) {
      alert("Please search for a property first!");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/voice/properties/${propertyId}/briefing`
      );

      if (!response.ok) throw new Error("Failed to generate briefing");

      const data = await response.json();
      const briefingText = data.briefing;

      // Use browser's TTS (FREE!)
      const utterance = new SpeechSynthesisUtterance(briefingText);
      utterance.rate = 0.9;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);

      // Add to conversation
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: briefingText,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to play briefing");
    } finally {
      setLoading(false);
    }
  };

  // Ask question via text
  const askQuestion = async () => {
    if (!question.trim() || !propertyId) return;

    const userMessage: Message = {
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/voice/properties/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          property_id: propertyId,
          question: question,
          conversation_history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) throw new Error("Failed to get answer");

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          timestamp: new Date(),
        },
      ]);

      // Speak answer using browser TTS (FREE!)
      const utterance = new SpeechSynthesisUtterance(data.answer);
      utterance.rate = 0.9;
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to ask question");
    } finally {
      setLoading(false);
    }
  };

  // Start voice recording using browser Speech Recognition (FREE!)
  const startRecording = () => {
    if (!propertyId) {
      alert("Please search for a property first!");
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition not supported. Use Chrome or Edge.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => setIsRecording(true);

    recognition.onresult = async (event: any) => {
      const transcript = event.results[0][0].transcript;
      setIsRecording(false);

      // Add user message
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: transcript,
          timestamp: new Date(),
        },
      ]);

      // Get AI response
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/voice/properties/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            property_id: propertyId,
            question: transcript,
            conversation_history: messages.map((m) => ({
              role: m.role,
              content: m.content,
            })),
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: data.answer,
              timestamp: new Date(),
            },
          ]);

          // Speak answer
          const utterance = new SpeechSynthesisUtterance(data.answer);
          utterance.rate = 0.9;
          window.speechSynthesis.speak(utterance);
        }
      } catch (err) {
        alert("Failed to get AI response");
      } finally {
        setLoading(false);
      }
    };

    recognition.onerror = () => {
      setIsRecording(false);
      alert("Speech recognition error. Try again.");
    };

    recognition.onend = () => setIsRecording(false);

    recognition.start();
  };

  return (
    <div
      style={{
        borderRadius: 28,
        border: "1px solid rgba(255,255,255,0.10)",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04))",
        boxShadow: "0 24px 80px rgba(0,0,0,0.35)",
        backdropFilter: "blur(18px)",
        padding: 22,
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 12px",
            borderRadius: 999,
            background: "rgba(34,211,238,0.10)",
            border: "1px solid rgba(34,211,238,0.18)",
            color: "#a5f3fc",
            fontSize: 11,
            fontWeight: 700,
            marginBottom: 12,
          }}
        >
          100% FREE - Browser-based voice
        </div>
        <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: "-0.02em" }}>
          AI Assistant & Voice Chat
        </div>
        <div
          style={{
            marginTop: 6,
            fontSize: 13,
            color: "rgba(255,255,255,0.55)",
            lineHeight: 1.6,
          }}
        >
          Ask questions via text or voice using Google Gemini (free!)
        </div>
      </div>

      {/* Voice Controls */}
      <div
        style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}
      >
        <button
          onClick={playBriefing}
          disabled={!propertyId || loading}
          style={{
            padding: "12px 18px",
            borderRadius: 14,
            background: propertyId
              ? "rgba(34,211,238,0.15)"
              : "rgba(255,255,255,0.05)",
            border: "1px solid rgba(34,211,238,0.30)",
            color: propertyId ? "#a5f3fc" : "rgba(255,255,255,0.3)",
            fontWeight: 700,
            fontSize: 14,
            cursor: propertyId && !loading ? "pointer" : "not-allowed",
          }}
        >
          {loading
            ? "Loading..."
            : isSpeaking
            ? "Restart Briefing"
            : "Listen to AI Briefing"}
        </button>

        <button
          onClick={stopSpeaking}
          disabled={!isSpeaking}
          style={{
            padding: "12px 18px",
            borderRadius: 14,
            background: isSpeaking
              ? "rgba(239,68,68,0.18)"
              : "rgba(255,255,255,0.05)",
            border: "1px solid rgba(239,68,68,0.35)",
            color: isSpeaking ? "#fca5a5" : "rgba(255,255,255,0.3)",
            fontWeight: 700,
            fontSize: 14,
            cursor: isSpeaking ? "pointer" : "not-allowed",
          }}
        >
          Stop Briefing
        </button>

        <button
          onClick={startRecording}
          disabled={!propertyId || loading || isRecording}
          style={{
            padding: "12px 18px",
            borderRadius: 14,
            background: isRecording
              ? "rgba(239,68,68,0.20)"
              : propertyId
              ? "rgba(139,92,246,0.15)"
              : "rgba(255,255,255,0.05)",
            border: isRecording
              ? "1px solid rgba(239,68,68,0.40)"
              : "1px solid rgba(139,92,246,0.30)",
            color: isRecording
              ? "#fca5a5"
              : propertyId
              ? "#c4b5fd"
              : "rgba(255,255,255,0.3)",
            fontWeight: 700,
            fontSize: 14,
            cursor: propertyId && !loading ? "pointer" : "not-allowed",
          }}
        >
          {isRecording ? "Listening..." : "Ask via Voice"}
        </button>
      </div>

      {/* Chat History */}
      <div
        style={{
          marginBottom: 16,
          maxHeight: 400,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              padding: 20,
              textAlign: "center",
              color: "rgba(255,255,255,0.4)",
              fontSize: 14,
            }}
          >
            No conversation yet. Ask a question to get started!
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={{
                  maxWidth: "75%",
                  padding: "12px 16px",
                  borderRadius: 16,
                  background:
                    msg.role === "user"
                      ? "rgba(34,211,238,0.15)"
                      : "rgba(139,92,246,0.15)",
                  border:
                    msg.role === "user"
                      ? "1px solid rgba(34,211,238,0.25)"
                      : "1px solid rgba(139,92,246,0.25)",
                  color: "#fff",
                  fontSize: 14,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: 4, fontSize: 12 }}>
                  {msg.role === "user" ? "You" : "AI Assistant (Gemini)"}
                </div>
                {msg.content}
                <div
                  style={{
                    marginTop: 6,
                    fontSize: 11,
                    color: "rgba(255,255,255,0.4)",
                  }}
                >
                  {msg.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Text Input */}
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && askQuestion()}
          placeholder={
            propertyId
              ? "Ask a question about this property..."
              : "Search for a property first"
          }
          disabled={!propertyId || loading}
          style={{
            flex: 1,
            padding: "12px 16px",
            borderRadius: 14,
            border: "1px solid rgba(255,255,255,0.10)",
            background: "rgba(0,0,0,0.30)",
            color: "#fff",
            outline: "none",
            fontSize: 14,
          }}
        />
        <button
          onClick={askQuestion}
          disabled={!propertyId || !question.trim() || loading}
          style={{
            padding: "12px 20px",
            borderRadius: 14,
            background:
              propertyId && question.trim() && !loading
                ? "#fff"
                : "rgba(255,255,255,0.15)",
            color:
              propertyId && question.trim() && !loading
                ? "#030712"
                : "rgba(255,255,255,0.5)",
            border: 0,
            fontWeight: 800,
            fontSize: 14,
            cursor:
              propertyId && question.trim() && !loading
                ? "pointer"
                : "not-allowed",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
