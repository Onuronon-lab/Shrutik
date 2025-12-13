import { createLazyComponent } from '../common/LazyWrapper';

// Lazy load the AudioVisualizer component
const LazyAudioVisualizer = createLazyComponent(
  () => import('./AudioVisualizer'),
  <div className="audio-visualizer-placeholder">
    <div className="flex items-center justify-center h-12 bg-gray-100 rounded">
      <div className="text-sm text-gray-500">Loading visualizer...</div>
    </div>
  </div>
);

export default LazyAudioVisualizer;
