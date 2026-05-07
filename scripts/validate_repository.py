from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
required = [
    'README.md',
    'docs/index.md',
    'docs/01-analisis-funcional/requerimientos-funcionales.md',
    'docs/02-datos/modelo-logico.md',
    'docs/05-seguridad-cumplimiento/seguridad.md',
    'docs/06-agent-ai/objetivos-agente.md',
    'backend/database/schema.sql',
    'backend/api/openapi.yaml',
    'governance/riesgos.md',
]
missing = [p for p in required if not (root / p).exists()]
if missing:
    print('Missing required files:')
    print('\n'.join(missing))
    sys.exit(1)
print('Repository structure validation passed.')
