"""Bounded GET transport with validated, pinned IPs and default no-fetch capture."""

import http.client
import ipaddress
import json
import queue
import socket
import ssl
import threading
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit

from rolekai.api.contracts import RawObservation
from rolekai.connectors.base import ConnectorError, require_success
from rolekai.domain import utcnow


def public_ip(value):
    address = ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    if isinstance(address, ipaddress.IPv6Address) and (address.sixtofour or address.teredo):
        return False
    # Do not route translated IPv4 addresses through an apparently public IPv6 literal.
    if isinstance(address, ipaddress.IPv6Address) and address in ipaddress.ip_network(
        "64:ff9b::/96"
    ):
        return False
    return address.is_global and not address.is_multicast and not address.is_unspecified


def validate_url(url):
    try:
        if len(url) > 2000 or "\\" in url or any(ord(c) <= 32 or ord(c) == 127 for c in url):
            raise ValueError("Unsafe URL")
        value = urlsplit(url)
        host = value.hostname
        if value.scheme not in ("https", "http") or not host or value.username or value.password:
            raise ValueError("Unsafe URL")
        if any(
            k.casefold()
            in (
                "api_key",
                "apikey",
                "api_token",
                "access_token",
                "password",
                "token",
                "signature",
                "authorization",
            )
            for k, _ in parse_qsl(value.query)
        ):
            raise ValueError("Credential query not allowed")
        if value.port not in (None, 443 if value.scheme == "https" else 80):
            raise ValueError("Unsafe port")
        host = host.encode("idna").decode("ascii").lower().rstrip(".")
        if (
            host == "localhost"
            or host.endswith((".localhost", ".local", ".internal"))
            or "%" in host
        ):
            raise ValueError("Unsafe host")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
            try:
                address = ipaddress.ip_address(socket.inet_aton(host))
            except OSError:
                pass
        if address is not None and not public_ip(str(address)):
            raise ValueError("Unsafe IP")
        if address is not None:
            host = str(address)
        authority = "[" + host + "]" if ":" in host else host
        return urlunsplit((value.scheme, authority, value.path or "/", value.query, ""))
    except ValueError, UnicodeError:
        raise ConnectorError("UNSAFE_URL") from None


def resolve_public(host):
    try:
        return [str(ipaddress.ip_address(host))]
    except ValueError:
        pass
    result = queue.Queue(maxsize=1)

    def lookup():
        try:
            result.put(socket.getaddrinfo(host, None, type=socket.SOCK_STREAM))
        except OSError:
            result.put(None)

    threading.Thread(target=lookup, daemon=True).start()
    try:
        values = result.get(timeout=3)
    except queue.Empty:
        raise ConnectorError("SOURCE_TIMEOUT", transient=True) from None
    if not values:
        raise ConnectorError("SOURCE_DNS", transient=True)
    return sorted({row[4][0] for row in values})


@dataclass(frozen=True)
class HTTPResult:
    status: int
    headers: dict[str, str]
    body: bytes


def pinned_get(url, ip, timeout, maximum):
    value = urlsplit(url)
    port = value.port or (443 if value.scheme == "https" else 80)
    connection = http.client.HTTPConnection(value.hostname, port, timeout=timeout)
    deadline = time.monotonic() + timeout
    active = [None]

    def interrupt():
        sock = active[0]
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    watchdog = threading.Timer(timeout, interrupt)
    watchdog.daemon = True
    watchdog.start()
    try:
        # Connect to the validated literal IP, preserving original Host and TLS SNI.
        sock = socket.create_connection((ip, port), timeout=timeout)
        active[0] = sock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ConnectorError("SOURCE_TIMEOUT", transient=True)
        sock.settimeout(remaining)
        if value.scheme == "https":
            try:
                sock = ssl.create_default_context().wrap_socket(
                    sock, server_hostname=value.hostname
                )
                active[0] = sock
            except BaseException:
                sock.close()
                raise
        connection.sock = sock
        path = urlunsplit(("", "", value.path or "/", value.query, ""))
        connection.request(
            "GET",
            path,
            headers={
                "Host": value.netloc,
                "Accept-Encoding": "identity",
                "User-Agent": "Rolekai/0.1 (private local discovery)",
            },
        )
        response = connection.getresponse()
        headers = {k.lower(): v for k, v in response.getheaders()}
        expected = headers.get("content-length")
        if expected is not None:
            try:
                expected = int(expected)
            except ValueError:
                raise ConnectorError("SOURCE_SCHEMA") from None
            if expected < 0 or expected > maximum:
                raise ConnectorError("SOURCE_TOO_LARGE")
        if headers.get("content-encoding", "identity").lower() != "identity":
            raise ConnectorError("SOURCE_CONTENT_ENCODING")
        chunks, count = [], 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ConnectorError("SOURCE_TIMEOUT", transient=True)
            sock.settimeout(remaining)
            chunk = response.read1(min(65536, maximum + 1 - count))
            if time.monotonic() >= deadline:
                raise ConnectorError("SOURCE_TIMEOUT", transient=True)
            if not chunk:
                break
            count += len(chunk)
            if count > maximum:
                raise ConnectorError("SOURCE_TOO_LARGE")
            chunks.append(chunk)
            if expected is not None and count == expected:
                break
        if expected is not None and count != expected:
            raise ConnectorError("SOURCE_NETWORK", transient=True)
        return HTTPResult(response.status, headers, b"".join(chunks))
    except OSError, http.client.HTTPException:
        raise ConnectorError("SOURCE_NETWORK", transient=True) from None
    finally:
        watchdog.cancel()
        connection.close()
        if active[0] is not None:
            active[0].close()


