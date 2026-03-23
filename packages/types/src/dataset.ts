export interface Dataset {
  id: string;
  name: string;
  filePath: string;
  fileSize: number;
  rowCount: number;
  columnCount: number;
  columnsInfo: ColumnInfo[];
  uploadStatus: UploadStatus;
  createdAt: Date;
  updatedAt: Date;
  fileType: 'csv' | 'excel' | 'json';
  encoding: string;
  delimiter?: string;
}

export type UploadStatus =
  | 'pending'
  | 'uploading'
  | 'processing'
  | 'completed'
  | 'failed';

export interface ColumnInfo {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'datetime';
  nullable: boolean;
  unique: boolean;
  min?: number;
  max?: number;
  mean?: number;
  std?: number;
  uniqueCount?: number;
  missingCount: number;
  missingPercentage: number;
}

export interface DatasetSubset {
  id: string;
  parentDatasetId: string;
  name: string;
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target';
  rowCount: number;
  splitConfig: SplitConfig;
  createdAt: Date;
  updatedAt: Date;
  filePath: string;
  fileSize: number;
}

export interface SplitConfig {
  type: 'time' | 'space' | 'mixed';
  timeColumn?: string;
  idColumn?: string;
  splits: SplitDefinition[];
  timeRange?: {
    start: string;
    end: string;
  };
  spaceGroups?: SpaceGroup[];
}

export interface SplitDefinition {
  name: string;
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target';
  timeRange?: {
    start: string;
    end: string;
  };
  spaceValues?: string[];
  rowCount: number;
  percentage: number;
}

export interface SpaceGroup {
  name: string;
  values: string[];
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target';
}

export interface UploadChunk {
  uploadId: string;
  chunkIndex: number;
  totalChunks: number;
  chunkSize: number;
  totalSize: number;
  fileHash: string;
  fileName: string;
  fileType: string;
}

export interface UploadProgress {
  uploadId: string;
  fileName: string;
  fileSize: number;
  uploadedSize: number;
  progress: number;
  status: UploadStatus;
  chunksUploaded: number;
  totalChunks: number;
  error?: string;
}

export interface DataQualityReport {
  datasetId: string;
  totalRows: number;
  totalColumns: number;
  missingValues: {
    total: number;
    percentage: number;
    byColumn: Record<string, number>;
  };
  duplicateRows: {
    count: number;
    percentage: number;
  };
  outliers: {
    count: number;
    percentage: number;
    byColumn: Record<string, number>;
  };
  dataTypes: Record<string, string>;
  recommendations: string[];
  warnings: string[];
  createdAt: Date;
}

export interface FileSplitInfo {
  originalFile: string;
  originalSize: number;
  chunks: FileChunk[];
  createdAt: Date;
}

export interface FileChunk {
  index: number;
  fileName: string;
  filePath: string;
  size: number;
  startRow?: number;
  endRow?: number;
  timeRange?: {
    start: string;
    end: string;
  };
  spaceValues?: string[];
}