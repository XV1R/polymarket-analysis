set dotenv-load

# Common paths
VENV_BIN := "./venv/bin"

# Aliases
alias f := fast
alias l := lab
alias r := run
alias s := streamlit

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