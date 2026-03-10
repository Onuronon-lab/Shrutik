import { createLazyComponent } from '../common/LazyWrapper';

// Lazy load the StatsDashboard component
const LazyStatsDashboard = createLazyComponent(
  () => import('./StatsDashboard'),
  <div className="space-y-6">
    <div className="animate-pulse">
      <div className="flex items-center justify-between mb-6">
        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        <div className="h-8 bg-gray-200 rounded w-32"></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-200 rounded"></div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 bg-gray-200 rounded"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    </div>
  </div>
);

export default LazyStatsDashboard;
