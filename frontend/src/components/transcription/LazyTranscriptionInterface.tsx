import { createLazyComponent } from '../common/LazyWrapper';

// Lazy load the TranscriptionInterface component
const LazyTranscriptionInterface = createLazyComponent(
  () => import('./TranscriptionInterface'),
  <div className="space-y-6">
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-full mb-4"></div>
      <div className="h-16 bg-gray-200 rounded mb-6"></div>
      <div className="h-32 bg-gray-200 rounded mb-6"></div>
      <div className="h-48 bg-gray-200 rounded"></div>
    </div>
  </div>
);

export default LazyTranscriptionInterface;
