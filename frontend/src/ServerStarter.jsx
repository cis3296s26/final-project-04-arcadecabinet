import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function ServerStarter({ game, onBack }) {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [playitStatus, setPlayitStatus] = useState(null);

  // Server configuration
  const [serverName, setServerName] = useState(
    game === "terraria" ? "World-Server" : "My Server",
  );
  const [maxPlayers, setMaxPlayers] = useState(game === "terraria" ? 16 : 10);
  const [difficulty, setDifficulty] = useState("normal");
  const [gameMode, setGameMode] = useState("survival");

  // Fetch Playit status on mount
  useEffect(() => {
    fetchPlayitStatus();
    fetchServers();
    const interval = setInterval(fetchServers, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchPlayitStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/playit/status`);
      const data = await response.json();
      setPlayitStatus(data);
    } catch (error) {
      console.error("Error fetching Playit status:", error);
    }
  };

  const startServer = async () => {
    setLoading(true);
    setMessage("");

    // Game specific
    const endpoint =
      game === "terraria"
        ? `${API_URL}/api/servers/start/terraria`
        : `${API_URL}/api/servers/start`;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          server_name: serverName,
          max_players: maxPlayers,
          difficulty: difficulty,
          game_mode: gameMode,
        }),
      });
      const data = await response.json();

      if (data.success) {
        setMessage(`✓ Server "${serverName}" created! ${data.message || ""}`);
        fetchServers();
      } else {
        setMessage(`✗ Error: ${data.detail || "Failed to create server"}`);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const stopServer = async (joinCode) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/servers/${joinCode}/stop`, {
        method: "POST",
      });
      const data = await response.json();

      if (data.success) {
        setMessage(`✓ ${data.message}`);
        fetchServers();
      } else {
        setMessage(`✗ Error: ${data.detail || "Failed to stop server"}`);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const restartServer = async (joinCode) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/servers/${joinCode}/restart`,
        {
          method: "POST",
        },
      );
      const data = await response.json();

      if (data.success) {
        setMessage(`✓ ${data.message}`);
        fetchServers();
      } else {
        setMessage(`✗ Error: ${data.detail || "Failed to restart server"}`);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteServer = async (joinCode, deleteWorld = false) => {
    const confirmed = window.confirm(
      deleteWorld
        ? `Delete server AND world data? This cannot be undone!`
        : `Delete server? (World data will be preserved)`,
    );

    if (!confirmed) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/servers/${joinCode}?delete_world=${deleteWorld}`,
        { method: "DELETE" },
      );
      const data = await response.json();

      if (data.success) {
        setMessage(`✓ ${data.message}`);
        fetchServers();
      } else {
        setMessage(`✗ Error: ${data.detail || "Failed to delete server"}`);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const setTunnelUrl = async (joinCode, url) => {
    if (!url || !url.trim()) return;

    try {
      const response = await fetch(
        `${API_URL}/api/servers/${joinCode}/tunnel`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: url.trim() }),
        },
      );
      const data = await response.json();

      if (data.success) {
        setMessage(`✓ Tunnel URL updated!`);
        fetchServers();
      } else {
        setMessage(`✗ Error: ${data.detail || "Failed to set tunnel URL"}`);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`);
    }
  };

  const fetchServers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/servers`);
      const data = await response.json();
      // Filter list to only show current game type
      const filtered = data.servers.filter(
        (s) => s.game_type === (game || "minecraft"),
      );
      setServers(filtered);
    } catch (error) {
      console.error("Error fetching servers:", error);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setMessage(`✓ Copied "${text}" to clipboard!`);
    setTimeout(() => setMessage(""), 3000);
  };

  const gameLabel = game ? String(game).toUpperCase() : "MINECRAFT";

  return (
    <div className="App">
      <header>
        <h1>🎮 Arcade Cabinet</h1>
        <p>{gameLabel} Server Manager - Tunnel-First</p>
      </header>

      <main>
        <div className="servers-header" style={{ marginBottom: 20 }}>
          <h2 style={{ margin: 0 }}>Server Starter</h2>
          <button onClick={onBack} className="btn-secondary btn-small">
            ← Back to Games
          </button>
        </div>

        {/* Playit Status Banner */}
        {playitStatus && (
          <div
            className={`playit-status ${playitStatus.mode === "automatic" ? "auto" : "manual"}`}
          >
            <h3>🌐 Tunneling Status</h3>
            {playitStatus.mode === "automatic" ? (
              <div>
                <p>
                  ✓ <strong>Automatic mode</strong> - Tunnels created
                  automatically
                </p>
                <p>Active tunnels: {playitStatus.tunnels_active}</p>
              </div>
            ) : (
              <div>
                <p>
                  ⚠️ <strong>Manual mode</strong> - Paste Playit URLs manually
                </p>
                <details>
                  <summary>How to enable automatic tunneling</summary>
                  <ol>
                    <li>
                      Install Playit: <code>playit.gg</code>
                    </li>
                    <li>Run Playit sidecar (see README)</li>
                    <li>Tunnels will auto-create</li>
                  </ol>
                </details>
              </div>
            )}
          </div>
        )}

        {/* Server Configuration */}
        <div className="config-section">
          <h3>⚙️ Server Configuration</h3>
          <div className="config-grid">
            <div className="config-item">
              <label>Server Name:</label>
              <input
                type="text"
                value={serverName}
                onChange={(e) => setServerName(e.target.value)}
              />
            </div>

            <div className="config-item">
              <label>Max Players:</label>
              <input
                type="number"
                value={maxPlayers}
                onChange={(e) => setMaxPlayers(parseInt(e.target.value))}
                min="1"
                max="100"
              />
            </div>

            <div className="config-item">
              <label>Difficulty:</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                {/* TERRARIA vs MINECRAFT DIFFICULTIES */}
                {game === "terraria" ? (
                  <>
                    <option value="normal">Normal</option>
                    <option value="expert">Expert</option>
                  </>
                ) : (
                  <>
                    <option value="peaceful">Peaceful</option>
                    <option value="easy">Easy</option>
                    <option value="normal">Normal</option>
                    <option value="hard">Hard</option>
                  </>
                )}
              </select>
            </div>

            {/* MINECRAFT ONLY SETTINGS */}
            {game !== "terraria" && (
              <div className="config-item">
                <label>Game Mode:</label>
                <select
                  value={gameMode}
                  onChange={(e) => setGameMode(e.target.value)}
                >
                  <option value="survival">Survival</option>
                  <option value="creative">Creative</option>
                  <option value="adventure">Adventure</option>
                </select>
              </div>
            )}
          </div>

          <button
            onClick={startServer}
            disabled={loading}
            className="btn-primary btn-large"
          >
            {loading ? "Starting Server..." : "🚀 Start New Server"}
          </button>
        </div>

        {/* Status Message */}
        {message && (
          <div
            className={`message ${message.startsWith("✓") ? "success" : "error"}`}
          >
            {message}
          </div>
        )}

        {/* Active Servers */}
        <div className="servers">
          <div className="servers-header">
            <h2>Active Servers ({servers.length})</h2>
            <button onClick={fetchServers} className="btn-secondary btn-small">
              🔄 Refresh
            </button>
          </div>

          {servers.length === 0 ? (
            <div className="empty">
              <p>No {gameLabel} servers running.</p>
              <p>Configure settings above and click "Start New Server"</p>
            </div>
          ) : (
            <div className="server-list">
              {servers.map((server) => (
                <div key={server.join_code} className="server-card">
                  <div className="server-header">
                    <div>
                      <h3>{server.server_name}</h3>
                      <span className="join-code">{server.join_code}</span>
                      <span className={`status ${server.status}`}>
                        {server.status}
                      </span>
                    </div>
                  </div>

                  {/* PRIMARY JOIN ADDRESS */}
                  <div className="join-section primary">
                    <h4>🌐 Join Address</h4>
                    {server.addresses.primary === "pending" ? (
                      <div className="pending-tunnel">
                        <p>⏳ Tunnel creating... (refresh in a few seconds)</p>
                        <p className="help-text">
                          Or paste your Playit URL below
                        </p>
                      </div>
                    ) : server.addresses.primary === "offline" ? (
                      <div className="offline">
                        <p>🔴 Server offline</p>
                      </div>
                    ) : (
                      <div className="copy-field large">
                        <code>{server.addresses.primary}</code>
                        <button
                          className="btn-copy"
                          onClick={() =>
                            copyToClipboard(server.addresses.primary)
                          }
                        >
                          📋 Copy
                        </button>
                      </div>
                    )}

                    {/* Local mapping (QoL) */}
                    <div className="local-map">
                      <div className="local-map-row">
                        <strong>Local port (for Playit):</strong>
                        <div className="copy-field compact on-dark">
                          <code>{server.port}</code>
                          <button
                            className="btn-copy small"
                            onClick={() => copyToClipboard(String(server.port))}
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                      <div className="local-map-row">
                        <strong>Localhost (this computer):</strong>
                        <div className="copy-field compact on-dark">
                          <code>
                            {server.addresses?.local ||
                              `localhost:${server.port}`}
                          </code>
                          <button
                            className="btn-copy small"
                            onClick={() =>
                              copyToClipboard(
                                server.addresses?.local ||
                                  `localhost:${server.port}`,
                              )
                            }
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Manual tunnel URL input (fallback) */}
                    {(server.addresses.primary === "pending" ||
                      playitStatus?.mode === "manual") && (
                      <details className="manual-tunnel">
                        <summary>Paste Playit URL manually</summary>
                        <div className="tunnel-input">
                          <input
                            type="text"
                            placeholder="abc123.playit.gg:12345"
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                setTunnelUrl(server.join_code, e.target.value);
                                e.target.value = "";
                              }
                            }}
                          />
                        </div>
                      </details>
                    )}
                  </div>

                  {/* ADVANCED: LOCAL ONLY */}
                  <details className="advanced-section">
                    <summary>⚙️ Advanced (Local Only)</summary>
                    <div className="detail-row">
                      <strong>Localhost:</strong>
                      <div className="copy-field">
                        <code>{server.addresses.local}</code>
                        <button
                          className="btn-copy small"
                          onClick={() =>
                            copyToClipboard(server.addresses.local)
                          }
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                    <div className="detail-row">
                      <strong>Container:</strong>
                      <code>{server.container_id}</code>
                    </div>
                    <div className="detail-row">
                      <strong>Volume:</strong>
                      <code>{server.volume_name}</code>
                    </div>
                  </details>

                  {/* Server Actions */}
                  <div className="server-actions">
                    {server.status === "running" && (
                      <>
                        <button
                          onClick={() => stopServer(server.join_code)}
                          disabled={loading}
                          className="btn-warning"
                        >
                          ⏸ Stop
                        </button>
                        <button
                          onClick={() => restartServer(server.join_code)}
                          disabled={loading}
                          className="btn-secondary"
                        >
                          🔄 Restart
                        </button>
                      </>
                    )}

                    {server.status === "stopped" && (
                      <button
                        onClick={() => restartServer(server.join_code)}
                        disabled={loading}
                        className="btn-primary"
                      >
                        ▶️ Resume
                      </button>
                    )}

                    <button
                      onClick={() => deleteServer(server.join_code, false)}
                      disabled={loading}
                      className="btn-danger"
                    >
                      🗑 Delete Container
                    </button>

                    <button
                      onClick={() => deleteServer(server.join_code, true)}
                      disabled={loading}
                      className="btn-danger-alt"
                    >
                      💥 Delete World
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="help-section">
          <h3>📖 How It Works</h3>
          <div className="help-grid">
            <div className="help-card">
              <h4>🌐 Playing with Anyone</h4>
              <ol>
                <li>Start a server above</li>
                <li>Copy the join address</li>
                <li>Share with friends (works anywhere)</li>
                <li>They paste it in game</li>
              </ol>
            </div>

            <div className="help-card">
              <h4>🏠 Playing Solo</h4>
              <ol>
                <li>Start a server</li>
                <li>Copy localhost address</li>
                <li>Use in game on this computer</li>
              </ol>
            </div>

            <div className="help-card">
              <h4>💾 World Persistence</h4>
              <p>
                ✅ Worlds auto-save
                <br />
                ✅ Stop/Restart keeps world
                <br />
                ✅ "Delete Container" keeps world
                <br />❌ "Delete World" = permanent
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ServerStarter;
