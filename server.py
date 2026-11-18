"""Spusteni produkcniho WSGI serveru."""

import ipaddress
import os

from waitress import serve

from app import create_app


def main():
    app = create_app()
    proxy = os.getenv('TRUSTED_PROXY', '').strip()
    options = {}
    if proxy:
        ipaddress.ip_address(proxy)
        options.update(trusted_proxy=proxy, trusted_proxy_count=1,
                       trusted_proxy_headers={'x-forwarded-for'})
    serve(app, host=os.getenv('HOST', '127.0.0.1'),
          port=int(os.getenv('PORT', '8080')), **options)


if __name__ == '__main__':
    main()