class SafeFetcher:
    def __init__(
        self,
        *,
        resolver=resolve_public,
        sender=pinned_get,
        allowed_hosts=(),
        max_bytes=262144,
        timeout=15,
        allow_redirects=True,
    ):
        self.resolver, self.sender = resolver, sender
        self.allowed_hosts = set(allowed_hosts)
        self.max_bytes, self.timeout = max_bytes, timeout
        self.allow_redirects = allow_redirects

    def fetch(self, url):
        deadline = time.monotonic() + self.timeout
        original_scheme = urlsplit(url).scheme
        for _ in range(4):
            url = validate_url(url)
            host = urlsplit(url).hostname
            if host not in self.allowed_hosts:
                raise ConnectorError("HOST_NOT_AUTHORIZED")
            if original_scheme == "https" and urlsplit(url).scheme != "https":
                raise ConnectorError("UNSAFE_REDIRECT")
            addresses = self.resolver(host)
            if not addresses or any(not public_ip(ip) for ip in addresses):
                raise ConnectorError("UNSAFE_DNS")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ConnectorError("SOURCE_TIMEOUT", transient=True)
            response = self.sender(url, addresses[0], remaining, self.max_bytes)
            if len(response.body) > self.max_bytes:
                raise ConnectorError("SOURCE_TOO_LARGE")
            if response.status in (301, 302, 303, 307, 308):
                if not self.allow_redirects:
                    raise ConnectorError("UNSAFE_REDIRECT")
                destination = response.headers.get("location")
                if not destination:
                    raise ConnectorError("UNSAFE_REDIRECT")
                url = urljoin(url, destination)
                continue
            require_success(response.status, response.headers)
            kind = response.headers.get("content-type", "").split(";")[0].lower()
            if kind not in ("text/html", "text/plain", "application/json"):
                raise ConnectorError("SOURCE_CONTENT_TYPE")
            return response
        raise ConnectorError("REDIRECT_LIMIT")


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "template", "iframe"):
            self.hidden += 1
        elif not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "template", "iframe") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def safe_text(content):
    parser = TextExtractor()
    parser.feed(content)
    return " ".join("".join(parser.parts).split())


def fetch_json(url):
    response = SafeFetcher(
        allowed_hosts=["remotive.com", "boards-api.greenhouse.io"],
        max_bytes=8 * 1024 * 1024,
        timeout=30,
        allow_redirects=False,
    ).fetch(url)
    try:
        result = json.loads(response.body)
        if not isinstance(result, dict):
            raise ValueError("Object required")
        return result
    except ValueError, UnicodeError:
        raise ConnectorError("SOURCE_SCHEMA") from None


class ManualURL:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher
        self.errors = []

    def fetch_detail(self, ref, *, text=None):
        url = validate_url(ref.url or "")
        html, error = None, None
        if text is None and self.fetcher is not None:
            try:
                result = self.fetcher.fetch(url)
                if result.headers.get("content-type", "").startswith("text/html"):
                    html = result.body.decode("utf-8", errors="replace")
                    text = safe_text(html)
                elif result.headers.get("content-type", "").startswith("text/plain"):
                    text = result.body.decode("utf-8", errors="replace")
                else:
                    raise ConnectorError("SOURCE_CONTENT_TYPE")
            except ConnectorError as exc:
                if exc.code.startswith(("UNSAFE", "HOST_NOT", "REDIRECT")):
                    raise
                error = exc.code
        return RawObservation(
            source="manual",
            source_url=url,
            retrieved_at=utcnow(),
            original_description_html=html,
            original_description_text=text,
            raw_payload={"needs_review": not bool(text), "fetch_error": error},
        )

    def discover(self, request):
        from rolekai.api.contracts import SourceReference

        return [
            self.fetch_detail(SourceReference(source="manual", url=request.url), text=request.text)
        ]
