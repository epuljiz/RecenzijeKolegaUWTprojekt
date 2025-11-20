**RecenzijeKolegaUWTprojekt**

Kratki opis
-
Ovo je jednostavna web-aplikacija za pisanje i pregled recenzija kolega (studentskih projekata). Aplikacija koristi Flask kao web-framework, MongoDB (pomoću Flask-PyMongo) za pohranu podataka, te pruža osnovne značajke za registraciju, prijavu, upravljanje korisnicima, dodavanje recenzija i administratorski panel.

Glavne značajke
-
- Registracija i prijava korisnika (hashirane lozinke)
- Verifikacija emaila (opcionalno, ovisno o konfiguraciji mail servisa)
- CRUD operacije nad recenzijama (dodavanje, uređivanje, brisanje)
- Administratorski panel za upravljanje korisnicima i recenzijama
- Rate-limiting za osjetljive rute

Tehnologije
-
- Python 3.x
- Flask
- Flask-PyMongo
- Flask-Login, Flask-Principal
- Flask-Mail
- MongoDB / Mongo Atlas

Brzi početak (lokalno)
-
1. Kloniraj repozitorij i uđi u direktorij projekta:

```powershell
cd C:\put\do\projekta\RecenzijeKolegaUWTprojekt
```

2. Kreiraj i aktiviraj virtualno okruženje (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Postavi varijable okoline (primjer: u `.env` ili u Render/servis gdje hostaš):

- `MONGO_URI` — MongoDB connection string (npr. Mongo Atlas)
- `SECRET_KEY` — tajni ključ za Flask sesije
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` — ako želiš koristiti slanje emailova

Primjer lokalnog pokretanja (development):

```powershell
# PowerShell
$env:FLASK_ENV = 'development'
$env:MONGO_URI = 'mongodb://localhost:27017/kolegarecenzije'
python run.py
```

Konfiguracija (važna okruženja)
-
- `MONGO_URI`: obavezno postaviti kada koristite Atlas ili udaljeni Mongo.
- `SECRET_KEY`: postavite snažan, nasumičan ključ u produkciji.
- `MAIL_*`: ako šaljete verifikacijske mailove — provjerite pristup SMTP serveru.

Napomene za Deploy (Render / Mongo Atlas)
-
- Ako koristite Mongo Atlas, provjerite Network Access (IP whitelist). Render koristi dinamičke egress IP adrese — kao privremeno rješenje za testiranje možete otvoriti pristup sa `0.0.0.0/0`, ali to nije preporučeno u produkciji. Bolji pristup je konfiguracija VPC/VNet ili korištenje specifičnog servisa koji Render preporuča.
- Postavite sve potrebne env varijable u Render Dashboard → Environment.

Struktura projekta (ključne mape/datoteke)
-
- `run.py` — entry point aplikacije
- `config.py` — konfiguracijske klase i varijable
- `requirements.txt` — popis Python paketa
- `app/` — glavni paket aplikacije
	- `__init__.py` — app factory, registracija blueprinta i ekstenzija
	- `extensions.py` — inicijalizacija ekstenzija (mongo, login, mail, principal, limiter)
	- `models.py` — korisnički model i pomoćne metode
	- `auth/` — registracija, login, forme, utilsi
	- `admin/` — administratorske rute i viewovi
	- `reviews/`, `profile/`, `main/` — ostali moduli i rute
	- `templates/` — Jinja2 šablone
	- `static/` — css i js statički resursi

Korisne naredbe za razvoj
-
- Instalacija dependencyja: `pip install -r requirements.txt`
- Pokretanje aplikacije: `python run.py`
- Pokretanje jednostavnog Mongo konekt testa (Python repl):

```powershell
python - <<'PY'
from pymongo import MongoClient
uri = 'TVOJ_MONGO_URI'
client = MongoClient(uri, serverSelectionTimeoutMS=5000)
try:
		print(client.server_info())
		print('Connected OK')
except Exception as e:
		print('Connect error:', e)
PY
```

---
_Ovaj README daje kratak pregled kako brzo pokrenuti i razumjeti strukturu projekta. Za detaljne upute vezane uz razvoj, testiranje ili produkciju, preporučam dodati odvojene sekcije prema potrebama._