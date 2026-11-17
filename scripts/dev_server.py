"""Local static preview server with secret/config files blocked."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent


class SafeStaticHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        requested = unquote(urlsplit(path).path).lstrip("/")
        candidate = (ROOT / requested).resolve()
        if candidate != ROOT and ROOT not in candidate.parents:
            return str(ROOT / "__blocked__")
        if any(part.startswith(".") for part in candidate.relative_to(ROOT).parts):
            return str(ROOT / "__blocked__")
        if candidate.name.lower().startswith(".env"):
            return str(ROOT / "__blocked__")
        return str(candidate)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), SafeStaticHandler)
    print("FasalMitra preview: http://127.0.0.1:8000")
    server.serve_forever()
