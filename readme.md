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

Testy: `uv run pytest`. Podrobnosti: [provoz](doc/provoz.md),
[userdb API](doc/userdb-api.md). Python ≥ 3.12, závislosti spravuje `uv` v `.venv`.
