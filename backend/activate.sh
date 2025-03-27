#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Activate virtual environment
source venv/bin/activate 