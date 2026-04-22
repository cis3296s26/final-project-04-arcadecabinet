from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import docker
import random
import os
import json
from pathlib import Path
from typing import Optional
from threading import Lock


app = FastAPI(title="Arcade Cabinet API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client (initialized lazily and with fallbacks so the API can still start)
_docker_client: Optional[docker.DockerClient] = None
_docker_client_error: Optional[str] = None
_docker_client_lock = Lock()

# In-memory storage
active_servers = {}

# Playit config directory (sidecar shares)
_playit_config_dir: Optional[Path] = Path(os.getenv("PLAYIT_CONFIG_DIR", "/app/playit-configs"))
_playit_config_dir_error: Optional[str] = None
try:
    _playit_config_dir.mkdir(parents=True, exist_ok=True)
except Exception as e:
    _playit_config_dir_error = str(e)
    _playit_config_dir = None

PLAYIT_CONFIG_DIR = _playit_config_dir
PLAYIT_URL_SUFFIX = ".url"
DEFAULT_PLAYIT_NETWORK = os.getenv("PLAYIT_NETWORK", "arcade-network")

# Models
class ServerConfig(BaseModel):
    server_name: str = "My Server"
    max_players: int = 10
    difficulty: str = "normal"  
    game_mode: str = "survival"

class TunnelURL(BaseModel):
    url: str

# Helper functions
def _format_docker_error(errors: list[str]) -> str:
    return "; ".join([e for e in errors if e]) or "Unknown error"


def get_docker_client() -> docker.DockerClient:
    """
    Return a working Docker client.

    This intentionally falls back from an invalid DOCKER_HOST to the default
    Unix socket so the API can run across Windows/Mac/Linux (Docker Desktop or native).
    """
    global _docker_client, _docker_client_error

    if _docker_client is not None:
        return _docker_client

    with _docker_client_lock:
        if _docker_client is not None:
            return _docker_client

        errors: list[str] = []
        docker_host = os.getenv("DOCKER_HOST")

        # 1) Try explicit DOCKER_HOST if provided
        if docker_host:
            try:
                client = docker.DockerClient(base_url=docker_host)
                client.ping()
                _docker_client = client
                _docker_client_error = None
                return _docker_client
            except Exception as e:
                errors.append(f"DOCKER_HOST={docker_host} failed: {e}")

        # 2) Try the standard Unix socket if present (most common for Docker Desktop + Linux)
        docker_sock = Path("/var/run/docker.sock")
        if docker_sock.exists():
            try:
                client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
                client.ping()
                _docker_client = client
                _docker_client_error = None
                return _docker_client
            except Exception as e:
                errors.append(f"unix:///var/run/docker.sock failed: {e}")

        # 3) Last resort: whatever docker SDK infers
        try:
            client = docker.from_env()
            client.ping()
            _docker_client = client
            _docker_client_error = None
            return _docker_client
        except Exception as e:
            errors.append(f"docker.from_env() failed: {e}")

        _docker_client_error = _format_docker_error(errors)
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Docker is not reachable from the backend container/process.",
                "details": _docker_client_error,
            },
        )


def generate_join_code():
    """Generate a random join code like DRAGON-42"""
    words = ["DRAGON", "TIGER", "PHOENIX", "WOLF", "BEAR"]
    word = random.choice(words)
    num = random.randint(10, 99)
    return f"{word}-{num}"

def _playit_url_path(join_code: str) -> Optional[Path]:
    if PLAYIT_CONFIG_DIR is None:
        return None
    return PLAYIT_CONFIG_DIR / f"{join_code}{PLAYIT_URL_SUFFIX}"


def write_playit_config(join_code: str, local_ip: str, local_port: int, game_type: str = "minecraft"):
    """
    Write a Playit config file for this server. Playit sidecar will pick this up and create a tunnel.
    """
    if PLAYIT_CONFIG_DIR is None:
        return None

    config = {
        "version": "1",
        "tunnels": [{
            "name": f"{game_type}-{join_code.lower()}",
            "port_type": "tcp",
            "local_port": local_port,
            "local_ip": local_ip,
        }]
    }

    config_path = PLAYIT_CONFIG_DIR / f"{join_code}.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    
    return config_path

def read_playit_tunnel_url(join_code: str) -> Optional[str]:
    """
    Read the assigned public URL from Playit's output. Playit sidecar writes this after creating the tunnel.
    """
    url_file = _playit_url_path(join_code)

    if url_file and url_file.exists():
        return url_file.read_text().strip()
    
    return None

