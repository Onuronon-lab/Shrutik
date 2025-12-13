import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { ScriptState, DurationOption } from '../types/state';

import { ScriptLoadingState } from '../types/enhanced';

interface ScriptStore extends ScriptState {
  // Actions
  setLoadingState: (loadingState: ScriptLoadingState) => void;
  setSelectedDuration: (duration: DurationOption | null) => void;
  reset: () => void;
}

const initialState: ScriptState = {
  loadingState: { status: 'idle' },
  selectedDuration: null,
  cache: new Map(),
};

export const useScriptStore = create<ScriptStore>()(
  devtools(
    persist(
      set => ({
        ...initialState,

        setLoadingState: loadingState => set({ loadingState }, false, 'setLoadingState'),

        setSelectedDuration: selectedDuration =>
          set({ selectedDuration }, false, 'setSelectedDuration'),

        reset: () => set(initialState, false, 'reset'),
      }),
      {
        name: 'script-store',
        // Only persist selectedDuration, not the current script or loading states
        partialize: state => ({ selectedDuration: state.selectedDuration }),
      }
    ),
    {
      name: 'script-store',
    }
  )
);
