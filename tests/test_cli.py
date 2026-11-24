import json

import pytest

from realo_api import RealoApi, TransportResponse
from realo_api.cli import main

BASE = ["--public-key", "p", "--private-key", "s"]


def api_for(status, content_type, body):
    calls = []

    def t(method, url, headers, b):
        calls.append((method, url, b))
        return TransportResponse(status, {"Content-Type": content_type}, body)

    return RealoApi.create_with_transport("p", "s", t), calls


def test_json_output(capsys):
    api, calls = api_for(200, "application/json", b'{"a": "\xc3\xa9/"}')
    assert main(BASE + ["-m", "POST", "-b", '{"x": 1}', "/things"], api=api) == 0
    assert calls == [("POST", "https://api.realo.com/1.0/things", b'{"x":1}')]
    assert json.loads(capsys.readouterr().out) == {"a": "é/"}


def test_non_json_needs_force(capsys):
    api, _ = api_for(200, "image/png", b"BIN")
    assert main(BASE + ["/x"], api=api) == 0
    out = capsys.readouterr()
    assert out.out == "" and "-f" in out.err
    assert main(BASE + ["-f", "/x"], api=api) == 0
    assert capsys.readouterr().out == "BIN"


def test_error_with_errors(capsys):
    api, _ = api_for(400, "application/json", b'{"errors":[{"type":"T","message":"m"}]}')
    assert main(BASE + ["/x"], api=api) == 1
    assert json.loads(capsys.readouterr().out) == {"errors": [{"type": "T", "message": "m"}]}


def test_error_without_errors(capsys):
    api, _ = api_for(500, "text/plain", b"boom")
    assert main(BASE + ["/x"], api=api) == 1
    assert capsys.readouterr().err.startswith("Error 500: ")


def test_invalid_body_and_environment(capsys):
    assert main(BASE + ["-b", "{bad", "/x"]) == 1
    assert main(BASE + ["-e", "nope", "/x"]) == 1
    assert "production, sandbox" in capsys.readouterr().err


def test_missing_args():
    with pytest.raises(SystemExit) as ei:
        main(["/x"])
    assert ei.value.code == 2
