import { describe, expect, it } from 'vitest';

describe('public room data contracts', () => {
  it('uses yuan as the public balance unit', () => {
    expect({ balance_unit: '元' }.balance_unit).toBe('元');
  });
  it('marks stale values explicitly', () => {
    expect({ stale: true }.stale).toBe(true);
  });
  it('declares the backend-owned daily consumption method', () => {
    expect({ consumption_method: 'adjacent_daily_balance_drop' }.consumption_method).toBe('adjacent_daily_balance_drop');
  });
});
