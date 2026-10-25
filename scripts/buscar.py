import os, json, time, datetime, urllib.request, urllib.error

KEY = os.environ["FOOTBALL_KEY"]
LG = {"BSA": "Brasileirão", "CL": "Champions League", "PL": "Premier League", "PD": "La Liga", "BL1": "Bundesliga"}

def api(path):
    for _ in range(3):
        req = urllib.request.Request("https://api.football-data.org/v4/" + path, headers={"X-Auth-Token": KEY})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(65)
                continue
            raise Exception({401: "chave inválida", 403: "liga fora do plano grátis"}.get(e.code, "erro HTTP %s" % e.code))
    raise Exception("limite de requisições")

now = datetime.datetime.now(datetime.timezone.utc)
d = lambda x: x.strftime("%Y-%m-%d")
out = {"updated": now.isoformat(), "leagues": {}}
for c in LG:
    try:
        tb = api("competitions/%s/standings" % c); time.sleep(7)
        mt = api("competitions/%s/matches?dateFrom=%s&dateTo=%s" % (c, d(now), d(now + datetime.timedelta(days=9)))); time.sleep(7)
        tab = (next((s for s in tb["standings"] if s["type"] == "TOTAL"), None) or tb["standings"][0])["table"]
        T = {r["team"]["id"]: [r["playedGames"], r["goalsFor"], r["goalsAgainst"]] for r in tab}
        g = sum(r["goalsFor"] for r in tab); n = sum(r["playedGames"] for r in tab)
        ms = []
        for m in mt["matches"]:
            if m["status"] not in ("SCHEDULED", "TIMED"):
                continue
            h, a = m["homeTeam"], m["awayTeam"]
            if h.get("id") in T and a.get("id") in T:
                ms.append({"h": h.get("shortName") or h["name"], "a": a.get("shortName") or a["name"], "ts": m["utcDate"], "hs": T[h["id"]], "as": T[a["id"]]})
        out["leagues"][c] = {"avg": round(g / n, 3) if n else 1.3, "matches": ms, "error": None}
        print(c, len(ms), "jogos")
    except Exception as e:
        out["leagues"][c] = {"avg": 1.3, "matches": [], "error": str(e)}
        print(c, "erro:", e)
json.dump(out, open("data.json", "w"), ensure_ascii=False, indent=1)