def cleanup_playit_config(join_code: str):
    """Remove Playit config files for a server"""
    if PLAYIT_CONFIG_DIR is None:
        return

    config_file = PLAYIT_CONFIG_DIR / f"{join_code}.json"
    url_file = _playit_url_path(join_code)
    
    config_file.unlink(missing_ok=True)
    if url_file:
        url_file.unlink(missing_ok=True)
    
# Endpoints
 
@app.get("/")
def root():
    return {"message": "Arcade Cabinet API", "status": "running"}


@app.get("/api/servers")
def list_servers():
    """List all active servers"""
    # Refresh tunnel URLs from Playit sidecar
    for join_code, server in active_servers.items():
        primary = server.get("addresses", {}).get("primary")
        if not primary or primary == "pending":
            # Try to read tunnel URL from sidecar
            tunnel_url = read_playit_tunnel_url(join_code)
            if tunnel_url:
                server["addresses"]["primary"] = tunnel_url
    
    return {"servers": list(active_servers.values())}
                

@app.post("/api/servers/start")
def start_server(config: ServerConfig = None):
    """
    Start a Minecraft server.
    Creates Playit config for automatic tunneling.
    """
    if config is None:
        config = ServerConfig()
    
    join_code = generate_join_code()
    volume_name = f"minecraft-{join_code.lower()}"
    
    try:
        docker_client = get_docker_client()

        # If we're running under docker-compose, prefer attaching game servers to the shared network
        # so the Playit sidecar can reach them by container name.
        network_name: Optional[str] = None
        try:
            networks = docker_client.networks.list(filters={"name": DEFAULT_PLAYIT_NETWORK})
            if any(n.name == DEFAULT_PLAYIT_NETWORK for n in networks):
                network_name = DEFAULT_PLAYIT_NETWORK
        except Exception:
            network_name = None

        # Start Minecraft container
        run_kwargs = {
            "detach": True,
            "environment": {
                "EULA": "TRUE",
                "VERSION": "1.20.4",
                "TYPE": "VANILLA",
                "MAX_PLAYERS": str(config.max_players),
                "DIFFICULTY": config.difficulty,
                "MODE": config.game_mode,
                "SERVER_NAME": config.server_name,
            },
            "ports": {'25565/tcp': None},  # Random host port for localhost/manual Playit
            "volumes": {volume_name: {"bind": "/data", "mode": "rw"}},
            "name": f"minecraft-{join_code.lower()}",
            "remove": False,
        }
        if network_name:
            run_kwargs["network"] = network_name

        container = docker_client.containers.run("itzg/minecraft-server:latest", **run_kwargs)
 
        # Get assigned port
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['25565/tcp']
        host_port = port_info[0]['HostPort'] if port_info else "unknown"
        
        # Write Playit config for sidecar mode (if configured).
        # The sidecar can reach the game server by container name + container port when on the same network.
        write_playit_config(join_code, container.name, 25565, "minecraft")
        
        # Try to read tunnel URL (may not be ready immediately)
        tunnel_url = read_playit_tunnel_url(join_code)
        
        # Store server info
        server_info = {
            "join_code": join_code,
            "container_id": container.short_id,
            "container_name": container.name,
            "game_type": "minecraft",
            "status": "running",
            "port": host_port,
            "volume_name": volume_name,
            "server_name": config.server_name,
            "config": {
                "max_players": config.max_players,
                "difficulty": config.difficulty,
                "game_mode": config.game_mode
            },
            "addresses": {
                "primary": tunnel_url or "pending",  # Tunnel URL (main address)
                "local": f"localhost:{host_port}"     # Local only
            }
        }
        active_servers[join_code] = server_info
        
        return {
            "success": True,
            "server": server_info,
            "message": "Server starting. Tunnel URL will appear shortly." if not tunnel_url else "Server ready!"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")
 
 
@app.post("/api/servers/{join_code}/tunnel")
def set_tunnel_url(join_code: str, tunnel: TunnelURL):
    """
    Manual fallback: User provides their Playit tunnel URL.
    Use this if automatic Playit sidecar is not running.
    """
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Update server with user-provided tunnel URL
    active_servers[join_code]["addresses"]["primary"] = tunnel.url
    
    # Also write to file so it persists
    url_file = _playit_url_path(join_code)
    if url_file is not None:
        url_file.write_text(tunnel.url)
    
    return {
        "success": True,
        "message": f"Tunnel URL updated for {join_code}",
        "server": active_servers[join_code]
    }
 
 
@app.post("/api/servers/{join_code}/stop")
def stop_server(join_code: str):
    """Stop a server (preserves world data)"""
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    
    try:
        docker_client = get_docker_client()
        container = docker_client.containers.get(server["container_id"])
        container.stop(timeout=30)
        
        server["status"] = "stopped"
        server["addresses"]["primary"] = "offline"
        
        # Cleanup Playit config
        cleanup_playit_config(join_code)
        
        return {
            "success": True,
            "message": f"Server {join_code} stopped. World preserved."
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")
 
 
@app.post("/api/servers/{join_code}/restart")
def restart_server(join_code: str):
    """Restart a server with the same world data"""
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    
    try:
        docker_client = get_docker_client()
        container = docker_client.containers.get(server["container_id"])
        container.restart(timeout=30)
        
        # Get new port (might change)
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['25565/tcp']
        new_port = port_info[0]['HostPort'] if port_info else server["port"]
        
        server["status"] = "running"
        server["port"] = new_port
        server["addresses"]["local"] = f"localhost:{new_port}"
        
        # Recreate Playit tunnel with new port
        write_playit_config(join_code, container.name, 25565, "minecraft")
        tunnel_url = read_playit_tunnel_url(join_code)
        server["addresses"]["primary"] = tunnel_url or "pending"
        
        return {
            "success": True,
            "server": server,
            "message": "Server restarted. Tunnel recreating..."
        }

    except docker.errors.NotFound:
        # Container removed, need full recreation
        raise HTTPException(status_code=500, detail="Container not found. Use start_server instead.")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart: {str(e)}")
 
 
@app.delete("/api/servers/{join_code}")
def delete_server(join_code: str, delete_world: bool = False):
    """Delete a server and optionally its world data"""
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    
    try:
        docker_client = get_docker_client()
        # Stop and remove container
        try:
            container = docker_client.containers.get(server["container_id"])
            container.stop(timeout=10)
            container.remove()
        except docker.errors.NotFound:
            pass
        
        # Optionally delete volume
        if delete_world:
            try:
                volume = docker_client.volumes.get(server["volume_name"])
                volume.remove()
                message = f"Server {join_code} and world deleted permanently."
            except docker.errors.NotFound:
                message = f"Server {join_code} deleted (volume already removed)."
        else:
            message = f"Server {join_code} deleted. World preserved in {server['volume_name']}."
        
        # Cleanup Playit config
        cleanup_playit_config(join_code)
        
        # Remove from active servers
        del active_servers[join_code]
        
        return {"success": True, "message": message}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")
 
 
@app.get("/api/health")
def health_check():
    """Check system health"""
    try:
        docker_client = get_docker_client()
        
        # Playit status: only "automatic" if we actually see tunnels (.url files)
        playit_dir_ok = PLAYIT_CONFIG_DIR is not None
        playit_urls = list(PLAYIT_CONFIG_DIR.glob(f"*{PLAYIT_URL_SUFFIX}")) if playit_dir_ok else []
        
        return {
            "status": "healthy",
            "docker": "connected",
            "playit_sidecar": "enabled" if playit_urls else "manual mode",
            "playit_config_dir": str(PLAYIT_CONFIG_DIR) if playit_dir_ok else None,
            "playit_config_dir_error": _playit_config_dir_error,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
 
 
@app.get("/api/playit/status")
def playit_status():
    """Check Playit sidecar status and list active tunnels"""
    if PLAYIT_CONFIG_DIR is None:
        return {
            "config_dir": None,
            "configs_written": 0,
            "tunnels_active": 0,
            "mode": "manual",
            "error": _playit_config_dir_error,
        }

    configs = list(PLAYIT_CONFIG_DIR.glob("*.json"))
    urls = list(PLAYIT_CONFIG_DIR.glob(f"*{PLAYIT_URL_SUFFIX}"))
    
    return {
        "config_dir": str(PLAYIT_CONFIG_DIR),
        "configs_written": len(configs),
        "tunnels_active": len(urls),
        "mode": "automatic" if urls else "manual"
    }

@app.get("/api/volumes")
def list_volumes():
    """List all Minecraft world volumes"""
    try:
        docker_client = get_docker_client()
        volumes = docker_client.volumes.list(filters={"name": "minecraft-"})
        volume_list = [
            {
                "name": v.name,
                "created": v.attrs.get("CreatedAt", "unknown"),
            }
            for v in volumes
        ]
        return {"volumes": volume_list}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list volumes: {str(e)}")
