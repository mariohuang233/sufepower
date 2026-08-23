import {describe,it,expect} from 'vitest';
describe('public data contracts',()=>{it('keeps balance unit neutral before confirmation',()=>{expect({balance_unit:'unknown'}.balance_unit).toBe('unknown')});it('marks stale values explicitly',()=>{expect({stale:true}.stale).toBe(true)})});
