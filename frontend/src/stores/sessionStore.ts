import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { SessionState } from '../types/state';
import { RecordingSession } from '../types/api';

interface SessionStore extends SessionState {
  // Actions
  setCurrent: (session: RecordingSession | null) => void;
  setCreating: (isCreating: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState: SessionState = {
  current: null,
  isCreating: false,
  error: null,
  createdAt: null,
  expiresAt: null,
};

export const useSessionStore = create<SessionStore>()(
  devtools(
    persist(
      set => ({
        ...initialState,

        setCurrent: current => set({ current }, false, 'setCurrent'),

        setCreating: isCreating => set({ isCreating }, false, 'setCreating'),

        setError: error => set({ error }, false, 'setError'),

        reset: () => set(initialState, false, 'reset'),
      }),
      {
        name: 'session-store',
        // Persist the current session but not loading/error states
        partialize: state => ({ current: state.current }),
      }
    ),
    {
      name: 'session-store',
    }
  )
);
