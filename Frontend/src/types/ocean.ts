export interface OceanDataResponse {
  message?: string;
  viz_spec?: VizSpec;
  rows?: any[];
}

export interface VizSpec {
  viz_type: 'profile_plot' | 'ts_diagram' | 'trajectory_map' | 'surface_map' | 'contour_map_depth' | 'time_series_point' | 'hovmoller' | 'section_plot' | 'table' | 'line' | 'bar' | 'area' | 'scatter';
  title?: string;
  mark?: 'line' | 'point' | 'area' | 'rect' | 'circle';
  encoding?: any;
  fields_required?: string[];
  transform?: any[];
  notes?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: OceanDataResponse;
}

export interface Settings {
  units: 'metric' | 'imperial';
  reverseDepthAxis: boolean;
  smoothing: boolean;
  downsampling: number;
}