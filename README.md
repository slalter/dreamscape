# Dreamscape

AI-powered interactive 3D world builder. Describe what you imagine — watch it materialize.

## Quick Start

```bash
git clone https://github.com/slalter/dreamscape.git
cd dreamscape
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
docker compose up
# Open http://localhost:3000
```

## Controls

- **Space** (hold): Push-to-talk — describe what you see
- **Space** (tap): Toggle continuous voice listening
- **WASD**: Move around
- **Mouse**: Look around (click scene first)
- **Enter**: Focus text input (fallback)

## How It Works

1. You describe a scene using voice or text
2. The backend sends your description + current world state to Claude
3. GPT-4o uses function calling to create objects, set environment, add terrain, and narrate
4. Objects appear in your 3D scene in real-time via WebSocket
5. Walk around and describe more — the world evolves

## Architecture

- **Frontend**: Three.js + TypeScript + Vite
- **Backend**: FastAPI + Python + OpenAI API (function calling)
- **Communication**: WebSocket for real-time bidirectional updates
- **Voice**: Web Speech API (Chrome, Edge, Safari)

## Configuration

All settings in `.env` — see `.env.example` for all options including model selection, temperature, max objects, and timeouts.

## Cost

~$0.01-0.05 per interaction using GPT-4o. A 50-interaction session costs ~$0.50-2.50.
