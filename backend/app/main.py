from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import docker
import random

app = FastAPI(title="Arcade Cabinet API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THE FIX: Try-Except for Docker Initialization ---
try:
    docker_client = docker.from_env()
    print("✅ Docker connected successfully.")
except Exception as e:
    docker_client = None
    print(f"⚠️ WARNING: Docker not found. Running in MOCK MODE. Error: {e}")

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
    # If empty and in mock mode, add a fake one so the UI isn't empty
    if not active_servers and docker_client is None:
        return {"servers": [
            {"join_code": "MOCK-99", "container_id": "abc123", "game_type": "test", "status": "running", "port": "8080"}
        ]}
    return {"servers": list(active_servers.values())}


@app.post("/api/test/start")
def start_test_container():
    """POC: Start a container OR simulate starting one if Docker is offline"""
    join_code = generate_join_code()
    
    # 1. Check if we can actually use Docker
    if docker_client:
        try:
            container = docker_client.containers.run(
                "nginx:alpine",
                detach=True,
                ports={'80/tcp': None},
                name=f"test-{join_code.lower()}",
                remove=True
            )
            container.reload()
            port_info = container.attrs['NetworkSettings']['Ports']['80/tcp']
            host_port = port_info[0]['HostPort'] if port_info else "unknown"
            
            server_info = {
                "join_code": join_code,
                "container_id": container.short_id,
                "game_type": "test",
                "status": "running",
                "port": host_port
            }
            active_servers[join_code] = server_info
            return {"success": True, "server": server_info, "message": "Real container started."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # 2. Mock Logic (If Docker is not running)
    mock_server = {
        "join_code": join_code,
        "container_id": "mock-id-" + join_code.lower(),
        "game_type": "test",
        "status": "running",
        "port": "8080"
    }
    active_servers[join_code] = mock_server
    return {
        "success": True, 
        "server": mock_server, 
        "message": "MOCK MODE: No Docker found, simulated server startup."
    }


@app.post("/api/test/stop")
def stop_all_test_containers():
    """Stop containers OR clear mock list"""
    stopped = []
    
    for join_code, server in list(active_servers.items()):
        if docker_client:
            try:
                container = docker_client.containers.get(server["container_id"])
                container.stop()
                stopped.append(join_code)
            except:
                pass
        else:
            stopped.append(join_code) # Just simulate stopping in mock mode
            
        del active_servers[join_code]
    
    return {"success": True, "stopped": stopped, "message": f"Cleared {len(stopped)} servers"}


@app.get("/api/health")
def health_check():
    """Check if Docker is accessible"""
    if not docker_client:
        return {"status": "unhealthy", "docker": "disconnected", "mode": "mock"}
    try:
        docker_client.ping()
        return {"status": "healthy", "docker": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}