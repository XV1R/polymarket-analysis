set dotenv-load

# Common paths
VENV_BIN := "./venv/bin"

# Aliases
alias f := fast
alias l := lab
alias r := run
alias s := streamlit
alias dc := docker-up
alias dcd := docker-down
alias dcl := docker-logs
alias dr := docker-rebuild-restart

@_default:
    just --list

run:
    {{VENV_BIN}}/python3 app.py

lab:
    {{VENV_BIN}}/jupyter lab

fast:
    {{VENV_BIN}}/fastapi dev app.py

streamlit:
    {{VENV_BIN}}/streamlit run dashboard.py

install PACKAGE:
    {{VENV_BIN}}/pip install {{PACKAGE}}


# Docker commands
docker-build:
    # Build all Docker images with verbose output
    docker compose build --progress=plain --no-cache

docker-build-cached:
    # Build all Docker images with cache (faster)
    docker compose build --progress=plain

docker-build-api:
    # Build API image only with verbose output
    docker compose build --progress=plain --no-cache api

docker-build-dashboard:
    # Build Dashboard image only with verbose output
    docker compose build --progress=plain --no-cache dashboard

docker-up:
    # Start all services in detached mode with verbose output
    docker compose up -d --remove-orphans

docker-up-verbose:
    # Start all services in foreground with verbose output
    docker compose up --build

docker-down:
    # Stop and remove all containers
    docker compose down

docker-restart:
    # Restart all services
    docker compose restart

docker-logs:
    # View logs from all services (last 100 lines, then follow)
    docker compose logs --tail=100 -f

docker-logs-api:
    # View logs from API service only (last 100 lines, then follow)
    docker compose logs --tail=100 -f api

docker-logs-dashboard:
    # View logs from Dashboard service only (last 100 lines, then follow)
    docker compose logs --tail=100 -f dashboard

docker-logs-all:
    # View all logs from all services (no limit)
    docker compose logs --tail=all

docker-ps:
    # Show running containers with details
    docker compose ps -a

docker-rebuild:
    # Rebuild and restart all services with verbose output
    docker compose up -d --build --progress=plain --force-recreate

docker-rebuild-restart:
    # Stop, rebuild, and restart all services
    docker compose down
    docker compose build
    docker compose up -d

docker-clean:
    # Stop containers and remove volumes
    docker compose down -v

docker-clean-all:
    # Remove containers, volumes, and images
    docker compose down -v --rmi all

docker-shell-api:
    # Open shell in API container
    docker compose exec api /bin/bash

docker-shell-dashboard:
    # Open shell in Dashboard container
    docker compose exec dashboard /bin/bash

docker-status:
    # Show status of all services
    @docker compose ps -a
    @echo ""
    @echo "API Health:"
    @curl -s http://localhost:8000/ | head -1 || echo "API not responding"
    @echo ""
    @echo "Dashboard Health:"
    @curl -s http://localhost:8501/_stcore/health | head -1 || echo "Dashboard not responding"

docker-debug:
    # Show detailed debug information
    @echo "=== Docker Compose Configuration ==="
    @docker compose config
    @echo ""
    @echo "=== Docker Images ==="
    @docker images | grep -E "(polymarket|REPOSITORY)" || docker images
    @echo ""
    @echo "=== Docker Containers ==="
    @docker ps -a | grep -E "(polymarket|CONTAINER)" || docker ps -a
    @echo ""
    @echo "=== Docker Networks ==="
    @docker network ls | grep polymarket || docker network ls
    @echo ""
    @echo "=== Build Context Files ==="
    @echo "Files that will be sent to Docker build context:"
    @find . -maxdepth 2 -type f -name "*.py" -o -name "requirements.txt" -o -name "Dockerfile*" | head -20

docker-inspect-api:
    # Inspect API container details
    docker compose ps api
    docker inspect polymarket-api 2>/dev/null || echo "Container not found"

docker-inspect-dashboard:
    # Inspect Dashboard container details
    docker compose ps dashboard
    docker inspect polymarket-dashboard 2>/dev/null || echo "Container not found"

docker-build-logs:
    # Show build logs for failed builds
    @echo "=== Recent Build Logs ==="
    @docker compose logs --tail=200 | grep -i -E "(error|fail|warn|build)" || docker compose logs --tail=200