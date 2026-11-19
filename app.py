"""Identifikace clena hkfree a prihlaseni do SledovaniTV."""

import ipaddress
import math
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request


class UpstreamError(Exception):
    """API nevratilo pouzitelnou odpoved."""


def client_ip():
    return str(ipaddress.ip_address(request.remote_addr or ''))


def get_json(url, timeout, *, auth=None, params=None, missing_ok=False):
    # Neprebijet chyby API nasledovanim presmerovani s osobnimi udaji.
    response = requests.get(
        url, auth=auth, params=params, timeout=timeout, allow_redirects=False
    )
    if missing_ok and response.status_code == 404:
        return None
    if response.status_code != 200:
        raise UpstreamError()
    data = response.json()
    if not isinstance(data, dict):
        raise UpstreamError()
    return data


def identify_user(config, ip):
    base = config['USERDB_API_URL'].rstrip('/')
    auth = (config['USERDB_API_USERNAME'], config['USERDB_API_PASSWORD'])
    options = dict(auth=auth, timeout=config['HTTP_TIMEOUT'], missing_ok=True)
    found = get_json(f'{base}/uzivatel/get-uzivatelby-ip/{ip}', **options)
    if found is None:
        return None
    user_id = found.get('Uzivatel_id')
    if found.get('result') != 'OK' or type(user_id) is not int or user_id <= 0:
        raise UpstreamError()
    detail = get_json(f'{base}/uzivatel/get-uzivatel/{user_id}', **options)
    if detail is None:
        return None
    user = detail.get('uzivatel')
    if detail.get('result') != 'OK' or not isinstance(user, dict):
        raise UpstreamError()
    fields = [user.get(key) for key in ('email', 'jmeno', 'prijmeni')]
    if not all(isinstance(value, str) for value in fields):
        raise UpstreamError()
    email, first_name, last_name = fields
    return dict(partnerid=user_id, email=email, fullName=f'{first_name} {last_name}'.strip())


def create_app(overrides=None):
    load_dotenv(Path(__file__).with_name('.env'))
    app = Flask(__name__)
    defaults = {
        'USERDB_API_URL': 'https://userdb.hkfree.org/userdb/api',
        'USERDB_API_USERNAME': '',
        'USERDB_API_PASSWORD': '',
        'SLEDOVANITV_API_URL': 'https://sledovanitv.cz/partner/api',
        'SLEDOVANITV_PARTNER': 'hkfree',
        'SLEDOVANITV_PASSWORD': '',
        'HTTP_TIMEOUT': '5',
    }
    app.config.update({key: os.getenv(key, default) for key, default in defaults.items()})
    app.config.update(overrides or {})
    for key in defaults:
        if not str(app.config[key]).strip():
            raise ValueError(f'Chybi konfigurace {key}; doplnte .env.')
    timeout = float(app.config['HTTP_TIMEOUT'])
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('HTTP_TIMEOUT musi byt kladne konecne cislo.')
    app.config['HTTP_TIMEOUT'] = timeout
    for key in ('USERDB_API_URL', 'SLEDOVANITV_API_URL'):
        url = urlsplit(app.config[key])
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError(f'{key} musi byt HTTPS URL bez prihlasovacich udaju, dotazu a fragmentu.')

    @app.after_request
    def private_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.get('/ip')
    def diagnostic_ip():
        try:
            return app.response_class(client_ip() + '\n', mimetype='text/plain')
        except ValueError:
            return app.response_class('Neplatná IP adresa.\n', status=400, mimetype='text/plain')

    @app.get('/')
    def login():
        try:
            ip = client_ip()
        except ValueError:
            return render_template('error.html', reason='unidentified', ip='neznamá'), 400
        try:
            info = identify_user(app.config, ip)
            if info is None:
                return render_template('error.html', reason='unidentified', ip=ip), 403
            result = get_json(
                app.config['SLEDOVANITV_API_URL'].rstrip('/') + '/identifyuser',
                app.config['HTTP_TIMEOUT'],
                params={**info, 'partner': app.config['SLEDOVANITV_PARTNER'],
                        'password': app.config['SLEDOVANITV_PASSWORD'], 'ip': ip},
            )
            if result.get('status'):
                target = result.get('url')
                if not isinstance(target, str) or any(ord(c) < 33 or ord(c) == 127 for c in target):
                    raise UpstreamError()
                parsed = urlsplit(target)
                if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                    raise UpstreamError()
                return redirect(target, code=303)
            if result.get('error') == 'login used':
                return render_template('error.html', reason='login_used', ip=ip, email=info['email']), 409
            raise UpstreamError()
        except (requests.RequestException, ValueError, UpstreamError):
            # Vyjimky requests mohou obsahovat URL s heslem; nelogovat jejich text.
            app.logger.warning('Identifikace selhala pri komunikaci s API.')
            return render_template('error.html', reason='unavailable', ip=ip), 503

    return app
