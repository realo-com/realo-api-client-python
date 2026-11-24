import json

import pytest

from realo_api import DEFAULT_USER_AGENT, RealoApi, RealoApiException, TransportResponse

# Expected values generated independently with the OpenSSL CLI (php is not installed):
#   printf '<base string>' | openssl dgst -sha256 -hmac secret -binary | base64
# which is exactly PHP's base64_encode(hash_hmac('sha256', $base, $key, true)).
GET_SIG = "/7DN6s0o9ArdMT5Rfud4VSf0IbfAEIfb9/ekJD90mBM="
POST_SIG = "F2u5RYPhFW6asRMNls0cZ2lTbJ8vZgf6M46+zQ003Yg="


class FakeTransport:
    def __init__(self, status=200, content_type="application/json", body=b"{}"):
        self.response = TransportResponse(status, {"Content-Type": content_type}, body)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, headers, body))
        return self.response


def make(**kw):
    t = FakeTransport(**kw)
    return RealoApi.create_with_transport("pub", "secret", t), t


def test_get_without_body_signature_and_headers():
    api, t = make()
    assert api.request("/agencies") == {}
    method, url, headers, body = t.calls[0]
    assert (method, url, body) == ("GET", "https://api.realo.com/1.0/agencies", None)
    assert headers["Authorization"] == 'Realo key="pub", version="1.0", signature="%s"' % GET_SIG
    assert headers["Content-Type"] == "application/json"
    assert headers["User-Agent"] == DEFAULT_USER_AGENT
    assert DEFAULT_USER_AGENT.startswith("RealoApiClient-Python/")


def test_post_with_body_signs_exact_sent_bytes():
    api, t = make()
    api.request("agencies", "post", {"a": 1}, {"X-Custom": "1"})
    method, url, headers, body = t.calls[0]
    assert method == "POST" and body == b'{"a":1}'
    assert headers["Authorization"].endswith('signature="%s"' % POST_SIG)
    assert headers["X-Custom"] == "1"


def test_signed_body_matches_sent_body_with_unicode():
    api, t = make()
    api.request("x", "POST", {"name": "Zoë/é"})
    _, url, headers, body = t.calls[0]
    assert api.sign("POST", url, body.decode("utf-8")) == headers["Authorization"]
    assert json.loads(body) == {"name": "Zoë/é"}


def test_sandbox_environment():
    t = FakeTransport()
    api = RealoApi.create_with_transport("p", "s", t, "sandbox")
    api.request("/a")
    assert t.calls[0][1] == "https://api-sandbox.realo.com/1.0/a"


def test_invalid_environment():
    with pytest.raises(ValueError, match=r"production, sandbox"):
        RealoApi.create("p", "s", "nope")


def test_json_response_parsed():
    api, _ = make(content_type="application/json; charset=utf-8", body=b'{"data": [1]}')
    assert api.request("a") == {"data": [1]}


def test_non_json_response_returns_bytes():
    api, _ = make(content_type="image/png", body=b"\x89PNG")
    assert api.request("a") == b"\x89PNG"


def test_error_with_errors_body():
    body = json.dumps({"errors": [{"type": "NotFound", "message": "nope"}]}).encode()
    api, _ = make(status=404, body=body)
    with pytest.raises(RealoApiException) as ei:
        api.request("a")
    e = ei.value
    assert e.code == 404 and e.type == "NotFound"
    assert e.errors == [{"type": "NotFound", "message": "nope"}]
    assert str(e) == "NotFound: nope"


@pytest.mark.parametrize("body", [b"{}", b'{"errors": []}', b"not json", b""])
def test_error_without_usable_errors(body):
    api, _ = make(status=500, body=body)
    with pytest.raises(RealoApiException) as ei:
        api.request("a")
    assert ei.value.code == 500 and not ei.value.errors and ei.value.type is None


def test_error_non_json_content_type():
    api, _ = make(status=502, content_type="text/html", body=b"<html>")
    with pytest.raises(RealoApiException) as ei:
        api.request("a")
    assert ei.value.errors is None and ei.value.code == 502


def test_transport_error():
    def boom(*a):
        raise ConnectionError("down")

    api = RealoApi.create_with_transport("p", "s", boom)
    with pytest.raises(RealoApiException) as ei:
        api.request("a")
    assert "down" in str(ei.value) and ei.value.errors is None
