#!/bin/bash

# Define the source directory (original project directory) and the target directory
SOURCE_DIR="."
TARGET_DIR="./dist"

# Define the top-level directories or files you want to move (relative to SOURCE_DIR)
TOP_LEVEL_FILES_AND_DIRS=(
    "stitch"
    "Dockerfile"
    "requirements.txt"
)


# Ensure the target directory exists and is clean
rm -rf $TARGET_DIR
mkdir -p "$TARGET_DIR"

# Loop through each top-level directory/file and use rsync to move it
for item in "${TOP_LEVEL_FILES_AND_DIRS[@]}"; do
    # Use rsync to move each directory/file, excluding Python cache files
    rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' "$SOURCE_DIR/$item" "$TARGET_DIR/"
done


echo "rsync -av --exclude='.venv' --exclude='data' --exclude='.env' ./dist/ homeserver:/srv/ourstitch/"

echo "cd /srv/ourstitch/ && docker build -t ourstitch:latest . && sudo systemctl restart stack-ourstitch"
