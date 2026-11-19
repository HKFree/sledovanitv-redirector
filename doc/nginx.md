# Nginx před aplikací

Ukázka [nginx.conf](nginx.conf) předpokládá nginx přímo na stejném Linux
hostiteli jako Docker Compose. Klient se připojuje přímo k nginxu; mezi nimi
není CDN ani další proxy. Nginx ukončuje HTTPS a předává požadavky na
`http://127.0.0.1:4251`.

## Spuštění aplikace

[`compose.yaml`](../compose.yaml) používá host networking. Kontejner sdílí síť hostitele,
aplikace poslouchá pouze na `127.0.0.1:4251` a důvěřuje proxy `127.0.0.1`.
Docker gateway ani její případné přečíslování se tohoto spojení neúčastní.
Kontejner tím sdílí i přístup k ostatním síťovým službám hostitele.
Nasazení je určené pro běžný Docker Engine na Linuxu; na rootless Dockeru
nebo Docker Desktopu je potřeba vlastnosti host networking ověřit zvlášť.

Na cílovém serveru:

```sh
docker compose pull
docker compose up -d --force-recreate app
```

Při přechodu zachovejte stejný adresář a název Compose projektu, aby se existující
služba `app` znovu vytvořila ve správném projektu.

Do `.env` není potřeba hodnotu `TRUSTED_PROXY` doplňovat: Compose
nastavuje `HOST=127.0.0.1`, `PORT=4251` a `TRUSTED_PROXY=127.0.0.1` přímo
v `environment`, což má přednost před `.env`. Přístupy k API a `APP_IMAGE`
zůstávají v `.env`.
Ukázková konfigurace nginxu platí beze změny.

`TRUSTED_PROXY=0.0.0.0/0` aplikace nepřijímá: podporuje jednu konkrétní IP.
Samotný Waitress nabízí wildcard `*`, ale aplikace jej záměrně nepovoluje.
Důvěra všem protistranám by umožnila každému, kdo dosáhne na backend, určit IP
pro identifikaci uživatele pomocí podvržené hlavičky. Compose ponechává
jednu konkrétní důvěryhodnou adresu.

## Nastavení nginxu

V konfiguraci nahraďte `tv.example.org` vlastní doménou a upravte cesty
k existujícímu TLS certifikátu a klíči. Soubor vložte do konfigurace načítané
uvnitř `http {}`. Například na Debianu/Ubuntu:

```sh
sudo cp doc/nginx.conf /etc/nginx/sites-available/hkfree-tv.conf
sudo ln -s /etc/nginx/sites-available/hkfree-tv.conf /etc/nginx/sites-enabled/hkfree-tv.conf
sudo nginx -t
sudo systemctl reload nginx
```

Doménu a cesty upravte před `nginx -t`. Příkazy provádějte na cílovém serveru.
Certifikát se touto ukázkou nevystavuje ani neobnovuje; pro ACME HTTP challenge
použijte konfiguraci svého správce certifikátů.

Nginx přepisuje `X-Forwarded-For` hodnotou `$remote_addr`, takže klient nemůže
podvrhnout IP vlastní hlavičkou. Aplikace důvěřuje jednomu proxy hopu a používá
pouze tuto hlavičku. Pokud je před nginxem další proxy, je nejprve nutné vyřešit
zjišťování skutečné IP na nginxu; tato ukázka takovou topologii nepokrývá.

Změna `.env` vyžaduje znovuvytvoření kontejneru; samotný `docker compose restart`
nové proměnné prostředí nenačte.

Podklady: [nginx proxy modul](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
[Waitress: nastavení důvěryhodné proxy](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html),
[Docker: host networking](https://docs.docker.com/engine/network/drivers/host/).
