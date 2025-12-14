import React from 'react';
import LazyExportBatchManager from '../components/export/LazyExportBatchManager';

const ExportPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <LazyExportBatchManager />
    </div>
  );
};

export default ExportPage;
