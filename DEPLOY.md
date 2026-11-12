# Deploy guide (Heroku / Railway / VPS)

Pehle in variables ki zarurat padegi (sample.env me poori list hai):
`API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGO_DB_URI`, `OWNER_ID`, `LOGGER_ID`, `STRING_SESSION`.

> Important: `MONGO_DB_URI` ab zaroori hai. Pehle bina URI ke bot kisi aur ke database me data likhta tha, wo hata diya gaya hai.
> `AUTO_PULL_UPSTREAM=False` (default) rakho, warna bot start par `UPSTREAM_REPO` ka purana code pull karke is fixed code ko overwrite kar dega.

## Heroku
1. Is folder ko apne GitHub repo me push karo.
2. Heroku dashboard me new app banao, Settings me stack ko **container** karo (`app.json` me already set hai).
3. Config Vars me upar wale variables daalo.
4. Deploy tab se GitHub repo connect karke deploy karo (`heroku.yml` Dockerfile se worker chalata hai).
5. Resources tab me **worker** dyno ON karo (web dyno nahi chahiye).

CLI se:
```bash
heroku create <app-name> --stack container
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... MONGO_DB_URI=... OWNER_ID=... LOGGER_ID=... STRING_SESSION=...
git push heroku master
heroku ps:scale worker=1
```

## Railway
1. Repo GitHub par push karo, Railway me **New Project > Deploy from GitHub repo**.
2. `railway.json` Dockerfile se build karwata hai.
3. Variables tab me upar wale variables daalo, deploy ho jayega.

## VPS (Ubuntu / Debian)
Option A: Docker (sabse easy)
```bash
cp sample.env .env      # .env me values bharo
docker compose up -d --build
docker compose logs -f
```

Option B: bina Docker
```bash
bash setup              # packages + venv + .env banata hai
bash start              # test run
sudo bash vps-service.sh   # 24/7 chalane ke liye (systemd)
```

## Update karna
Code badalne ke baad apne repo me push karo aur redeploy karo (Heroku/Railway), ya VPS par `docker compose up -d --build`.
