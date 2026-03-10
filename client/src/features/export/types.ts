export type ExportTab = 'dataset' | 'metadata' | 'history';

export interface ExportHistoryFilters {
  export_type: string;
  date_from: string;
  date_to: string;
}
