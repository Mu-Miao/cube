import hashlib
import hmac
import time
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin

from app.config import BACKEND_DIR, settings


FIRMWARE_DIR = BACKEND_DIR / "data" / "firmware"
_metadata_cache: dict[Path, tuple[int, int, str]] = {}


def firmware_md5(path: Path) -> str:
    stat = path.stat()
    cached = _metadata_cache.get(path)
    key = (stat.st_mtime_ns, stat.st_size)
    if cached and cached[:2] == key:
        return cached[2]
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    _metadata_cache[path] = (key[0], key[1], digest)
    return digest


def _signature(filename: str, expires: int) -> str:
    payload = f"{filename}:{expires}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest()


def build_signed_firmware_url(
    base_url: str,
    filename: str,
    ttl_seconds: int = 600,
) -> str:
    expires = int(time.time()) + ttl_seconds
    query = urlencode({"expires": expires, "signature": _signature(filename, expires)})
    normalized_base = base_url if base_url.endswith("/") else f"{base_url}/"
    path = f"api/v1/ota/firmware/{quote(filename)}"
    return f"{urljoin(normalized_base, path)}?{query}"


def resolve_signed_firmware(filename: str, expires: int, signature: str) -> Path | None:
    if expires < int(time.time()):
        return None
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name.endswith(".bin"):
        return None
    if not hmac.compare_digest(_signature(safe_name, expires), signature):
        return None
    path = FIRMWARE_DIR / safe_name
    return path if path.is_file() else None
