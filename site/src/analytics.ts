export type Point = { room_id: string; slot: string; sampled_at: string; balance_value: number | null; balance_unit?: string; quality?: string; consumed?: number | null; recharged?: number; consumption_quality?: string };

export type ConsumptionDay = { day: string; consumed: number; recharged: number; endBalance: number | null; quality?: string };

export function sortedPoints(points: Point[]): Point[] {
  return points.filter((point) => typeof point.balance_value === 'number').sort((a, b) => a.sampled_at.localeCompare(b.sampled_at));
}

export function consumptionDays(points: Point[]): ConsumptionDay[] {
  const sorted = sortedPoints(points);
  const canonical = sorted.filter((point) => point.consumed !== undefined || point.consumption_quality !== undefined);
  if (canonical.length) {
    return canonical.map((point) => ({
      day: point.sampled_at.slice(0, 10),
      consumed: typeof point.consumed === 'number' ? point.consumed : 0,
      recharged: point.recharged || 0,
      endBalance: point.balance_value,
      quality: point.consumption_quality || 'insufficient_history',
    }));
  }
  const grouped = new Map<string, ConsumptionDay>();
  for (let index = 1; index < sorted.length; index += 1) {
    const previousPoint = sorted[index - 1];
    const currentPoint = sorted[index];
    const gapHours = (Date.parse(currentPoint.sampled_at) - Date.parse(previousPoint.sampled_at)) / 3600000;
    if (gapHours > 32 || (previousPoint.balance_unit && currentPoint.balance_unit && previousPoint.balance_unit !== currentPoint.balance_unit)) continue;
    const previous = sorted[index - 1].balance_value as number;
    const current = sorted[index].balance_value as number;
    const day = sorted[index].sampled_at.slice(0, 10);
    const row = grouped.get(day) ?? { day, consumed: 0, recharged: 0, endBalance: current };
    if (previous >= 0 && current >= 0 && previous > current && previous - current <= 50) row.consumed += previous - current;
    if (current > previous) row.recharged += current - previous;
    row.endBalance = current;
    grouped.set(day, row);
  }
  return [...grouped.values()].sort((a, b) => a.day.localeCompare(b.day));
}

export function totalConsumption(points: Point[]): number {
  return consumptionDays(points).reduce((total, day) => total + day.consumed, 0);
}

export function averageDailyConsumption(points: Point[], days = 7): number {
  const rows = consumptionDays(points).slice(-days).filter((row) => row.quality ? row.quality === 'ok' : row.consumed > 0);
  if (!rows.length) return 0;
  return rows.reduce((total, row) => total + row.consumed, 0) / rows.length;
}

export function forecast(balance: number | null, points: Point[]) {
  const daily = averageDailyConsumption(points);
  const days = balance != null && daily > 0 ? balance / daily : null;
  const confidence = Math.min(1, consumptionDays(points).filter((row) => row.quality ? row.quality === 'ok' : row.consumed > 0).length / 7);
  return { daily, days, confidence };
}

export function rankByConsumption(rows: Array<{ room_id: string; consumed: number }>) {
  return [...rows].sort((a, b) => b.consumed - a.consumed).map((row, index) => ({ ...row, rank: index + 1 }));
}

export function formatNumber(value: number, digits = 1): string {
  return value.toLocaleString('zh-CN', { maximumFractionDigits: digits });
}
