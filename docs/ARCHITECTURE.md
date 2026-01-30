# Dreamscape Architecture

## Overview

Dreamscape is an AI-powered interactive 3D world builder. Users describe scenes using text (and eventually voice), and an LLM interprets their descriptions to procedurally generate and place 3D objects in a real-time Three.js environment.

## Core Principle

The LLM does NOT place pre-made blocks. It **generates novel geometry and materials** via executable scripts, creating unique objects each time. This is the fundamental differentiator.

## System Architecture

```
User Input (text/voice)
       |
       v
  Frontend (Three.js + TypeScript)
       |  WebSocket
       v
  Backend (FastAPI + Python)
       |
       v
  LLM Service (Claude API)
       |  Tool calls
       v
  World State Manager
       |
       v
  Object Generation Pipeline
       |
       v
  Frontend receives objects via WebSocket
       |
       v
  Three.js renders new objects
```

## Components

### Frontend (TypeScript + Three.js)
- **Engine**: Three.js scene management, camera, controls, lighting
- **Object Loader**: Receives generated object definitions from backend, creates Three.js meshes
- **UI**: Text input, status indicators, settings panel
- **Audio** (future): Web Speech API for voice input

### Backend (Python + FastAPI)
- **API Layer**: WebSocket endpoint for real-time communication
- **LLM Service**: Claude API integration with tool definitions
- **World State**: Tracks all objects, their properties, positions, and narrative context
- **Object Generator**: Executes LLM-generated scripts to produce 3D geometry data
- **Narrative Manager**: Maintains story context and scene history for LLM prompts

### LLM Tools
The LLM has access to these tools:
1. **create_object**: Generate a new 3D object with geometry, material, position, physics
2. **modify_object**: Change properties of an existing object
3. **remove_object**: Remove an object from the scene
4. **set_environment**: Change sky, fog, lighting, ambient sounds
5. **create_terrain**: Generate terrain/ground surfaces
6. **narrate**: Send narrative text to the user

### Object Generation
Objects are defined as JSON specifications that the frontend interprets:
- **Geometry**: Parametric (box, sphere, cylinder, etc.) or procedural (via vertex data)
- **Material**: Color, texture parameters, transparency, emissive properties
- **Physics**: Gravity, collision, mass
- **Behavior**: Optional update scripts (simple animations)
- **Metadata**: Name, description, narrative role

## Cost Estimates (Claude API)
- Average prompt with world state + tools: ~2000 tokens input
- Average response with tool calls: ~1000 tokens output
- Per interaction: ~$0.01-0.03 (Claude 3.5 Sonnet)
- Session of 50 interactions: ~$0.50-1.50

## Configuration
All settings in `backend/app/config.py` with environment variable overrides:
- LLM model selection and parameters
- Max objects per scene
- Generation timeout
- API keys
