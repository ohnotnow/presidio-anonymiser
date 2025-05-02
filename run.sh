#!/usr/bin/env bash
# run_presidio.sh
#
# Pulls/starts Presidio Docker containers if needed, activates Python venv,
# runs main.py on a given file, then stops & removes containers if they were started by this script.

set -euo pipefail

# Usage check
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input-text-file-or-path-to-directory-of-files>"
  exit 1
fi
INPUT_FILE="$1"

# Docker image & container names
ANALYZER_IMAGE="mcr.microsoft.com/presidio-analyzer:latest"
ANONYMIZER_IMAGE="mcr.microsoft.com/presidio-anonymizer:latest"
ANALYZER_CONTAINER="presidio-analyzer"
ANONYMIZER_CONTAINER="presidio-anonymizer"

# Track which containers this script started
started_containers=()

# Function to ensure a container is running or start if needed
ensure_container() {
  local name="$1" image="$2" port_map="$3"

  # Check if container exists
  if docker ps -a --format '{{.Names}}' | grep -qx "$name"; then
    # Exists: check if running
    if docker ps --format '{{.Names}}' | grep -qx "$name"; then
      echo "[i] Container '$name' is already running; reusing."
    else
      echo "[i] Container '$name' exists but is stopped; starting."
      docker start "$name"
      started_containers+=("$name")
    fi
  else
    # Doesn't exist: pull image and run
    echo "[+] Pulling image '$image'..."
    docker pull "$image"
    echo "[+] Running container '$name'..."
    docker run -d --name "$name" -p $port_map "$image"
    started_containers+=("$name")
  fi
}

# Ensure analyzer and anonymizer containers
ensure_container "$ANALYZER_CONTAINER" "$ANALYZER_IMAGE" "5002:3000"
ensure_container "$ANONYMIZER_CONTAINER" "$ANONYMIZER_IMAGE" "5001:3000"

# Give services time to initialize if newly started
if [[ ${#started_containers[@]} -gt 0 ]]; then
  echo "[+] Waiting for services to become healthy..."
  sleep 5
fi

# Activate Python virtual environment
if [[ -f ".venv/bin/activate" ]]; then
  echo "[+] Activating virtual environment 'venv'..."
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "[!] Virtual environment 'venv' not found."
  exit 1
fi

# Run the anonymization script
if [[ -d "$INPUT_FILE" ]]; then
  echo "[+] Running Python script on directory '$INPUT_FILE'..."
  python main.py --text-path "$INPUT_FILE"
elif [[ -f "$INPUT_FILE" ]]; then
  echo "[+] Running Python script on file '$INPUT_FILE'..."
  python main.py --text-file "$INPUT_FILE"
else
  echo "[!] Error: '$INPUT_FILE' is neither a file nor a directory."
  exit 1
fi

# Deactivate venv
deactivate

# Cleanup: stop & remove containers we started
if [[ ${#started_containers[@]} -gt 0 ]]; then
  echo "[+] Cleaning up containers: ${started_containers[*]}"
  docker stop ${started_containers[*]}
  docker rm   ${started_containers[*]}
else
  echo "[i] No containers were started by this script; skipping cleanup."
fi

echo "[+] Done."
