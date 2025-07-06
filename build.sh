#!/bin/bash

# Build script for Heroku deployment

echo "Installing Node.js dependencies..."
cd frontend
npm install

echo "Building React app..."
npm run build

echo "Moving back to root..."
cd ..

echo "Build complete!"
