# Kontejnery a GitHub Actions

## Image

`Dockerfile` používá Python 3.12 slim a dvoufázový build. Builder instaluje
přes uv 0.11.29 do `.venv` pouze produkční závislosti podle `uv.lock`.
Výsledný image obsahuje prostředí, aplikaci a šablony; server běží jako
uživatel `10001:10001` na `0.0.0.0:8080`. Při startu se závislosti neinstalují.

`.dockerignore` povoluje pouze soubory nutné k sestavení. `.env`, lokální
`.venv`, Git, testy a dočasné soubory editoru se do build kontextu neposílají.
Přihlašovací údaje nejsou potřeba při buildu a patří až do prostředí kontejneru.

## CI a publikování

Workflow `.github/workflows/container.yml` reaguje na push a pull request:

1. V Pythonu 3.12 nainstaluje zamčené závislosti, spustí pytest a ověří Compose.
2. Po úspěšných testech sestaví image pro `linux/amd64`.
3. Spustí image s testovacími přístupy a ověří HTTP server na portu 4251.
   Kontroluje HTTP 404 na neexistující cestě, takže nevolá živá API.
4. Pouze při pushi publikuje tento ověřený image do `ghcr.io/<owner>/<repo>`.
   Název je odvozený z repozitáře a převedený na malá písmena.

Tagy: název větve, tag z Gitu nebo `pr-<číslo>`, dále `sha-<celý commit SHA>`.
`latest` se aktualizuje pouze při pushi na výchozí větev. Pull requesty se
nepublikují. Actions jsou připnuté na konkrétní commity; uv má stejnou verzi
v CI i Dockerfile. Workflow nepotřebuje přístupy k userdb ani SledovaniTV.

Publikování používá automatický `GITHUB_TOKEN` s oprávněním `packages: write`.
V repozitáři musí být povolené GitHub Actions a publikování balíčků. U existujícího
GHCR balíčku ověřte oprávnění příslušného repozitáře zapisovat do balíčku.
Pro anonymní stahování nastavte balíčku veřejnou viditelnost; jinak se cílový
stroj musí přihlásit přes `docker login ghcr.io` účtem/tokenem s právem čtení balíčku.

## Cílový stroj

Stačí Docker Engine s Compose, `compose.yaml` a `.env` ve stejné složce.
Není potřeba checkout zdrojových souborů ani Python/uv na hostiteli.
V `.env` nastavte přístupy z `.env.example` a adresu image, například:

```dotenv
APP_IMAGE=ghcr.io/organizace/hkfree_tv:latest
BIND_ADDRESS=0.0.0.0
```

```sh
docker compose pull
docker compose up -d
docker compose logs --tail=100 app
```

Stejné první dva příkazy použijte při aktualizaci. Pro nasazení konkrétní verze
nebo návrat na předchozí nastavte `APP_IMAGE` s tagem `sha-<celý commit SHA>`.
Deployment na cílový stroj probíhá ručně; CI publikuje pouze image.

Compose publikuje `4251:8080`, restartuje službu po pádu a po restartu Dockeru
(pokud nebyla ručně zastavená) a spouští ji se souborovým systémem jen pro čtení
a bez Linux capabilities. `HOST` a `PORT` z aplikačního `.env` přepisuje na
`0.0.0.0` a `8080`, aby se zachovalo mapování portů.

`BIND_ADDRESS` určuje adresu hostitele, výchozí `0.0.0.0` zpřístupňuje port 4251
na všech IPv4 rozhraních. Za reverzní proxy na stejném hostiteli nastavte
`BIND_ADDRESS=127.0.0.1`. Pro identifikaci musí aplikace vidět skutečnou IP člena:
při použití proxy nastavte `TRUSTED_PROXY` na IP, ze které se proxy skutečně
připojuje **uvnitř kontejneru** (může jít o adresu Docker gateway, nikoli
`127.0.0.1`). Proxy musí správně nastavovat `X-Forwarded-For`. Podrobnosti
jsou v [provozní dokumentaci](provoz.md#ip-návštěvníka-a-proxy).

Příkazy `docker compose config` bez `--quiet` a `docker inspect` mohou zobrazit
hodnoty z prostředí; jejich výstup s přístupy nezveřejňujte.

Podklady: [uv v Dockeru](https://docs.astral.sh/uv/guides/integration/docker/),
[publikování image na GitHubu](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images),
[konfigurace Compose](https://docs.docker.com/reference/compose-file/services/).
