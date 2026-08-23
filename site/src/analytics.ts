export type Point = { room_id: string; slot: string; sampled_at: string; balance_value: number | null; balance_unit?: string; quality?: string };

export type ConsumptionDay = { day: string; consumed: number; recharged: number; endBalance: number | null };

export function sortedPoints(points: Point[]): Point[] {
  return points.filter((point) => typeof point.balance_value === 'number').sort((a, b) => a.sampled_at.localeCompare(b.sampled_at));
}

export function consumptionDays(points: Point[]): ConsumptionDay[] {
  const sorted = sortedPoints(points);
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
  const rows = consumptionDays(points).slice(-days).filter((row) => row.consumed > 0);
  if (!rows.length) return 0;
  return rows.reduce((total, row) => total + row.consumed, 0) / rows.length;
}

export function forecast(balance: number | null, points: Point[]) {
  const daily = averageDailyConsumption(points);
  const days = balance != null && daily > 0 ? balance / daily : null;
  const confidence = Math.min(1, consumptionDays(points).filter((row) => row.consumed > 0).length / 7);
  return { daily, days, confidence };
}

export function rankByConsumption(rows: Array<{ room_id: string; consumed: number }>) {
  return [...rows].sort((a, b) => b.consumed - a.consumed).map((row, index) => ({ ...row, rank: index + 1 }));
}

export function formatNumber(value: number, digits = 1): string {
  return value.toLocaleString('zh-CN', { maximumFractionDigits: digits });
}

export function analogy(value: number, seed = Math.random()): { icon: string; text: string; detail: string } {
  const options = [
    { icon: '📱', text: `约等于手机充电 ${formatNumber(value * 74, 0)} 次`, detail: '按 1 度电约可为手机充电 74 次估算' },
    { icon: '🧺', text: `约等于洗衣 ${formatNumber(value * 2, 0)} 桶`, detail: '按每桶洗衣约 0.5 度电估算' },
    { icon: '☕', text: `约等于煮咖啡 ${formatNumber(value * 12, 0)} 杯`, detail: '把复杂的度数换成一杯热咖啡' },
    { icon: '🚲', text: `电动车大约能骑 ${formatNumber(value * 50, 0)} 公里`, detail: '按常见电动车每公里约 0.02 度电估算' },
    { icon: '🚗', text: `小米 SU7 约能行驶 ${formatNumber(value * 6, 0)} 公里`, detail: '按电动车每公里约 0.16 度电估算' },
    { icon: '🌳', text: `需要约 ${formatNumber(value * 0.06, 1)} 棵树吸收对应碳排放`, detail: '碳排放为公开估算口径，仅用于直观理解' },
    { icon: '🤖', text: `约支持 ${formatNumber(value * 20, 0)} 次 AI 问答`, detail: 'AI 用电量因模型和设备不同而变化' },
  ];
  return options[Math.floor(Math.max(0, Math.min(0.999999, seed)) * options.length)];
}
