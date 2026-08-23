import { describe, expect, it } from 'vitest';
import { analogy, consumptionDays, forecast, rankByConsumption } from './analytics';

const points = [
  { room_id: 'r', slot: '1', sampled_at: '2026-08-01T00:00:00+08:00', balance_value: 10 },
  { room_id: 'r', slot: '2', sampled_at: '2026-08-01T04:00:00+08:00', balance_value: 8 },
  { room_id: 'r', slot: '3', sampled_at: '2026-08-01T20:00:00+08:00', balance_value: 9 },
  { room_id: 'r', slot: '4', sampled_at: '2026-08-02T00:00:00+08:00', balance_value: 7 },
];

describe('public consumption analytics', () => {
  it('treats drops as consumption and increases as recharge', () => {
    expect(consumptionDays(points)).toEqual([
      { day: '2026-08-01', consumed: 2, recharged: 1, endBalance: 9 },
      { day: '2026-08-02', consumed: 2, recharged: 0, endBalance: 7 },
    ]);
  });
  it('forecasts remaining days from recent average', () => {
    expect(forecast(7, points).daily).toBe(2);
    expect(forecast(7, points).days).toBe(3.5);
  });
  it('ranks highest consumption first and returns a safe analogy', () => {
    expect(rankByConsumption([{ room_id: 'a', consumed: 1 }, { room_id: 'b', consumed: 3 }])[0].room_id).toBe('b');
    expect(analogy(1, 0).text).toContain('手机');
  });
});
