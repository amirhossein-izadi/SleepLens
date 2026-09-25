/** Exponential moving average for per-epoch series (chart smoothing). */
export function ema(values: (number | null)[], span = 30): (number | null)[] {
  const alpha = 2 / (span + 1);
  let previous: number | null = null;
  return values.map((value) => {
    if (value === null || value === undefined || Number.isNaN(value)) return value;
    previous = previous === null ? value : alpha * value + (1 - alpha) * previous;
    return Math.round(previous * 1000) / 1000;
  });
}

/** Contiguous [startPosition, endPosition] runs of a boolean predicate. */
export function contiguousRuns(flags: boolean[], predicate: (value: boolean) => boolean): [number, number][] {
  const runs: [number, number][] = [];
  let start: number | null = null;
  for (let index = 0; index < flags.length; index += 1) {
    const active = predicate(flags[index]);
    if (active && start === null) start = index;
    if (!active && start !== null) {
      runs.push([start, index - 1]);
      start = null;
    }
  }
  if (start !== null) runs.push([start, flags.length - 1]);
  return runs;
}
