# Provoz

## Konfigurace a spuštění

Používejte Python ≥ 3.12 a `uv sync --locked`. `uv` vytvoří `.venv`; závislosti
neinstalujte globálně. Produkční server Waitress spustíte `uv run python server.py`.
Pro instalaci bez testovacích závislostí použijte `uv sync --locked --no-dev`
a `uv run --no-dev python server.py`.

`.env` se načítá ze složky projektu; již nastavené proměnné prostředí mají přednost.
Soubor nepatří do Gitu. Pro novou instalaci použijte `.env.example`; existující
lokální `.env` nepřepisujte, obsahuje přenesené přístupy userdb. Přístupová práva
nastavte na `600`. Před prvním spuštěním doplňte `SLEDOVANITV_PASSWORD`.
Chybějící přihlašovací údaj způsobí srozumitelnou chybu při startu.

| Proměnná | Význam / výchozí hodnota |
| --- | --- |
| `USERDB_API_URL` | `https://userdb.hkfree.org/userdb/api` |
| `USERDB_API_USERNAME`, `USERDB_API_PASSWORD` | Basic Auth pro userdb |
| `SLEDOVANITV_API_URL` | `https://sledovanitv.cz/partner/api` |
| `SLEDOVANITV_PARTNER` | `hkfree` |
| `SLEDOVANITV_PASSWORD` | Heslo partnera, nutno doplnit |
| `HTTP_TIMEOUT` | `5` sekund pro připojení i čekání na data každého požadavku |
| `HOST`, `PORT` | `127.0.0.1`, `8080` |
| `TRUSTED_PROXY` | IP jediné důvěryhodné reverzní proxy, výchozí prázdné |

## IP návštěvníka a proxy

Identifikace vychází z `REMOTE_ADDR`. Ve výchozím nastavení server ignoruje
`X-Forwarded-For`. Pokud je před aplikací jedna reverzní proxy, nastavte
`TRUSTED_PROXY` na její konkrétní IP a zajistěte, aby proxy nastavovala
`X-Forwarded-For` na skutečnou IP klienta. Pro lokální proxy to bývá `127.0.0.1`
(ověřte skutečnou adresu spojení). Waitress důvěřuje jednomu proxy hopu a pouze
této hlavičce. Nepovolujte přímý veřejný přístup k backendu při provozu za proxy.
Více proxy za sebou vyžaduje přizpůsobení konfigurace a ověření předávané IP.

## Tok a chybové stavy

`GET /` provede dva požadavky na userdb a poté
`GET https://sledovanitv.cz/partner/api/identifyuser` s parametry `partnerid`,
`email`, `fullName`, `partner`, `password`, `ip`. Tento kontrakt vychází z původní
PHP aplikace. JSON s pravdivým `status` a HTTPS `url` vede na HTTP 303.
Adresu přesměrování dodává důvěryhodné API SledovaniTV.

Nenalezený uživatel vrátí HTML s HTTP 403, `error: "login used"` s HTTP 409,
výpadek nebo vadná odpověď API s HTTP 503 a vadná IP s HTTP 400. Původní PHP
chybové stránky vracely HTTP 200; nový kód rozlišuje stavy. České šablony používají
automatické escapování. Všechny odpovědi mají `Cache-Control: no-store`
a `Referrer-Policy: no-referrer`.

Požadavky nepokračují přes HTTP přesměrování a automaticky se neopakují.
Chybové logy aplikace neobsahují URL API, hesla, odpovědi API ani osobní údaje.
Partnerské API podle původního kontraktu přijímá heslo v query stringu;
nezapínejte ladicí HTTP logování s URL požadavků.

## Ověření

`uv run pytest` ověřuje tok přihlášení, parametry API, HTTP 303, chybové stavy,
escapování, IPv6 a ignorování podvržené IP hlavičky bez důvěryhodné proxy.
Testy simulují odpovědi API a nevolají skutečné služby.
Přihlášení do SledovaniTV lze provozně ověřit až po doplnění hesla a z IP člena.
