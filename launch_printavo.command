#!/bin/bash

# Set your Printavo credentials here
export PRINTAVO_EMAIL="your-email@printavo.com"
export PRINTAVO_TOKEN="your-token-here"

# Navigate to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the Python script
python3 printavo-order-create.py
