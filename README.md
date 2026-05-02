# 🕹️ Arcade Cabinet

Arcade Cabinet is a cross-platform application designed to manage and launch game servers seamlessly using Docker. 

---

## 🚀 How to Run

### 1. Prerequisites
Before running the application, ensure **Docker Desktop** is installed and running.
* **Download:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

### 2. Environment Setup
The backend talks to Docker via the Docker socket mount (`/var/run/docker.sock`). 

* If you enable the optional **Playit sidecar**, make sure to set `SECRET_KEY` in your `.env` file.
* This project is fully cross-platform (Windows, Mac, and Linux).

### 3. Launching the App
After downloading the most recent build
In the folder location run the following command in your terminal:
```
docker-compose up --build  
```

* **Frontend:** Access at:
  ```
  http://localhost:3000
  ```
* **Backend:** Access at:
  ```
  http://localhost:8000
  ```

---

## 🛠 Troubleshooting: Connection Errors

If the backend returns `503 Service Unavailable` when you click **"Start server"**, the container cannot reach the Docker socket:

* **Windows (Docker Desktop):** Set `DOCKER_SOCK_PATH=//var/run/docker.sock` in your `.env`, then run `docker compose down` and `docker compose up --build`.
* **Any OS (Fallback):** Enable Docker’s TCP API and set `DOCKER_HOST=tcp://host.docker.internal:2375` in `.env`. 
  > **Note:** This is less secure and recommended for development or class projects only.

---

## 🎮 How to Start a Server

### 1. Select Your Game
To start a server, select the **Create** button for the game you want by hovering over the image.

<img width="1000" alt="Select Game" src="https://github.com/user-attachments/assets/bc5b88e8-0b3e-4e7e-95fc-28f9a35ab3a5" />

### 2. Configure Settings
From there, you can set parameters as desired. For a default setup, leave the settings as they are. Click the **Start New Server** button.

<img width="1000" alt="Configure Server" src="https://github.com/user-attachments/assets/47932f5c-a6ac-4b16-840e-0bb661666129" />

### 3. Connect and Play
A new server will appear in your **Active Servers** list. To connect, go to the specific game client and follow the standard procedures to join.

<img width="1000" alt="Active Servers List" src="https://github.com/user-attachments/assets/7c3b01c1-307d-401b-8e40-ec57dde1e3fa" />
