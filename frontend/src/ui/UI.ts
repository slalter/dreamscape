/**
 * UI overlay for Dreamscape - text input, status, narration display.
 */

export class UI {
  private container: HTMLElement;
  private inputEl: HTMLInputElement;
  private statusEl: HTMLElement;
  private narrativeEl: HTMLElement;
  private logEl: HTMLElement;
  private onSubmit: (text: string) => void;

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
        <div id="help-text">Click to look around | WASD to move | Enter to type</div>
      </div>
      <div id="narrative-panel"></div>
      <div id="bottom-bar">
        <input id="user-input" type="text" placeholder="Describe what you imagine..." autocomplete="off" />
        <div id="input-hint">Press Enter to send</div>
      </div>
      <div id="log-panel"></div>
    `;
    container.appendChild(overlay);

    this.inputEl = document.getElementById('user-input') as HTMLInputElement;
    this.statusEl = document.getElementById('status') as HTMLElement;
    this.narrativeEl = document.getElementById('narrative-panel') as HTMLElement;
    this.logEl = document.getElementById('log-panel') as HTMLElement;

    this.setupInputHandling();
  }

  private setupInputHandling(): void {
    this.inputEl.addEventListener('keydown', (e) => {
      e.stopPropagation(); // Don't trigger movement keys
      if (e.key === 'Enter' && this.inputEl.value.trim()) {
        const text = this.inputEl.value.trim();
        this.inputEl.value = '';
        this.onSubmit(text);
        this.addLog(`You: ${text}`, 'user');
      }
      if (e.key === 'Escape') {
        this.inputEl.blur();
      }
    });

    // Focus input on Enter key when not focused
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && document.activeElement !== this.inputEl) {
        e.preventDefault();
        this.inputEl.focus();
        document.exitPointerLock();
      }
    });
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

    // Fade out after 15 seconds
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

    // Keep only last 50 entries
    while (this.logEl.children.length > 50) {
      this.logEl.removeChild(this.logEl.firstChild!);
    }
  }

  showError(message: string): void {
    this.addLog(`Error: ${message}`, 'error');
  }
}
