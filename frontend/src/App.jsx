import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:5000";

function App() {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState(
    "Hello! I'm your personal assistant. How can I help you?"
  );
  const [history, setHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);

  useEffect(() => {
    loadHistory();

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();

      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
        setError("");
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;

        setCommand(transcript);
        handleCommand(transcript);
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);

        if (event.error === "not-allowed") {
          setError("Microphone permission was denied.");
        } else if (event.error === "no-speech") {
          setError("I didn't hear anything.");
        } else {
          setError("Voice input failed. Please try again.");
        }

        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }

      window.speechSynthesis.cancel();
    };
  }, []);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/history`);

      if (!response.ok) {
        throw new Error("Failed to load command history.");
      }

      const data = await response.json();

      setHistory(Array.isArray(data) ? data : data.history || []);
    } catch (error) {
      console.error("History error:", error);
    }
  };

  const speak = (text) => {
    if (!("speechSynthesis" in window)) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const startListening = () => {
    if (!recognitionRef.current) {
      setError(
        "Voice recognition is not supported by this browser. Try Google Chrome."
      );
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      return;
    }

    setError("");

    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error("Could not start recognition:", error);
    }
  };

  const handleCommand = async (commandText = command) => {
    const text = commandText.trim();

    if (!text || isProcessing) {
      return;
    }

    setCommand(text);
    setError("");
    setIsProcessing(true);

    try {
      /*
       * Commands handled completely in the browser.
       * No Flask request is required for these.
       */
      const normalizedCommand = text.toLowerCase();

      if (
        normalizedCommand === "open google" ||
        normalizedCommand === "open google.com"
      ) {
        window.open("https://www.google.com", "_blank");

        const browserResponse = "Opening Google.";

        setResponse(browserResponse);
        speak(browserResponse);

        await loadHistory();

        return;
      }

      if (
        normalizedCommand === "open youtube" ||
        normalizedCommand === "open youtube.com"
      ) {
        window.open("https://www.youtube.com", "_blank");

        const browserResponse = "Opening YouTube.";

        setResponse(browserResponse);
        speak(browserResponse);

        await loadHistory();

        return;
      }

      /*
       * Backend command router.
       */
      const apiResponse = await fetch(`${API_BASE_URL}/command`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          command: text,
        }),
      });

      if (!apiResponse.ok) {
        throw new Error(`Server returned ${apiResponse.status}`);
      }

      const data = await apiResponse.json();
      console.log("Command response:", data);
      const assistantResponse =
        data.response ||
        data.message ||
        data.result ||
        "I couldn't understand that command.";

      setResponse(assistantResponse);

      speak(assistantResponse);

      await loadHistory();
    } catch (error) {
      console.error("Command error:", error);

      const errorMessage =
        "I couldn't connect to the assistant server. Make sure the Flask backend is running.";

      setResponse(errorMessage);
      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    await handleCommand();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleCommand();
    }
  };

  const clearInput = () => {
    setCommand("");
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  const repeatResponse = () => {
    if (response) {
      speak(response);
    }
  };

  const useHistoryCommand = (historyCommand) => {
    setCommand(historyCommand);
  };

  const formatDate = (dateValue) => {
    if (!dateValue) {
      return "";
    }

    try {
      const date = new Date(dateValue);

      if (Number.isNaN(date.getTime())) {
        return String(dateValue);
      }

      return date.toLocaleString();
    } catch {
      return String(dateValue);
    }
  };

  return (
    <div className="app">
      <div className="background-glow glow-one"></div>
      <div className="background-glow glow-two"></div>

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            AI
          </div>

          <div>
            <h1>Personal Assistant</h1>
            <p>AI-powered desktop assistant</p>
          </div>
        </div>

        <div className="connection-status">
          <span className="status-dot"></span>
          <span>Assistant Online</span>
        </div>
      </header>

      <main className="main-container">
        <section className="assistant-section">
          <div className="assistant-card">
            <div className="assistant-header">
              <div>
                <span className="eyebrow">PERSONAL ASSISTANT</span>
                <h2>How can I help you?</h2>
              </div>

              <div className="assistant-orb">
                <div className="orb-inner">
                  {isListening ? "●" : "AI"}
                </div>
              </div>
            </div>

            <div className="response-container">
              <div className="response-label">
                <span className="response-dot"></span>
                Assistant
              </div>

              <p className="response-text">{response}</p>

              <div className="response-actions">
                <button
                  className="small-button"
                  onClick={repeatResponse}
                  disabled={!response}
                >
                  🔊 Repeat
                </button>

                {isSpeaking && (
                  <button
                    className="small-button stop-button"
                    onClick={stopSpeaking}
                  >
                    ■ Stop
                  </button>
                )}
              </div>
            </div>

            <form className="command-form" onSubmit={handleSubmit}>
              <div className="input-wrapper">
                <textarea
                  value={command}
                  onChange={(event) => setCommand(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a command..."
                  rows="1"
                  disabled={isProcessing}
                />

                {command && (
                  <button
                    type="button"
                    className="clear-button"
                    onClick={clearInput}
                    aria-label="Clear command"
                  >
                    ×
                  </button>
                )}
              </div>

              <button
                type="button"
                className={`voice-button ${
                  isListening ? "listening" : ""
                }`}
                onClick={startListening}
                disabled={isProcessing}
                title={
                  isListening
                    ? "Stop listening"
                    : "Start voice recognition"
                }
              >
                {isListening ? "■" : "🎙"}
              </button>

              <button
                type="submit"
                className="send-button"
                disabled={!command.trim() || isProcessing}
              >
                {isProcessing ? "..." : "Send"}
              </button>
            </form>

            <div className="command-hint">
              <span>Press Enter to send</span>
              <span>•</span>
              <span>Use the microphone for voice input</span>
            </div>

            {error && <div className="error-message">{error}</div>}
          </div>

          <div className="quick-actions">
            <div className="section-title">
              <h3>Quick actions</h3>
              <span>Common commands</span>
            </div>

            <div className="quick-action-grid">
              <button
                onClick={() => handleCommand("what time is it")}
                disabled={isProcessing}
              >
                <span className="quick-icon">🕐</span>
                <span>
                  <strong>Time</strong>
                  <small>Current time</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("what is today's date")}
                disabled={isProcessing}
              >
                <span className="quick-icon">📅</span>
                <span>
                  <strong>Date</strong>
                  <small>Today's date</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("open downloads")}
                disabled={isProcessing}
              >
                <span className="quick-icon">📥</span>
                <span>
                  <strong>Downloads</strong>
                  <small>Open folder</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("open documents")}
                disabled={isProcessing}
              >
                <span className="quick-icon">📄</span>
                <span>
                  <strong>Documents</strong>
                  <small>Open folder</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("open pictures")}
                disabled={isProcessing}
              >
                <span className="quick-icon">🖼</span>
                <span>
                  <strong>Pictures</strong>
                  <small>Open folder</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("open terminal")}
                disabled={isProcessing}
              >
                <span className="quick-icon">⌨</span>
                <span>
                  <strong>Terminal</strong>
                  <small>Open terminal</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("open google")}
                disabled={isProcessing}
              >
                <span className="quick-icon">G</span>
                <span>
                  <strong>Google</strong>
                  <small>Open browser</small>
                </span>
              </button>

              <button
                onClick={() => handleCommand("open youtube")}
                disabled={isProcessing}
              >
                <span className="quick-icon">▶</span>
                <span>
                  <strong>YouTube</strong>
                  <small>Open browser</small>
                </span>
              </button>
            </div>
          </div>
        </section>

        <aside className="history-section">
          <div className="history-card">
            <div className="history-header">
              <div>
                <span className="eyebrow">ACTIVITY</span>
                <h2>Recent Commands</h2>
              </div>

              <button
                className="refresh-button"
                onClick={loadHistory}
                title="Refresh history"
              >
                ↻
              </button>
            </div>

            {history.length === 0 ? (
              <div className="empty-history">
                <div className="empty-icon">◷</div>
                <h3>No commands yet</h3>
                <p>
                  Your recent commands will appear here after you
                  interact with the assistant.
                </p>
              </div>
            ) : (
              <div className="history-list">
                {history.map((item, index) => {
                  console.log("History item:", item);
                  const historyCommand =
                    item.command_text ||
                    // item.command ||
                    // item.text ||
                    "";

                  const historyResponse =
                    item.response_text ||
                    // item.response ||
                    // item.message ||
                    "";

                  return (
                    <button
                      className="history-item"
                      key={item._id || item.id || index}
                      onClick={() =>
                        useHistoryCommand(historyCommand)
                      }
                    >
                      <div className="history-command">
                        <span className="history-arrow">›</span>
                        <span>{historyCommand}</span>
                      </div>

                      {historyResponse && (
                        <div className="history-response">
                          {historyResponse}
                        </div>
                      )}

                      {item.created_at && (
                        <div className="history-time">
                          {formatDate(item.created_at)}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </aside>
      </main>

      <footer className="footer">
        <span>Personal Assistant</span>
        <span>React + Flask + MongoDB</span>
      </footer>
    </div>
  );
}

export default App;