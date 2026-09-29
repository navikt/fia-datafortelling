import os
import shutil
import sys

print(f"PATH={os.environ.get('PATH', '')}", flush=True)

try:
    quarto = shutil.which("quarto")
    bash = shutil.which("bash")
    print(f"quarto={quarto!r}", flush=True)
    print(f"bash={bash!r}", flush=True)
except Exception as error:
    print(f"which() failed: {error!r}", flush=True)
    raise

if quarto is None:
    print("ERROR: quarto was not found in PATH", flush=True)
    sys.exit(1)
