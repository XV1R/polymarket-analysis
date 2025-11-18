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

# Docker commands
docker-build:
    # Build all Docker images
    docker-compose build

docker-up:
    # Start all services in detached mode
    docker-compose up -d

docker-down:
    # Stop and remove all containers
    docker-compose down

docker-restart:
    # Restart all services
    docker-compose restart

docker-logs:
    # View logs from all services
    docker-compose logs -f

docker-logs-api:
    # View logs from API service only
    docker-compose logs -f api

docker-logs-dashboard:
    # View logs from Dashboard service only
    docker-compose logs -f dashboard

docker-ps:
    # Show running containers
    docker-compose ps

docker-rebuild:
    # Rebuild and restart all services
    docker-compose up -d --build

docker-rebuild-restart:
    # Stop, rebuild, and restart all services
    docker-compose down
    docker-compose build
    docker-compose up -d

docker-clean:
    # Stop containers and remove volumes
    docker-compose down -v

docker-clean-all:
    # Remove containers, volumes, and images
    docker-compose down -v --rmi all

docker-shell-api:
    # Open shell in API container
    docker-compose exec api /bin/bash

docker-shell-dashboard:
    # Open shell in Dashboard container
    docker-compose exec dashboard /bin/bash

docker-status:
    # Show status of all services
    @docker-compose ps
    @echo ""
    @echo "API Health:"
    @curl -s http://localhost:8000/ | head -1 || echo "API not responding"
    @echo ""
    @echo "Dashboard Health:"
    @curl -s http://localhost:8501/_stcore/health | head -1 || echo "Dashboard not responding"