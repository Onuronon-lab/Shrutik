import { createLazyComponent } from '../common/LazyWrapper';

// Lazy load the ExportBatchManager component
const LazyExportBatchManager = createLazyComponent(
  () => import('./ExportBatchManager'),
  <div className="max-w-7xl mx-auto">
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
      <div className="h-32 bg-gray-200 rounded mb-6"></div>
      <div className="h-64 bg-gray-200 rounded"></div>
    </div>
  </div>
);

export default LazyExportBatchManager;
