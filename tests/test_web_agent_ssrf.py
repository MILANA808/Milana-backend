from app.api import web_agent


def _answers(ip: str):
    return [(None, None, None, None, (ip, 443))]


def test_public_url_rejects_loopback_and_private_literals():
    assert not web_agent.public_url("http://127.0.0.1:8000/")
    assert not web_agent.public_url("http://10.0.0.8/")
    assert not web_agent.public_url("http://169.254.169.254/latest/meta-data/")


def test_public_url_rejects_credentials_and_non_http():
    assert not web_agent.public_url("https://user:pass@example.com/")
    assert not web_agent.public_url("file:///etc/passwd")
    assert not web_agent.public_url("http://localhost/")


def test_public_url_allows_public_host(monkeypatch):
    monkeypatch.setattr(web_agent.socket, "getaddrinfo", lambda *a, **k: _answers("93.184.216.34"))
    assert web_agent.public_url("https://example.com/")


def test_public_url_rejects_host_resolving_private(monkeypatch):
    monkeypatch.setattr(web_agent.socket, "getaddrinfo", lambda *a, **k: _answers("192.168.1.5"))
    assert not web_agent.public_url("https://attacker.example/")


def test_public_url_fails_closed_on_mixed_dns_answers(monkeypatch):
    monkeypatch.setattr(
        web_agent.socket,
        "getaddrinfo",
        lambda *a, **k: _answers("93.184.216.34") + _answers("10.0.0.4"),
    )
    assert not web_agent.public_url("https://mixed.example/")
