#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if Docker is running
check_docker() {
    echo -e "${BLUE}Checking if Docker is running...${NC}"
    if ! docker info > /dev/null 2>&1; then
        echo -e "${YELLOW}Docker is not running. Attempting to start Docker...${NC}"
        
        # Check the OS and start Docker accordingly
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            open -a Docker
            
            # Wait for Docker to start (up to 60 seconds)
            echo -e "${BLUE}Waiting for Docker to start...${NC}"
            for i in {1..60}; do
                if docker info > /dev/null 2>&1; then
                    echo -e "${GREEN}Docker has started successfully!${NC}"
                    return 0
                fi
                sleep 1
                echo -n "."
                if (( i % 10 == 0 )); then
                    echo ""
                fi
            done
            
            echo -e "\n${RED}Failed to start Docker. Please start it manually and try again.${NC}"
            exit 1
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            echo -e "${YELLOW}Attempting to start Docker service...${NC}"
            sudo systemctl start docker
            
            # Wait for Docker to start
            sleep 5
            if docker info > /dev/null 2>&1; then
                echo -e "${GREEN}Docker has started successfully!${NC}"
                return 0
            else
                echo -e "${RED}Failed to start Docker. Please start it manually and try again.${NC}"
                exit 1
            fi
        else
            echo -e "${RED}Unsupported OS. Please start Docker manually and try again.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}Docker is already running.${NC}"
        return 0
    fi
}

# Function to check if Ollama has all required models
check_ollama_models() {
    echo -e "${BLUE}Checking if Ollama has all required models...${NC}"
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}Ollama is not installed. Please install Ollama first.${NC}"
        echo -e "${YELLOW}Visit https://ollama.com/ for installation instructions.${NC}"
        exit 1
    fi
    
    # Get the list of required models from the install_ollama_models.sh file
    required_models=($(grep -E '^\s*"[^"]+' llm-backend/install_ollama_models.sh | sed 's/^\s*"\([^"]*\)".*/\1/'))
    
    # Get the list of installed models
    installed_models=($(ollama list | awk 'NR>1 {print $1}'))
    
    missing_models=()
    
    # Check if all required models are installed
    for model in "${required_models[@]}"; do
        found=false
        for installed in "${installed_models[@]}"; do
            if [[ "$model" == "$installed" ]]; then
                found=true
                break
            fi
        done
        
        if [[ "$found" == false ]]; then
            missing_models+=("$model")
        fi
    done
    
    # If there are missing models, ask the user if they want to install them
    if [[ ${#missing_models[@]} -gt 0 ]]; then
        echo -e "${YELLOW}The following Ollama models are missing:${NC}"
        for model in "${missing_models[@]}"; do
            echo -e "  - ${model}"
        done
        
        read -p "Do you want to install the missing models? (y/n): " install_choice
        if [[ "$install_choice" == "y" || "$install_choice" == "Y" ]]; then
            echo -e "${BLUE}Installing missing Ollama models...${NC}"
            bash llm-backend/install_ollama_models.sh
        else
            echo -e "${YELLOW}Continuing without installing missing models. Some features may not work correctly.${NC}"
        fi
    else
        echo -e "${GREEN}All required Ollama models are installed.${NC}"
    fi
}

# Function to start all services
start_services() {
    # Start Ollama in the background
    echo -e "${BLUE}Starting Ollama service...${NC}"
    ollama serve > ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo -e "${GREEN}Ollama started with PID: $OLLAMA_PID${NC}"
    
    # Give Ollama a moment to start
    sleep 2
    
    # Start Docker Compose services
    echo -e "${BLUE}Starting Docker Compose services...${NC}"
    docker compose up --build -d
    
    # Start the LLM backend
    echo -e "${BLUE}Starting LLM backend service...${NC}"
    cd llm-backend && python app.py &
    LLM_BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}LLM backend started with PID: $LLM_BACKEND_PID${NC}"
    
    echo -e "${GREEN}All services have been started!${NC}"
    echo -e "${YELLOW}To stop all services, press Ctrl+C or run: ./stop_app.sh${NC}"
    
    # Create a file to store PIDs for later cleanup
    echo "$OLLAMA_PID" > .ollama_pid
    echo "$LLM_BACKEND_PID" > .llm_backend_pid
    
    # Wait for user to press Ctrl+C
    trap cleanup INT
    echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
    wait
}

# Function to clean Docker and rebuild everything
clean_and_rebuild() {
    echo -e "${BLUE}Cleaning Docker resources...${NC}"
    
    # Stop and remove containers
    docker compose down
    
    # Remove volumes
    echo -e "${YELLOW}Do you want to remove all Docker volumes? This will delete all data. (y/n): ${NC}"
    read -p "" remove_volumes
    if [[ "$remove_volumes" == "y" || "$remove_volumes" == "Y" ]]; then
        docker compose down -v
        echo -e "${GREEN}Docker volumes removed.${NC}"
    fi
    
    # Remove images
    echo -e "${YELLOW}Do you want to remove all Docker images related to this project? (y/n): ${NC}"
    read -p "" remove_images
    if [[ "$remove_images" == "y" || "$remove_images" == "Y" ]]; then
        docker compose down --rmi all
        echo -e "${GREEN}Docker images removed.${NC}"
    fi
    
    # Prune unused resources
    echo -e "${YELLOW}Do you want to prune unused Docker resources? (y/n): ${NC}"
    read -p "" prune_resources
    if [[ "$prune_resources" == "y" || "$prune_resources" == "Y" ]]; then
        docker system prune -f
        echo -e "${GREEN}Unused Docker resources pruned.${NC}"
    fi
    
    echo -e "${GREEN}Docker cleanup completed.${NC}"
}

# Function to cleanup when the script is interrupted
cleanup() {
    echo -e "\n${BLUE}Stopping all services...${NC}"
    
    # Stop the LLM backend
    if [[ -f .llm_backend_pid ]]; then
        LLM_BACKEND_PID=$(cat .llm_backend_pid)
        kill $LLM_BACKEND_PID 2>/dev/null
        rm .llm_backend_pid
    fi
    
    # Stop Ollama
    if [[ -f .ollama_pid ]]; then
        OLLAMA_PID=$(cat .ollama_pid)
        kill $OLLAMA_PID 2>/dev/null
        rm .ollama_pid
    fi
    
    # Stop Docker Compose services
    docker compose down
    
    echo -e "${GREEN}All services have been stopped.${NC}"
    exit 0
}

# Main script
echo -e "${GREEN}=== Application Startup Script ===${NC}"
echo -e "${BLUE}This script will help you start all the services required for the application.${NC}"
echo -e "${YELLOW}Please choose an option:${NC}"
echo -e "  1. Start application"
echo -e "  2. Clean Docker and rebuild everything"
echo -e "  3. Exit"

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        check_docker
        check_ollama_models
        start_services
        ;;
    2)
        check_docker
        clean_and_rebuild
        echo -e "${YELLOW}Do you want to start the application after cleaning? (y/n): ${NC}"
        read -p "" start_after_clean
        if [[ "$start_after_clean" == "y" || "$start_after_clean" == "Y" ]]; then
            check_ollama_models
            start_services
        else
            echo -e "${GREEN}Cleanup completed. Exiting.${NC}"
        fi
        ;;
    3)
        echo -e "${GREEN}Exiting.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac 