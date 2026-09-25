#!/bin/sh
set -eu

eval "$(python - <<'PY'
import json, shlex
from pathlib import Path
p = Path('/data/options.json')
options = json.loads(p.read_text()) if p.is_file() else {}
threads = int(options.get('threads', 4))
if not 1 <= threads <= 32:
    raise SystemExit('threads must be between 1 and 32')
print('LAYA_THREADS=' + shlex.quote(str(threads)))
print('LAYA_API_KEY=' + shlex.quote(str(options.get('api_key', ''))))
PY
)"
export LAYA_THREADS LAYA_API_KEY
export HF_HOME=/data/huggingface
export LAYA_HOST=0.0.0.0
export LAYA_PORT=8000
export LAYA_DEVICE=cpu
export LAYA_MODELS=multilingual
export LAYA_PRELOAD=1

exec python -m laya.serve
