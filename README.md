# 🛠Current setup 

- ✅ **Set up a local Ubuntu Server on VMware**  
  Simulated a production environment for deployment testing.

- 🐳 **Installed Docker** and configured the backend environment using:
  - **Gunicorn** as the WSGI server for Django
  - **Nginx** as a reverse proxy and static file handler

- 🔧 **Created and configured**:
  - `Dockerfile`
  - `docker-compose.yml`
  - `nginx.conf`  
  To containerize the backend application.

- 📦 **Built and tested Docker images locally**  
  Including configuration of networking, volumes, and container orchestration.

- 🚀 **Set up GitHub Actions CI/CD pipeline**:
  - Triggered on push to the `backend` branch
  - Automatically pulls Docker config files (`Dockerfile`, `docker-compose.yml`, `nginx.conf`) from the `devops` branch
  - Builds and pushes the image to **Docker Hub**


