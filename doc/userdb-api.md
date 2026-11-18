# userdb API pro identifikaci podle IP

Podkladem je původní `userdb-api-example.txt` (uživatel jej označil jako
`userdb-api-example.php`). Ukázka byla po převodu odstraněna. Tento návod popisuje
jen doložené operace; není úplnou dokumentací userdb API.

Základní URL: `https://userdb.hkfree.org/userdb/api`. Oba požadavky používají
HTTP Basic Auth, přihlašovací jméno a heslo jsou v `.env` pod
`USERDB_API_USERNAME` a `USERDB_API_PASSWORD`. Volat výhradně přes HTTPS.

1. `GET /uzivatel/get-uzivatelby-ip/{ip}` vrací při HTTP 200 například
   `{"result":"OK","Uzivatel_id":42}`.
   HTTP 404 a `{"result":"User for IP address not found"}` znamenají nenalezeného člena.
2. `GET /uzivatel/get-uzivatel/{id}` vrací při HTTP 200 objekt `uzivatel`:

   ```json
   {
     "result": "OK",
     "uzivatel": {
       "jmeno": "Jana",
       "prijmeni": "Nová",
       "email": "jana@example.org"
     }
   }
   ```

   Odpověď obsahuje i další údaje, které aplikace nepotřebuje a nepředává dál.
   HTTP 404 a `{"result":"User ID not found"}` znamenají neexistující ID.

Mapování do SledovaniTV: `Uzivatel_id` → `partnerid`, `email` → `email`,
`jmeno + " " + prijmeni` → `fullName`. IP pochází ze spojení návštěvníka.
Chyby autentizace, nedostupnost a neplatné odpovědi se zobrazují jako výpadek,
nikoli jako nenalezený člen. Aplikace nemá přímé připojení do databáze.
