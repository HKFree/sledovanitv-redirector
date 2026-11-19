# Pokyny pro práci v projektu

- Aplikace identifikuje návštěvníka podle IP přes userdb API a přesměrovává
  na SledovaniTV. Zachovej mapování a HTTP 303; kontrakty jsou v `doc/`.
- Používej Python ≥ 3.12, Flask/Jinja a Waitress. Udržuj aplikaci malou;
  nepřidávej databázi, frontendový build ani framework bez konkrétní potřeby.
- Projekt a závislosti spravuj přes `uv`, výhradně v `.venv`.
  Změny závislostí zapisuj do `pyproject.toml` i `uv.lock`.
- Tajné údaje patří pouze do `.env` nebo prostředí. Nikdy je nezapisuj do
  dokumentace, testů, URL v logu ani commitu. `.env.example` musí zůstat bez hesel.
- userdb používej pouze přes API, nikoli přímými SQL dotazy. Neposílej další
  osobní údaje nad rámec původního kontraktu bez požadavku uživatele.
- Nedůvěřuj IP v HTTP hlavičkách bez explicitně nastavené důvěryhodné proxy.
  Síťová volání musí mít timeout a ověřování TLS; šablony automatické escapování.
- Při změnách identifikace a API spusť `uv run pytest`. Testy nesmí volat živá API
  ani používat skutečná hesla. Upravuj testy podle změn chování, nikoli kosmetiky.
- `readme.md` udržuj stručný, provozní a API detaily ukládej do `doc/`.
- Texty pro návštěvníky a dokumentaci piš česky v UTF-8.
- Kontejnery a CI popisuje `doc/kontejnery.md`. Do image ani build kontextu
  nepřidávej `.env`. Udržuj stejnou verzi uv a Pythonu v Dockerfile a CI.
- Compose používá host networking na Linuxu: aplikace poslouchá na
  `127.0.0.1:4251` a důvěřuje nginxu z `127.0.0.1`. Zachovej stejné nastavení v CI.
- Docker v tomto pracovním prostředí nespouštěj. Build a běh kontejneru ověřuje
  GitHub Actions; lokálně kontroluj konfiguraci staticky a spusť Python testy.
