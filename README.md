# Arcade Cabinet

# How to run

Before running, ensure Docker Desktop is installed and running.

1. In Docker Desktop settings, under "General", enable "Expose daemon on tcp://localhost:2375 without TLS".

2. The `.env` file is configured for cross-platform. For Windows/Mac/Linux, it uses `tcp://host.docker.internal:2375`. If you need to change it, edit `.env`.

- On the command line run with
```
docker-compose up --build  
```

This will start the backend on port 8000 and frontend on port 3000.

# How to contribute
Follow this project board to know the latest status of the project: [https://nq-98.atlassian.net/jira/software/projects/AC/boards/35] 

### How to build
- Use this github repository: ... 
- Specify what branch to use for a more stable release or for cutting edge development.  
- Use InteliJ 11
- Specify additional library to download if needed 
- What file and target to compile and run. 
- What is expected to happen when the app start. 
