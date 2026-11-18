from unittest.mock import Mock

import pytest
import requests

from app import create_app


@pytest.fixture
def client():
    app = create_app({
        'TESTING': True,
        'USERDB_API_USERNAME': 'test-user',
        'USERDB_API_PASSWORD': 'test-userdb-secret',
        'SLEDOVANITV_PASSWORD': 'test-tv-secret',
    })
    return app.test_client()


def reply(data, status=200):
    return Mock(status_code=status, json=Mock(return_value=data))


def user_responses(email='clen@example.org'):
    return [reply({'result': 'OK', 'Uzivatel_id': 42}),
            reply({'result': 'OK', 'uzivatel': {
                'email': email, 'jmeno': 'Jiří', 'prijmeni': 'Černý',
            }})]


def mock_api(monkeypatch, responses):
    get = Mock(side_effect=responses)
    monkeypatch.setattr('app.requests.get', get)
    return get


def test_redirect_and_api_contract(client, monkeypatch):
    get = mock_api(monkeypatch, user_responses() + [reply({
        'status': True, 'url': 'https://sledovanitv.cz/login?token=abc',
    })])
    response = client.get('/', environ_overrides={'REMOTE_ADDR': '10.107.1.2'},
                          headers={'X-Forwarded-For': '10.107.9.9'})
    assert response.status_code == 303
    assert response.headers['Location'] == 'https://sledovanitv.cz/login?token=abc'
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    calls = get.call_args_list
    assert calls[0].args[0].endswith('/uzivatel/get-uzivatelby-ip/10.107.1.2')
    assert calls[1].args[0].endswith('/uzivatel/get-uzivatel/42')
    assert calls[0].kwargs['auth'] == ('test-user', 'test-userdb-secret')
    assert calls[2].args[0] == 'https://sledovanitv.cz/partner/api/identifyuser'
    assert calls[2].kwargs['params'] == {
        'partnerid': 42, 'email': 'clen@example.org', 'fullName': 'Jiří Černý',
        'partner': 'hkfree', 'password': 'test-tv-secret', 'ip': '10.107.1.2',
    }
    assert 'auth' not in calls[2].kwargs or calls[2].kwargs['auth'] is None
    assert all(call.kwargs['timeout'] == 5 for call in calls)
    assert all(call.kwargs['allow_redirects'] is False for call in calls)


@pytest.mark.parametrize('detail_missing', [False, True])
def test_user_not_found(client, monkeypatch, detail_missing):
    responses = [reply({'result': 'User for IP address not found'}, 404)]
    if detail_missing:
        responses = [user_responses()[0], reply({'result': 'User ID not found'}, 404)]
    get = mock_api(monkeypatch, responses)
    response = client.get('/')
    assert response.status_code == 403
    assert 'nepodařilo identifikovat' in response.text
    assert get.call_count == len(responses)


def test_login_used_escapes_email(client, monkeypatch):
    mock_api(monkeypatch, user_responses('<script>alert(1)</script>') + [
        reply({'status': False, 'error': 'login used'})])
    response = client.get('/')
    assert response.status_code == 409
    assert 'Login již existuje' in response.text
    assert '<script>' not in response.text
    assert '&lt;script&gt;' in response.text


@pytest.mark.parametrize('failure', [
    requests.Timeout('URL with test-userdb-secret'),
    requests.ConnectionError('URL with test-userdb-secret'),
    reply({}, 401), reply({}, 500), reply({}, 302), reply([]),
    reply({'result': 'OK', 'Uzivatel_id': '../oops'}),
    Mock(status_code=200, json=Mock(side_effect=ValueError('bad json'))),
])
def test_userdb_errors_are_safe(client, monkeypatch, caplog, failure):
    mock_api(monkeypatch, [failure])
    response = client.get('/')
    assert response.status_code == 503
    assert 'dočasně mimo provoz' in response.text
    assert 'test-userdb-secret' not in response.text + caplog.text


@pytest.mark.parametrize('failure', [
    requests.Timeout('URL with test-tv-secret'), reply({}, 500),
    reply({'status': False, 'error': 'other'}), reply(None),
    reply({'status': True}),
    reply({'status': True, 'url': 'javascript:alert(1)'}),
    reply({'status': True, 'url': '//sledovanitv.cz/login'}),
    reply({'status': True, 'url': 'https://sledovanitv.cz/\r\nX-Evil:1'}),
])
def test_tv_errors_are_safe(client, monkeypatch, caplog, failure):
    mock_api(monkeypatch, user_responses() + [failure])
    response = client.get('/')
    assert response.status_code == 503
    assert 'test-tv-secret' not in response.text + caplog.text


def test_invalid_ip_does_not_call_api(client, monkeypatch):
    get = mock_api(monkeypatch, [])
    response = client.get('/', environ_overrides={'REMOTE_ADDR': 'invalid'})
    assert response.status_code == 400
    get.assert_not_called()


def test_ipv6(client, monkeypatch):
    get = mock_api(monkeypatch, [reply({}, 404)])
    response = client.get('/', environ_overrides={'REMOTE_ADDR': '2001:db8::1'})
    assert response.status_code == 403
    assert get.call_args.args[0].endswith('/get-uzivatelby-ip/2001:db8::1')


def test_missing_password_fails_at_startup():
    with pytest.raises(ValueError, match='SLEDOVANITV_PASSWORD'):
        create_app({'USERDB_API_USERNAME': 'test', 'USERDB_API_PASSWORD': 'test',
                    'SLEDOVANITV_PASSWORD': ''})
