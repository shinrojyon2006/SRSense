#!/usr/bin/env bash
# ==============================================================================
# SRSense AI — Initial Setup Script
# ==============================================================================
set -e

echo "🚀 Setting up SRSense AI environment..."

if [ ! -f .env ]; then
    echo "📄 Creating .env from .env.example..."
    cp .env.example .env
else
    echo "ℹ️  .env already exists."
fi

echo "✅ Environment preparation complete!"
echo "👉 Run 'docker-compose up --build' to start SRSense AI platform."
