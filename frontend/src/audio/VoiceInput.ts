/**
 * Voice input using the Web Speech API (SpeechRecognition).
 * Provides continuous speech-to-text with interim results.
 */

// Web Speech API types (not in standard lib)
interface SpeechRecognitionEvent extends Event {
  readonly results: SpeechRecognitionResultList;
  readonly resultIndex: number;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string;
  readonly message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
  onspeechend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
  }
}

export type VoiceState = 'idle' | 'listening' | 'processing' | 'unavailable';

export interface VoiceCallbacks {
  onStateChange: (state: VoiceState) => void;
  onInterimResult: (text: string) => void;
  onFinalResult: (text: string) => void;
  onError: (error: string) => void;
}

export class VoiceInput {
  private recognition: SpeechRecognition | null = null;
  private callbacks: VoiceCallbacks;
  private _state: VoiceState = 'idle';
  private autoRestart = false;
  private silenceTimeout: ReturnType<typeof setTimeout> | null = null;
  private readonly silenceMs: number;

  constructor(callbacks: VoiceCallbacks, silenceMs = 2000) {
    this.callbacks = callbacks;
    this.silenceMs = silenceMs;

    const SpeechRecognitionCtor =
      window.SpeechRecognition ?? window.webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      this._state = 'unavailable';
      callbacks.onStateChange('unavailable');
      return;
    }

    this.recognition = new SpeechRecognitionCtor();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';
    this.recognition.maxAlternatives = 1;

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      this.resetSilenceTimer();

      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      if (interimTranscript) {
        this.callbacks.onInterimResult(interimTranscript);
      }

      if (finalTranscript) {
        this.callbacks.onFinalResult(finalTranscript.trim());
      }
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === 'no-speech') {
        // Not really an error, just no speech detected
        return;
      }
      if (event.error === 'aborted') {
        return;
      }
      this.callbacks.onError(`Speech error: ${event.error}`);
      this.setState('idle');
    };

    this.recognition.onend = () => {
      if (this.autoRestart && this._state === 'listening') {
        // Auto-restart for continuous listening
        try {
          this.recognition?.start();
        } catch {
          this.setState('idle');
        }
      } else {
        this.setState('idle');
      }
    };

    this.recognition.onstart = () => {
      this.setState('listening');
    };
  }

  get state(): VoiceState {
    return this._state;
  }

  get isAvailable(): boolean {
    return this._state !== 'unavailable';
  }

  get isListening(): boolean {
    return this._state === 'listening';
  }

  startListening(): void {
    if (!this.recognition || this._state === 'unavailable') {
      this.callbacks.onError('Voice input not available in this browser');
      return;
    }

    if (this._state === 'listening') {
      this.stopListening();
      return;
    }

    this.autoRestart = true;
    try {
      this.recognition.start();
    } catch {
      // Already started
      this.setState('listening');
    }
  }

  stopListening(): void {
    this.autoRestart = false;
    this.clearSilenceTimer();
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch {
        // Already stopped
      }
    }
    this.setState('idle');
  }

  toggle(): void {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  private setState(state: VoiceState): void {
    this._state = state;
    this.callbacks.onStateChange(state);
  }

  private resetSilenceTimer(): void {
    this.clearSilenceTimer();
    this.silenceTimeout = setTimeout(() => {
      // After silence, we don't stop - continuous mode keeps going
      // But we could use this to trigger a "thinking" state
    }, this.silenceMs);
  }

  private clearSilenceTimer(): void {
    if (this.silenceTimeout) {
      clearTimeout(this.silenceTimeout);
      this.silenceTimeout = null;
    }
  }

  destroy(): void {
    this.stopListening();
    this.recognition = null;
  }
}
