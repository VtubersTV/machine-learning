#!/bin/bash

# Store the current working directory in a variable
CURRENT_DIR=$(pwd)

echo "Activating the virtual environment..."

# Check if the .venv directory exists, and create it if necessary
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating a new one..."
else
    echo "Virtual environment found. Activating it..."
fi

# Determine if python3 is available, default to python if not
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Determine the appropriate pip version to use
if $PYTHON -m pip --version &> /dev/null; then
    PIP=pip
else
    PIP=pip3
fi

# Create the virtual environment if it doesn't already exist
$PYTHON -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

echo "Virtual environment successfully activated."

# Check if the requirements.txt file is present
if [ ! -f "requirements.txt" ]; then
    exit 0
else
    # Prompt the user to install dependencies from requirements.txt
    read -p "Do you want to install the requirements? [y/n] " INSTALL_REQUIREMENTS

    if [[ "$INSTALL_REQUIREMENTS" =~ ^[Yy]$ ]]; then
        echo "Installing dependencies..."
        $PIP install -r requirements.txt
        echo "Dependencies installed successfully."
    else
        echo "Skipping requirements installation."
    fi
fi
