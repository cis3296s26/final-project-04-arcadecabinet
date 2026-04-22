import { useState, useEffect } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [servers, setServers] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [networkInfo, setNetworkInfo] = useState(null)
  
  // Server configuration
  const [serverName, setServerName] = useState('My Server')
  const [maxPlayers, setMaxPlayers] = useState(10)
  const [difficulty, setDifficulty] = useState('normal')
  const [gameMode, setGameMode] = useState('survival')

  // Fetch network info on mount
  useEffect(() => {
    fetchNetworkInfo()
  }, [])

  const fetchNetworkInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/network/info`)
      const data = await response.json()
      setNetworkInfo(data)
    } catch (error) {
      console.error('Error fetching network info:', error)
    }
  }

  const startServer = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_URL}/api/servers/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          server_name: serverName,
          max_players: maxPlayers,
          difficulty: difficulty,
          game_mode: gameMode
        })
      })
      const data = await response.json()
      
      if (data.success) {
        setMessage(`✓ Server "${serverName}" (${data.server.join_code}) started! World will persist.`)
        fetchServers()
      } else {
        setMessage(`✗ Failed to start server`)
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const stopServer = async (joinCode) => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_URL}/api/servers/${joinCode}/stop`, {
        method: 'POST'
      })
      const data = await response.json()
      
      if (data.success) {
        setMessage(`✓ Server stopped. World data saved!`)
        fetchServers()
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const restartServer = async (joinCode) => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_URL}/api/servers/${joinCode}/restart`, {
        method: 'POST'
      })
      const data = await response.json()
      
      if (data.success) {
        setMessage(`✓ Server restarted with same world!`)
        fetchServers()
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const deleteServer = async (joinCode, deleteWorld = false) => {
    const confirmed = window.confirm(
      deleteWorld 
        ? `Delete server AND world data permanently? This cannot be undone!`
        : `Delete server container? (World data will be preserved)`
    )
    
    if (!confirmed) return

    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(
        `${API_URL}/api/servers/${joinCode}?delete_world=${deleteWorld}`,
        { method: 'DELETE' }
      )
      const data = await response.json()
      
      if (data.success) {
        setMessage(`✓ ${data.message}`)
        fetchServers()
      }
    } catch (error) {
      setMessage(`✗ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const fetchServers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/servers`)
      const data = await response.json()
      setServers(data.servers)
    } catch (error) {
      console.error('Error fetching servers:', error)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setMessage(`✓ Copied "${text}" to clipboard!`)
    setTimeout(() => setMessage(''), 3000)
  }

  return (
    <div className="App">
      <header>
        <h1>🎮 Arcade Cabinet</h1>
        <p>Minecraft Server Manager - POC v0.2</p>
      </header>

      <main>
        {/* Network Info Banner */}
        {networkInfo && (
          <div className="network-info">
            <h3>🌐 Network Information</h3>
            <div className="network-details">
              <div>
                <strong>Local IP:</strong> 
                <code>{networkInfo.local_ip}</code>
                <button 
                  className="btn-copy"
                  onClick={() => copyToClipboard(networkInfo.local_ip)}
                >
                  Copy
                </button>
              </div>
              <p className="help-text">
                Share "<strong>{networkInfo.local_ip}:PORT</strong>" with friends on the same WiFi network
              </p>
            </div>
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
                placeholder="My Awesome Server"
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
                <option value="peaceful">Peaceful</option>
                <option value="easy">Easy</option>
                <option value="normal">Normal</option>
                <option value="hard">Hard</option>
              </select>
            </div>

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
          </div>

          <button 
            onClick={startServer} 
            disabled={loading}
            className="btn-primary btn-large"
          >
            {loading ? 'Starting Server...' : '🚀 Start New Server'}
          </button>
        </div>

        {/* Status Message */}
        {message && (
          <div className={`message ${message.startsWith('✓') ? 'success' : 'error'}`}>
            {message}
          </div>
        )}

        {/* Active Servers */}
        <div className="servers">
          <div className="servers-header">
            <h2>Active Servers ({servers.length})</h2>
            <button 
              onClick={fetchServers}
              className="btn-secondary btn-small"
            >
              🔄 Refresh
            </button>
          </div>

          {servers.length === 0 ? (
            <div className="empty">
              <p>No servers running.</p>
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

                  <div className="server-details">
                    <div className="detail-row">
                      <strong>Join Address (Local):</strong>
                      <div className="copy-field">
                        <code>localhost:{server.port}</code>
                        <button 
                          className="btn-copy"
                          onClick={() => copyToClipboard(`localhost:${server.port}`)}
                        >
                          Copy
                        </button>
                      </div>
                    </div>

                    {server.network && (
                      <div className="detail-row">
                        <strong>Join Address (LAN):</strong>
                        <div className="copy-field">
                          <code>{server.network.lan}</code>
                          <button 
                            className="btn-copy"
                            onClick={() => copyToClipboard(server.network.lan)}
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="detail-row">
                      <strong>Config:</strong>
                      <span>
                        {server.config.max_players} players • 
                        {server.config.difficulty} • 
                        {server.config.game_mode}
                      </span>
                    </div>

                    <div className="detail-row">
                      <strong>World Data:</strong>
                      <code className="volume-name">{server.volume_name}</code>
                    </div>

                    <div className="detail-row">
                      <strong>Container:</strong>
                      <code>{server.container_id}</code>
                    </div>
                  </div>

                  <div className="server-actions">
                    {server.status === 'running' && (
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

                    {server.status === 'stopped' && (
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
          <h3>📖 How to Join</h3>
          <div className="help-grid">
            <div className="help-card">
              <h4>Playing Solo (Same Computer)</h4>
              <ol>
                <li>Start a server above</li>
                <li>Open Minecraft</li>
                <li>Multiplayer → Direct Connect</li>
                <li>Enter: <code>localhost:PORT</code></li>
              </ol>
            </div>

            <div className="help-card">
              <h4>Playing with Friends (Same WiFi)</h4>
              <ol>
                <li>Start a server and copy the LAN address</li>
                <li>Share address with friends</li>
                <li>Friends open Minecraft</li>
                <li>Multiplayer → Direct Connect</li>
                <li>Enter the shared address</li>
              </ol>
            </div>

            <div className="help-card">
              <h4>World Persistence</h4>
              <p>
                ✅ Your world saves automatically<br/>
                ✅ Stop/Restart keeps your world<br/>
                ✅ "Delete Container" keeps world<br/>
                ❌ "Delete World" removes it forever
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
