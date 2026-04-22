from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import docker
import random
import string
import socket

app = FastAPI(title="Arcade Cabinet API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client
docker_client = docker.from_env()

# In-memory storage (POC only)
active_servers = {}

# Helper functions

def generate_join_code():
    """Generate a random join code like DRAGON-42"""
    words = ["DRAGON", "TIGER", "PHOENIX", "WOLF", "BEAR"]
    word = random.choice(words)
    num = random.randint(10, 99)
    return f"{word}-{num}"

def get_local_ip():
    """Get the local IP address for LAN joining"""  
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"

# API Models

class ServerConfig(BaseModel):
    server_name: str = "My Server"
    max_players: int = 10
    difficulty: str = "normal"  
    game_mode: str = "survival"

# Endpoints
 
@app.get("/")
def root():
    return {"message": "Arcade Cabinet API", "status": "running"}


@app.get("/api/servers")
def list_servers():
    """List all active servers"""
    return {"servers": list(active_servers.values())}

@app.get("/api/network/info")
def get_network_info():
    """Get the local IP address for LAN joining"""
    local_ip = get_local_ip()
    return {
        "local_ip": local_ip,
        "localhost": "127.0.0.1",
        "message": f"Share {local_ip}: PORT with friends on the same network"
    }

@app.post("/api/servers/start")
def start_server(config: ServerConfig = None):
    """
    Start a Minecraft server with persistence
    """
    if config is None:
        config = ServerConfig()

    join_code = generate_join_code()
    volume_name = f"minecraft-{join_code.lower()}"
    
    try:
        # Start a Minecraft server 
        container = docker_client.containers.run(
            "itzg/minecraft-server:latest",
            detach=True,
            environment={
                "EULA": "TRUE",
                "VERSION": "1.20.4",
                "TYPE": "VANILLA",
                "MAX_PLAYERS": str(config.max_players),
                "DIFFICULTY": config.difficulty,
                "MODE": config.game_mode,
                "SERVER_NAME": config.server_name
            },
            ports={'25565/tcp': None},
            volumes={volume_name: {"bind": "/data", "mode": "rw"}},  # Named volume 
            name=f"minecraft-{join_code.lower()}",
            remove=False # Don't auto-remove so we can manage lifecycle explicitly
        )

        # Get assigned host port
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['25565/tcp']
        host_port = port_info[0]['HostPort'] if port_info else "unknown"
    
        # Get local IP for LAN joining
        local_ip = get_local_ip()

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
            "network": {
                "localhost": f"localhost:{host_port}",
                "lan": f"{local_ip}:{host_port}"
            }
        }
        active_servers[join_code] = server_info
    
        return {
            "success": True,
            "server": server_info,
            "message": f"Server {join_code} started.  World will persist across restarts."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")
        


@app.post("/api/servers/{join_code}/stop")
def stop_server(join_code: str):
    """Stop a specific server"""
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    
    try:
        container = docker_client.containers.get(server["container_id"])
        container.stop(timeout=30)  # Give it 30 seconds to save
        
        server["status"] = "stopped"
        
        return {
            "success": True,
            "message": f"Server {join_code} stopped. World data preserved in volume {server['volume_name']}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")

@app.post("/api/servers/{join_code}/restart")
def restart_server(join_code: str):
    """Restart a server with the same world data"""
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    
    try:
        # Get the existing container
        container = docker_client.containers.get(server["container_id"])
        
        # Restart it
        container.restart(timeout=30)
        
        # Update status
        server["status"] = "running"
        
        return {
            "success": True,
            "server": server,
            "message": f"Server {join_code} restarted. World data preserved."
        }
        
    except docker.errors.NotFound:
        # Container was removed, need to recreate with same volume
        return recreate_server(join_code)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart server: {str(e)}")


def recreate_server(join_code: str):
    """Recreate a server container using existing volume"""
    server = active_servers[join_code]
    
    try:
        # Start new container with same volume
        container = docker_client.containers.run(
            "itzg/minecraft-server:latest",
            detach=True,
            environment={
                "EULA": "TRUE",
                "VERSION": "1.20.4",
                "TYPE": "VANILLA",
                "MAX_PLAYERS": str(server["config"]["max_players"]),
                "DIFFICULTY": server["config"]["difficulty"],
                "MODE": server["config"]["game_mode"],
                "SERVER_NAME": server["server_name"],
            },
            ports={'25565/tcp': None},
            volumes={server["volume_name"]: {"bind": "/data", "mode": "rw"}},
            name=f"minecraft-{join_code.lower()}-restarted",
            remove=False
        )
        
        # Update server info
        container.reload()
        port_info = container.attrs['NetworkSettings']['Ports']['25565/tcp']
        host_port = port_info[0]['HostPort'] if port_info else "unknown"
        local_ip = get_local_ip()
        
        server["container_id"] = container.short_id
        server["container_name"] = container.name
        server["status"] = "running"
        server["port"] = host_port
        server["network"]["localhost"] = f"localhost:{host_port}"
        server["network"]["lan"] = f"{local_ip}:{host_port}"
        
        return {
            "success": True,
            "server": server,
            "message": f"Server {join_code} recreated with existing world data."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recreate server: {str(e)}")


@app.delete("/api/servers/{join_code}")
def delete_server(join_code: str, delete_world: bool = False):
    """
    Delete a server and optionally its world data
    
    Args:
        join_code: The server's join code
        delete_world: If True, also delete the world data volume
    """
    if join_code not in active_servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = active_servers[join_code]
    
    try:
        # Stop and remove container
        try:
            container = docker_client.containers.get(server["container_id"])
            container.stop(timeout=10)
            container.remove()
        except docker.errors.NotFound:
            pass  # Container already removed
        
        # Optionally delete volume
        if delete_world:
            try:
                volume = docker_client.volumes.get(server["volume_name"])
                volume.remove()
                message = f"Server {join_code} and world data deleted permanently."
            except docker.errors.NotFound:
                message = f"Server {join_code} deleted (volume already removed)."
        else:
            message = f"Server {join_code} deleted. World data preserved in {server['volume_name']}."
        
        # Remove from active servers
        del active_servers[join_code]
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete server: {str(e)}")


@app.get("/api/health")
def health_check():
    """Check if Docker is accessible"""
    try:
        docker_client.ping()
        return {"status": "healthy", "docker": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/volumes")
def list_volumes():
    """List all Minecraft world volumes"""
    try:
        volumes = docker_client.volumes.list(filters={"name": "minecraft-"})
        volume_list = [
            {
                "name": v.name,
                "created": v.attrs.get("CreatedAt", "unknown"),
            }
            for v in volumes
        ]
        return {"volumes": volume_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list volumes: {str(e)}")