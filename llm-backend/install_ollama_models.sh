#!/bin/bash

# Array of models to install
models=(
    "mistral:latest"
    "olmo2:latest"
    "granite-code:8b"
    "dolphin-mistral:latest"
    "wizardlm2:latest"
    "llama3.2:latest"
)

echo "🚀 Starting Ollama model installation..."
echo "----------------------------------------"

# Loop through each model and install
for model in "${models[@]}"; do
    echo "📥 Installing $model..."
    ollama pull "$model"
    
    # Check if the installation was successful
    if [ $? -eq 0 ]; then
        echo "✅ Successfully installed $model"
    else
        echo "❌ Failed to install $model"
    fi
    echo "----------------------------------------"
done

echo "🎉 Installation process completed!"
echo "📋 Listing installed models:"
ollama list