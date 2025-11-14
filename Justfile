set dotenv-load

# Common paths
VENV_BIN := "./venv/bin"

# Aliases
alias f := fast
alias l := lab
alias r := run

@_default:
    just --list

run:
    {{VENV_BIN}}/python3 main.py

lab:
    {{VENV_BIN}}/jupyter lab

fast:
    {{VENV_BIN}}/fastapi dev main.py