import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

root=Path(__file__).resolve().parents[1]; data=root/'public-data/v1'; schemas=root/'schemas/v1'
manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8')); schema=json.loads((schemas/'manifest.schema.json').read_text(encoding='utf-8'))
errors=list(Draft202012Validator(schema).iter_errors(manifest))
if errors: raise SystemExit('manifest schema invalid: '+str(errors[0].message))
raw=' '.join(p.read_text(encoding='utf-8') for p in data.rglob('*.json'))
for word in ('entityacctid','acctno','devno','Authorization','Cookie','手机号','Token'):
    if word in raw: raise SystemExit('forbidden public field: '+word)
print('public data validation passed')
