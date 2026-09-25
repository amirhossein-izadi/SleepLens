export interface SignalChannelInfo {
  label: string;
  sample_rate: number;
  n_samples?: number;
}

export interface SignalSeries {
  t: number[];
  /** Present when the window is short enough to send raw points. */
  v?: number[];
  /** Min/max envelope, present after decimation of long windows. */
  min?: number[];
  max?: number[];
}

export interface SignalsPreview {
  study_id: string;
  epoch_index?: number;
  channels: SignalChannelInfo[];
  available_channels?: SignalChannelInfo[];
  start_sec: number;
  duration_sec: number;
  file_duration_sec?: number;
  max_points?: number;
  series: Record<string, SignalSeries>;
}
