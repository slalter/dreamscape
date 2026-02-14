/**
 * UI overlay for Dreamscape - voice input (primary), text input (fallback),
 * status, narration display.
 */

import { VoiceInput } from '../audio/VoiceInput';
import type { VoiceState } from '../audio/VoiceInput';

export class UI {
  private container: HTMLElement;
  private inputEl: HTMLInputElement;
  private statusEl: HTMLElement;
  private narrativeEl: HTMLElement;
  private logEl: HTMLElement;
  private voiceBtnEl: HTMLElement;
  private voiceIndicatorEl: HTMLElement;
  private interimEl: HTMLElement;
  private costEl: HTMLElement;
  private onSubmit: (text: string) => void;
  private voice: VoiceInput;
  private pendingVoiceText = '';

  constructor(container: HTMLElement, onSubmit: (text: string) => void) {
    this.container = container;
    this.onSubmit = onSubmit;

    // Build UI
    const overlay = document.createElement('div');
    overlay.id = 'ui-overlay';
    overlay.innerHTML = `
      <div id="top-bar">
        <div id="status">Connecting...</div>
        <div id="title">DREAMSCAPE</div>
        <div id="cost-display">$0.0000 (0 requests)</div>
        <div id="help-text">Click to look around | WASD to move | Space to talk</div>
      </div>
      <div id="narrative-panel"></div>
      <div id="voice-indicator">
        <div id="voice-ring"></div>
        <div id="voice-label">Listening...</div>
      </div>
      <div id="interim-text"></div>
      <div id="bottom-bar">
        <button id="voice-btn" title="Hold Space or click to talk">
          <svg id="mic-icon" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </button>
        <input id="user-input" type="text" placeholder="...or type here and press Enter" autocomplete="off" />
        <div id="input-hint">Space = talk | Enter = type</div>
      </div>
      <div id="log-panel"></div>
    `;
    container.appendChild(overlay);

    this.inputEl = document.getElementById('user-input') as HTMLInputElement;
    this.statusEl = document.getElementById('status') as HTMLElement;
    this.narrativeEl = document.getElementById('narrative-panel') as HTMLElement;
    this.logEl = document.getElementById('log-panel') as HTMLElement;
    this.costEl = document.getElementById('cost-display') as HTMLElement;
    this.voiceBtnEl = document.getElementById('voice-btn') as HTMLElement;
    this.voiceIndicatorEl = document.getElementById('voice-indicator') as HTMLElement;
    this.interimEl = document.getElementById('interim-text') as HTMLElement;

    // Initialize voice input
    this.voice = new VoiceInput({
      onStateChange: (state: VoiceState) => this.onVoiceStateChange(state),
      onInterimResult: (text: string) => this.onVoiceInterim(text),
      onFinalResult: (text: string) => this.onVoiceFinal(text),
      onError: (error: string) => this.addLog(error, 'error'),
    });

    this.setupInputHandling();
    this.setupVoiceControls();

    if (!this.voice.isAvailable) {
      this.voiceBtnEl.classList.add('unavailable');
      this.voiceBtnEl.title = 'Voice not available - use text input';
    }
  }

  private setupInputHandling(): void {
    this.inputEl.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter' && this.inputEl.value.trim()) {
        const text = this.inputEl.value.trim();
        this.inputEl.value = '';
        this.submitText(text);
      }
      if (e.key === 'Escape') {
        this.inputEl.blur();
      }
    });

    // Focus input on Enter key when not focused (and not voice active)
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && document.activeElement !== this.inputEl && !this.voice.isListening) {
        e.preventDefault();
        this.inputEl.focus();
        document.exitPointerLock();
      }
    });
  }

  private setupVoiceControls(): void {
    // Click mic button to toggle
    this.voiceBtnEl.addEventListener('click', (e) => {
      e.stopPropagation();
      this.voice.toggle();
    });

    // Space bar: hold to talk (push-to-talk), or tap to toggle
    let spaceDown = false;
    let spaceDownTime = 0;

    document.addEventListener('keydown', (e) => {
      if (e.code === 'Space' && document.activeElement !== this.inputEl) {
        e.preventDefault();
        if (!spaceDown) {
          spaceDown = true;
          spaceDownTime = Date.now();
          if (!this.voice.isListening) {
            this.voice.startListening();
          }
        }
      }
    });

    document.addEventListener('keyup', (e) => {
      if (e.code === 'Space' && document.activeElement !== this.inputEl) {
        e.preventDefault();
        if (spaceDown) {
          spaceDown = false;
          const held = Date.now() - spaceDownTime;
          if (held > 300) {
            // Was a hold - stop and submit
            this.voice.stopListening();
            this.flushVoiceText();
          } else {
            // Was a tap - toggle continuous mode
            // Already started above, leave it running
          }
        }
      }
    });
  }

  private onVoiceStateChange(state: VoiceState): void {
    this.voiceBtnEl.className = `voice-${state}`;
    this.voiceIndicatorEl.className = state === 'listening' ? 'active' : '';

    if (state === 'idle') {
      this.interimEl.textContent = '';
    }
  }

  private onVoiceInterim(text: string): void {
    this.interimEl.textContent = text;
  }

  private onVoiceFinal(text: string): void {
    this.interimEl.textContent = '';
    if (text.trim()) {
      this.pendingVoiceText += (this.pendingVoiceText ? ' ' : '') + text.trim();
      // Auto-submit after a pause (the voice recognition gives us final results
      // at natural phrase boundaries)
      this.submitText(this.pendingVoiceText);
      this.pendingVoiceText = '';
    }
  }

  private flushVoiceText(): void {
    if (this.pendingVoiceText.trim()) {
      this.submitText(this.pendingVoiceText.trim());
      this.pendingVoiceText = '';
    }
  }

  private submitText(text: string): void {
    this.onSubmit(text);
    this.addLog(`You: ${text}`, 'user');
  }

  setStatus(message: string): void {
    this.statusEl.textContent = message;
    this.statusEl.className = message === 'Ready' ? 'ready' :
      message.includes('Imagining') ? 'thinking' : '';
  }

  showNarration(text: string): void {
    const el = document.createElement('div');
    el.className = 'narration-entry';
    el.textContent = text;
    this.narrativeEl.appendChild(el);
    this.narrativeEl.scrollTop = this.narrativeEl.scrollHeight;

    setTimeout(() => {
      el.classList.add('fading');
      setTimeout(() => el.remove(), 2000);
    }, 15000);
  }

  addLog(text: string, type: 'user' | 'system' | 'error' = 'system'): void {
    const el = document.createElement('div');
    el.className = `log-entry log-${type}`;
    el.textContent = text;
    this.logEl.appendChild(el);
    this.logEl.scrollTop = this.logEl.scrollHeight;

    while (this.logEl.children.length > 50) {
      this.logEl.removeChild(this.logEl.firstChild!);
    }
  }

  updateCost(totalCostUsd: number, totalRequests: number): void {
    this.costEl.textContent = `$${totalCostUsd.toFixed(4)} (${totalRequests} req)`;
  }

  showError(message: string): void {
    this.addLog(`Error: ${message}`, 'error');
  }
}
