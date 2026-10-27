"""Garmin Connect Personal API client (standard library only).

Key -> 24 h access token (no refresh token; we simply ask for a new one).
The key is never printed, logged or put in an exception message.
"""
import gzip
import http.client
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
TOKEN_TTL = 23 * 3600
UA = "NewPaceLab/1.0"


class AuthError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status, path):
        super().__init__("HTTP %s pada %s" % (status, path.split("?")[0]))
        self.status = status


def load_key(athlete_id, keys_dir="keys"):
    """keys/<ID>.key wins over env GARMIN_KEY_<ID>."""
    f = Path(keys_dir) / ("%s.key" % athlete_id)
    if f.is_file():
        k = f.read_text(encoding="utf-8").strip()
        if k:
            return k
    return os.environ.get("GARMIN_KEY_%s" % athlete_id, "").strip() or None


class Client:
    def __init__(self, athlete_id, key, base=BASE, cache_dir=".token_cache", delay=0.4, log=print):
        self.id = athlete_id
        self._key = key
        self.base = base.rstrip("/")
        self.cache = Path(cache_dir) / ("%s.json" % athlete_id)
        self.delay = delay
        self.log = log
        self._token = None
        self.requests = 0

    def __repr__(self):
        return "Client(%s, key=***)" % self.id

    # ------------------------------------------------------------- token
    def token(self, force=False):
        if self._token and not force:
            return self._token
        if not force and self.cache.is_file():
            try:
                c = json.loads(self.cache.read_text())
                if time.time() - c["ts"] < TOKEN_TTL:
                    self._token = c["token"]
                    return self._token
            except (ValueError, KeyError):
                pass
        req = urllib.request.Request(self.base + TOKEN_PATH, data=b"", method="POST",
                                     headers={"Authorization": "ApiKey " + self._key, "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", "replace").strip()
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403):
                raise AuthError("Key %s kedaluwarsa/ditolak (HTTP %s). Buat key baru di "
                                "Garmin Connect > Account Settings." % (self.id, e.code)) from None
            raise ApiError(e.code, TOKEN_PATH) from None
        self._token = _parse_token(body)
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        self.cache.write_text(json.dumps({"token": self._token, "ts": time.time()}))
        return self._token

    # ------------------------------------------------------------- GET
    def get(self, path, params=None, raw=False, timeout=60):
        """JSON (or bytes if raw). None on 404 (endpoint not open to personal keys).
        Retries 429/5xx/timeouts with backoff; refreshes the token once on 401."""
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        refreshed = False
        for attempt in range(5):
            time.sleep(self.delay)
            req = urllib.request.Request(url, headers={
                "Authorization": "Bearer " + self.token(), "Accept": "application/json, */*",
                "Accept-Encoding": "gzip", "User-Agent": UA})
            self.requests += 1
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    body = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        body = gzip.decompress(body)
                    if raw:
                        return body
                    return json.loads(body) if body.strip() else None
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code == 401 and not refreshed:
                    refreshed = True
                    self.token(force=True)
                    continue
                if e.code in (401, 403):
                    raise AuthError("Key %s ditolak (HTTP %s)." % (self.id, e.code)) from None
                if e.code == 429 or e.code >= 500:
                    wait = _retry_after(e) or 2 ** (attempt + 1)
                    self.log("    %s: HTTP %s, tunggu %ss" % (self.id, e.code, wait))
                    time.sleep(wait)
                    continue
                raise ApiError(e.code, path) from None
            except (OSError, http.client.HTTPException) as e:  # timeout, reset
                wait = 2 ** (attempt + 1)
                self.log("    %s: %s, coba lagi %ss" % (self.id, type(e).__name__, wait))
                time.sleep(wait)
        raise ApiError("gagal 5x", path)


def _parse_token(body):
    try:
        data = json.loads(body)
    except ValueError:
        return body  # raw token string
    if isinstance(data, str):
        return data
    for k in ("accessToken", "access_token", "token"):
        if isinstance(data, dict) and data.get(k):
            return data[k]
    raise ApiError("format token tidak dikenal", TOKEN_PATH)


def _retry_after(e):
    try:
        return min(120, int(e.headers.get("Retry-After")))
    except (TypeError, ValueError):
        return None
