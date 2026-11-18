# hkfree TV

Malá aplikace ve Flasku: podle IP návštěvníka vyhledá člena přes userdb API,
přihlásí ho partnerským API SledovaniTV a přesměruje odpovědí HTTP 303.

Konfigurace se načítá z `.env` nebo proměnných prostředí; přehled nastavení
obsahuje `.env.example`.

```sh
uv sync --locked
uv run python server.py
```

Výchozí adresa je `http://127.0.0.1:8080/`.

Pro Docker Compose nastavte v `.env` také `APP_IMAGE` a spusťte
`docker compose up -d`. Aplikace bude dostupná na portu `4251`.
GitHub Actions po testech sestaví image a při pushi jej publikuje do GHCR.

Testy: `uv run pytest`. Podrobnosti: [provoz](doc/provoz.md),
[kontejnery a CI](doc/kontejnery.md), [userdb API](doc/userdb-api.md).
Python ≥ 3.12, závislosti spravuje `uv` v `.venv`.
