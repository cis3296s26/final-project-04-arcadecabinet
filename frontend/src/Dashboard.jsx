import { useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function Dashboard({ game, onBack }) {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const displayName = game
    ? game.charAt(0).toUpperCase() + game.slice(1)
    : "Game";

  const startServer = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/test/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ game: game }),
      });
      const data = await response.json();

      if (data.success) {
        setMessage(
          `✓ ${displayName} server ${data.server.join_code} started on port ${data.server.port}`,
        );
        fetchServers();
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const stopAllServers = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/test/stop`, {
        method: "POST",
      });
      const data = await response.json();

      if (data.success) {
        setMessage(`✓ Stopped ${data.stopped.length} servers`);
        setServers([]);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchServers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/servers`);
      const data = await response.json();
      setServers(data.servers);
    } catch (error) {
      console.error("Error fetching servers:", error);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  return (
    <div className="dashboard-wrapper">
      <header className="dashboard-header">
        <button onClick={onBack} className="btn-secondary back-btn">
          ← Back to Menu
        </button>
        <h1>Arcade Cabinet</h1>
      </header>

      <div className="dashboard-panel">
        <div className="controls">
          <button
            onClick={startServer}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? "Starting..." : `Start ${displayName} Server`}
          </button>

          <button
            onClick={stopAllServers}
            disabled={loading || servers.length === 0}
            className="btn-danger"
          >
            Stop All Servers
          </button>

          <button onClick={fetchServers} className="btn-secondary">
            Refresh List
          </button>
        </div>

        {message && (
          <div
            className={`message ${message.startsWith("✓") ? "success" : "error"}`}
          >
            {message}
          </div>
        )}

        <div className="servers">
          <h2>Active Servers ({servers.length})</h2>
          {servers.length === 0 ? (
            <p className="empty">
              No servers running. Click "Start {displayName} Server" to begin.
            </p>
          ) : (
            <ul>
              {servers.map((server) => (
                <li key={server.join_code} className="server-card">
                  <span className="join-code">{server.join_code}</span>
                  <span className="status">{server.status}</span>
                  <span className="port">Port: {server.port}</span>
                  <span className="container-id">{server.container_id}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
