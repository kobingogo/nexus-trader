import { useState, useCallback, useRef } from 'react';

interface StreamState {
  data: string;
  loading: boolean;
  error: string | null;
  done: boolean;
}

export function useStreamFetcher() {
  const [state, setState] = useState<StreamState>({
    data: '',
    loading: false,
    error: null,
    done: false,
  });
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchStream = useCallback(async (url: string, options?: RequestInit) => {
    // Reset state
    setState({ data: '', loading: true, error: null, done: false });
    
    // Abort previous request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let accumulatedData = '';
      let lineBuffer = '';

      while (true) {
        const { value, done } = await reader.read();
        
        if (done) {
          if (lineBuffer.trim()) {
            processLine(lineBuffer);
          }
          setState(prev => ({ ...prev, loading: false, done: true }));
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        lineBuffer += chunk;
        
        const lines = lineBuffer.split('\n');
        // The last element will be a partial line (or empty if it ended with \n)
        lineBuffer = lines.pop() || '';
        
        for (const line of lines) {
          processLine(line);
        }
      }

      function processLine(line: string) {
        if (!line.trim()) return;
        try {
          const msg = JSON.parse(line);
          if (msg.type === 'chunk') {
            accumulatedData += msg.content;
            setState(prev => ({ ...prev, data: accumulatedData }));
          } else if (msg.type === 'status') {
            // Optional: expose status to UI if needed
          } else if (msg.type === 'error') {
            throw new Error(msg.content);
          }
        } catch (e) {
          // If it's a real parse error, log it. Partial lines are handled by buffering.
          console.error("Stream parse error:", e, "Line:", line);
        }
      }
    } catch (err: unknown) {
      const error = err as Error;
      if (error.name === 'AbortError') {
        console.log('Fetch aborted');
      } else {
        console.error("Stream fetch error:", error);
        setState(prev => ({ ...prev, loading: false, error: error.message || 'Unknown error' }));
      }
    } finally {
      abortControllerRef.current = null;
    }
  }, []);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setState(prev => ({ ...prev, loading: false }));
    }
  }, []);

  return { ...state, fetchStream, abort };
}
