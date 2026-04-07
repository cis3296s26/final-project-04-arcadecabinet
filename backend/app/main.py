from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import docker
import random
import string

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


def generate_join_code():
    """Generate a random join code like DRAGON-42"""
    words = ["DRAGON", "TIGER", "PHOENIX", "WOLF", "BEAR"]
    word = random.choice(words)
    num = random.randint(10, 99)
    return f"{word}-{num}"


@app.get("/")
def root():
    return {"message": "Arcade Cabinet API", "status": "running"}


@app.get("/api/servers")
def list_servers():
    """List all active servers"""
    return {"servers": list(active_servers.values())}


@app.post("/api/test/start")
def start_test_container():
    """
    POC: Start a simple Minecraft server container using itzg 
    """
    join_code = generate_join_code()
    
    # Start a Minecraft server container using a simpler Minecraft server image
    container = docker_client.containers.run(
        "itzg/minecraft-server:latest",
        detach=True,
        environment={
            "EULA": "TRUE",
            "VERSION": "1.20.4",
            "TYPE": "VANILLA"
        },
        ports={'25565/tcp': None},
        volumes=[f"/tmp/minecraft-{join_code}:/data"],
        name=f"minecraft-{join_code.lower()}",
        remove=True
    )

    # Get assigned host port
    container.reload()
    port_info = container.attrs['NetworkSettings']['Ports']['25565/tcp']
    host_port = port_info[0]['HostPort'] if port_info else "unknown"
    
    # Store server info
    server_info = {
        "join_code": join_code,
        "container_id": container.short_id,
        "game_type": "minecraft",
        "status": "running",
        "port": host_port
    }
    active_servers[join_code] = server_info
    
    return {
        "success": True,
        "server": server_info,
        "message": f"Minecraft server started. Join at localhost:{host_port}"
    }


@app.post("/api/test/stop")
def stop_all_test_containers():
    """Stop all test containers"""
    stopped = []
    
    for join_code, server in list(active_servers.items()):
        try:
            container = docker_client.containers.get(server["container_id"])
            container.stop()
            stopped.append(join_code)
            del active_servers[join_code]
        except Exception as e:
            print(f"Error stopping {join_code}: {e}")
    
    return {
        "success": True,
        "stopped": stopped,
        "message": f"Stopped {len(stopped)} containers"
    }


@app.get("/api/health")
def health_check():
    """Check if Docker is accessible"""
    try:
        docker_client.ping()
        return {"status": "healthy", "docker": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
