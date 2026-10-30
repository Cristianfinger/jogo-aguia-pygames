"""Servidor estático temporário para os testes (serve dist/ numa porta livre)."""
import contextlib, socket, subprocess, sys, time
from pathlib import Path

@contextlib.contextmanager
def serve(directory=None):
    import os
    directory = directory or os.environ.get("AGUIA_DIST", "dist")
    root = Path(__file__).resolve().parent.parent / directory
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--directory", str(root), "--bind", "127.0.0.1"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError:
            time.sleep(0.1)
    try:
        yield f"http://127.0.0.1:{port}/index.html"
    finally:
        proc.terminate()
