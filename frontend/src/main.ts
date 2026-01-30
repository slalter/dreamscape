/**
 * Dreamscape - Main entry point.
 * Initializes the 3D scene, WebSocket connection, and UI.
 */

import { SceneManager } from './engine/SceneManager';
import { WebSocketClient } from './engine/WebSocketClient';
import { UI } from './ui/UI';
import type { WorldObject, EnvironmentSettings, TerrainParams } from './types/world';

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

function main(): void {
  const container = document.getElementById('app');
  if (!container) {
    throw new Error('No #app container found');
  }

  // Initialize 3D scene
  const sceneManager = new SceneManager(container);

  // Generate session ID
  const sessionId = generateSessionId();

  // Initialize WebSocket
  const wsClient = new WebSocketClient(sessionId);

  // Initialize UI
  const ui = new UI(container, (text: string) => {
    wsClient.sendUserInput(text);
  });

  // Wire up WebSocket handlers
  wsClient.on('object_created', (data) => {
    const obj = data as unknown as WorldObject;
    sceneManager.addObject(obj);
    ui.addLog(`Created: ${obj.name}`);
  });

  wsClient.on('object_modified', (data) => {
    const obj = data as unknown as WorldObject;
    sceneManager.modifyObject(obj);
    ui.addLog(`Modified: ${obj.name}`);
  });

  wsClient.on('object_removed', (data) => {
    const name = (data as { name: string }).name;
    sceneManager.removeObject(name);
    ui.addLog(`Removed: ${name}`);
  });

  wsClient.on('environment_updated', (data) => {
    const settings = data as unknown as EnvironmentSettings;
    sceneManager.updateEnvironment(settings);
    ui.addLog('Environment updated');
  });

  wsClient.on('terrain_created', (data) => {
    const terrain = data as unknown as TerrainParams;
    sceneManager.addTerrain(terrain);
    ui.addLog(`Terrain created: ${terrain.type}`);
  });

  wsClient.on('narration', (data) => {
    const text = (data as { text: string }).text;
    ui.showNarration(text);
  });

  wsClient.on('status', (data) => {
    const message = (data as { message: string }).message;
    ui.setStatus(message);
  });

  wsClient.on('error', (data) => {
    const message = (data as { message: string }).message;
    ui.showError(message);
  });

  wsClient.on('world_state', (_data) => {
    ui.setStatus('Connected');
    ui.addLog('World initialized');
  });

  // Connect
  wsClient.connect();
}

document.addEventListener('DOMContentLoaded', main);
