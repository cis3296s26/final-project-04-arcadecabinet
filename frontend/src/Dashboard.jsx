import { useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function Dashboard({ game }) {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const startTestServer = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/test/start`, {
        method: "POST",
      });
      const data = await response.json();

      if (data.success) {
        setMessage(
          `✓ Minecraft server ${data.server.join_code} started on port ${data.server.port}`,
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

  return (
    <div className="App">
      <header>
        <h1>🎮 Arcade Cabinet</h1>
        <p>Proof of Concept - Docker Integration Test</p>
      </header>

      <main>
        <div className="controls">
          <button
            onClick={startTestServer}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? "Starting..." : "Start Minecraft Server"}
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
              No servers running. Click "Start Minecraft Server" to begin.
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
        {/*
        <div className="info">
          <h3>What This Proves:</h3>
          <ul>
            <li>✓ Backend can start Docker containers programmatically</li>
            <li>✓ Frontend can communicate with backend API</li>
            <li>✓ Join codes are generated and tracked</li>
            <li>✓ Containers are assigned random ports</li>
            <li>✓ Full tech stack works together</li>
          </ul>
        </div>
        */}
      </main>
    </div>
  );
}

export default Dashboard;
