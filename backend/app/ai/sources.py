"""Fetch user-provided public pages as research sources (BRD MOD-03A MVP: competitors/URLs the
user enters). Page text is untrusted data; the server only ever fetches public internet hosts."""

import html
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlsplit

import httpx

MAX_SOURCES = 8
MAX_BYTES = 2 * 1024 * 1024
MAX_CHARS = 6000
UA = "Mozilla/5.0 (compatible; GrowthPilotResearch/1.0; +https://growthpilot.vn/bot)"


class BlockedURL(ValueError):
    pass


def _check_public(url: str) -> None:
    """SSRF guard: http(s) only, and every resolved address must be a public one.
    shortcut: httpx resolves again (DNS-rebinding window); pin the IP if this ever fetches for
    untrusted tenants at scale."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise BlockedURL("chỉ hỗ trợ http/https")
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise BlockedURL("không phân giải được tên miền") from e
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise BlockedURL("địa chỉ nội bộ bị chặn")


def _text(raw: str) -> tuple[str, str]:
    title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.DOTALL | re.IGNORECASE)
    body = re.sub(
        r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE
    )
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", html.unescape(body)).strip()
    return (html.unescape(title.group(1)).strip() if title else ""), body[:MAX_CHARS]


def fetch(url: str, client: httpx.Client) -> dict:
    for _ in range(4):  # follow redirects by hand so each hop is checked
        _check_public(url)
        with client.stream("GET", url, headers={"User-Agent": UA}) as r:
            if r.is_redirect and "location" in r.headers:
                url = urljoin(url, r.headers["location"])
                continue
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            if "html" not in ctype and "text/plain" not in ctype:
                raise ValueError(f"không phải trang văn bản ({ctype or 'unknown'})")
            data = b""
            for chunk in r.iter_bytes():
                data += chunk
                if len(data) > MAX_BYTES:
                    break
            title, text = _text(data.decode(r.encoding or "utf-8", "replace"))
            return {"url": url, "title": title or url, "text": text}
    raise ValueError("quá nhiều lần chuyển hướng")


def fetch_all(urls: list[str]) -> tuple[list[dict], list[str]]:
    """Returns ([{index, url, title, text}], [failure notes])."""
    sources, failed = [], []
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        for url in list(dict.fromkeys(urls))[:MAX_SOURCES]:
            try:
                page = fetch(url, client)
            except (httpx.HTTPError, ValueError) as e:
                failed.append(f"{url}: {e}")
                continue
            if page["text"]:
                sources.append({"index": len(sources), **page})
    return sources, failed
