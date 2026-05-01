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
    """
    global _docker_client, _docker_client_error

    if _docker_client is not None:
        return _docker_client

    with _docker_client_lock:
        if _docker_client is not None:
            return _docker_client

        errors: list[str] = []
        docker_host = os.getenv("DOCKER_HOST")

        if docker_host:
            try:
                client = docker.DockerClient(base_url=docker_host)
                client.ping()
                _docker_client = client
                return _docker_client
            except Exception as e:
                errors.append(f"DOCKER_HOST={docker_host} failed: {e}")

        docker_sock = Path("/var/run/docker.sock")
        if docker_sock.exists():
            try:
                client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
                client.ping()
                _docker_client = client
                return _docker_client
            except Exception as e:
                errors.append(f"unix:///var/run/docker.sock failed: {e}")

        try:
            client = docker.from_env()
            client.ping()
            _docker_client = client
            return _docker_client
        except Exception as e:
            errors.append(f"docker.from_env() failed: {e}")

        _docker_client_error = _format_docker_error(errors)
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Docker is not reachable.",
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
    Write a Playit config file for this server. 
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
    Read the assigned public URL from Playit's output.
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
    for join_code, server in active_servers.items():
        primary = server.get("addresses", {}).get("primary")
        if not primary or primary == "pending":
            tunnel_url = read_playit_tunnel_url(join_code)
            if tunnel_url:
                server["addresses"]["primary"] = tunnel_url
    
    return {"servers": list(active_servers.values())}
                

@app.post("/api/servers/start")
def start_server(config: ServerConfig = None):
    """
    Start a Minecraft server.
    """
    if config is None:
        config = ServerConfig()
    
    join_code = generate_join_code()
    volume_name = f"minecraft-{join_code.lower()}"
    
    try:
        docker_client = get_docker_client()
        network_name: Optional[str] = None
        try:
            networks = docker_client.networks.list(filters={"name": DEFAULT_PLAYIT_NETWORK})
            if any(n.name == DEFAULT_PLAYIT_NETWORK for n in networks):
                network_name = DEFAULT_PLAYIT_NETWORK
        except Exception:
            network_name = None

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
            "ports": {'25565/tcp': None},
            "volumes": {volume_name: {"bind": "/data", "mode": "rw"}},
            "name": f"minecraft-{join_code.lower()}",
            "remove": False,
        }
        if network_name:
            run_kwargs["network"] = network_name

        container = docker_client.containers.run("itzg/minecraft-server:latest", **run_kwargs)
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['25565/tcp']
        host_port = port_info[0]['HostPort'] if port_info else "unknown"
        
        write_playit_config(join_code, container.name, 25565, "minecraft")
        tunnel_url = read_playit_tunnel_url(join_code)
        
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
                "primary": tunnel_url or "pending",
                "local": f"localhost:{host_port}"
            }
        }
        active_servers[join_code] = server_info
        return {"success": True, "server": server_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")


@app.post("/api/servers/start/terraria")
def start_terraria_server(config: ServerConfig = None):
    """
    Start a Terraria server.
    """
    if config is None:
        config = ServerConfig()
    
    join_code = generate_join_code()
    volume_name = f"terraria-world-{join_code.lower()}"
    
    try:
        docker_client = get_docker_client()
        network_name: Optional[str] = None
        try:
            networks = docker_client.networks.list(filters={"name": DEFAULT_PLAYIT_NETWORK})
            if any(n.name == DEFAULT_PLAYIT_NETWORK for n in networks):
                network_name = DEFAULT_PLAYIT_NETWORK
        except Exception:
            network_name = None

        terraria_difficulty = "0" if config.difficulty == "normal" else "1"

        run_kwargs = {
            "detach": True,
            "tty": True,
            "stdin_open": True,
            "environment": {
                "WORLD_NAME": f"World-{join_code}",
                "MAX_PLAYERS": str(config.max_players),
                "AUTOCREATE": "1",
                "DIFFICULTY": terraria_difficulty,
                "SECURE": "0"
            },
            "ports": {'7777/tcp': None},
            "volumes": {volume_name: {"bind": "/root/.local/share/Terraria/Worlds", "mode": "rw"}},
            "name": f"terraria-{join_code.lower()}",
            "remove": False,
        }
        if network_name:
            run_kwargs["network"] = network_name

        container = docker_client.containers.run("hexlo/terraria-server-docker:latest", **run_kwargs)
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['7777/tcp']
        host_port = port_info[0]['HostPort'] if port_info else "unknown"
        
        write_playit_config(join_code, container.name, 7777, "terraria")
        tunnel_url = read_playit_tunnel_url(join_code)
        
        server_info = {
            "join_code": join_code,
            "container_id": container.short_id,
            "container_name": container.name,
            "game_type": "terraria",
            "status": "running",
            "port": host_port,
            "volume_name": volume_name,
            "server_name": f"World-{join_code}",
            "config": {
                "max_players": config.max_players,
                "difficulty": config.difficulty
            },
            "addresses": {
                "primary": tunnel_url or "pending",
                "local": f"localhost:{host_port}"
            }
        }
        active_servers[join_code] = server_info
        return {"success": True, "server": server_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")
 
 
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
        cleanup_playit_config(join_code)
        return {"success": True, "message": f"Server {join_code} stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")
 
 
@app.delete("/api/servers/{join_code}")
def delete_server(join_code: str, delete_world: bool = False):
    """Delete a server and optionally its world data"""
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    try:
        docker_client = get_docker_client()
        try:
            container = docker_client.containers.get(server["container_id"])
            container.stop(timeout=10)
            container.remove()
        except docker.errors.NotFound:
            pass
        
        if delete_world:
            try:
                volume = docker_client.volumes.get(server["volume_name"])
                volume.remove()
            except docker.errors.NotFound:
                pass
        
        cleanup_playit_config(join_code)
        del active_servers[join_code]
        return {"success": True, "message": f"Server {join_code} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")