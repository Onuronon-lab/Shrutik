export const formatFileSize = (bytes?: number): string => {
  if (!bytes) return 'N/A';
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${Math.round((bytes / Math.pow(1024, i)) * 100) / 100} ${sizes[i]}`;
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};
