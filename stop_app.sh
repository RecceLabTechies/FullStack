#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping all services...${NC}"

# Stop the LLM backend
if [[ -f .llm_backend_pid ]]; then
    LLM_BACKEND_PID=$(cat .llm_backend_pid)
    echo -e "${YELLOW}Stopping LLM backend (PID: $LLM_BACKEND_PID)...${NC}"
    kill $LLM_BACKEND_PID 2>/dev/null
    rm .llm_backend_pid
    echo -e "${GREEN}LLM backend stopped.${NC}"
else
    echo -e "${YELLOW}LLM backend PID file not found. It may not be running.${NC}"
fi

# Stop Ollama
if [[ -f .ollama_pid ]]; then
    OLLAMA_PID=$(cat .ollama_pid)
    echo -e "${YELLOW}Stopping Ollama (PID: $OLLAMA_PID)...${NC}"
    kill $OLLAMA_PID 2>/dev/null
    rm .ollama_pid
    echo -e "${GREEN}Ollama stopped.${NC}"
else
    echo -e "${YELLOW}Ollama PID file not found. It may not be running.${NC}"
fi

# Stop Docker Compose services
echo -e "${YELLOW}Stopping Docker Compose services...${NC}"
docker compose down
echo -e "${GREEN}Docker Compose services stopped.${NC}"

echo -e "${GREEN}All services have been stopped successfully.${NC}" 