"""ATLAS V3. Quote snapshots (not guaranteed real time) + French Google News RSS.
No fabricated prices or automated claim of news causality. Requires Internet when run.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import pathlib
from collections import defaultdict
from urllib.parse import urlencode
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import feedparser
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
PARIS = ZoneInfo("Europe/Paris")

INDICES = {
    "S&P 500": "^GSPC", "Nasdaq 100": "^NDX", "Dow Jones": "^DJI",
    "Euro Stoxx 50": "^STOXX50E", "CAC 40": "^FCHI", "DAX": "^GDAXI",
    "Marchés émergents (ETF EEM)": "EEM", "VIX": "^VIX",
    "Taux US 10 ans (proxy ^TNX)": "^TNX", "EUR/USD": "EURUSD=X",
    "Pétrole Brent": "BZ=F",
}
# Périmètre de 40 grandes valeurs reconnues. Il ne s'agit pas d'un indice exhaustif.
US = {
    "Apple": ("AAPL", "Technologie"), "Microsoft": ("MSFT", "Technologie"),
    "Nvidia": ("NVDA", "Technologie"), "Alphabet": ("GOOGL", "Technologie"),
    "Amazon": ("AMZN", "Consommation"), "Meta": ("META", "Technologie"),
    "Tesla": ("TSLA", "Automobile"), "Broadcom": ("AVGO", "Technologie"),
    "AMD": ("AMD", "Technologie"), "Intel": ("INTC", "Technologie"),
    "Netflix": ("NFLX", "Médias"), "Salesforce": ("CRM", "Technologie"),
    "Oracle": ("ORCL", "Technologie"), "Palantir": ("PLTR", "Technologie"),
    "JPMorgan": ("JPM", "Banques"), "Berkshire Hathaway": ("BRK-B", "Finance"),
    "Visa": ("V", "Finance"), "Walmart": ("WMT", "Consommation"),
    "Eli Lilly": ("LLY", "Santé"), "UnitedHealth": ("UNH", "Santé"),
}
EU = {
    "ASML": ("ASML.AS", "Technologie"), "SAP": ("SAP.DE", "Technologie"),
    "Siemens": ("SIE.DE", "Industrie"), "LVMH": ("MC.PA", "Luxe"),
    "TotalEnergies": ("TTE.PA", "Énergie"), "Schneider Electric": ("SU.PA", "Industrie"),
    "Airbus": ("AIR.PA", "Industrie"), "Sanofi": ("SAN.PA", "Santé"),
    "Allianz": ("ALV.DE", "Assurance"), "BNP Paribas": ("BNP.PA", "Banques"),
    "Air Liquide": ("AI.PA", "Industrie"), "Inditex": ("ITX.MC", "Consommation"),
    "Adyen": ("ADYEN.AS", "Finance"), "Infineon": ("IFX.DE", "Technologie"),
    "Deutsche Telekom": ("DTE.DE", "Télécoms"), "Santander": ("SAN.MC", "Banques"),
    "EssilorLuxottica": ("EL.PA", "Santé"), "Hermès": ("RMS.PA", "Luxe"),
    "AXA": ("CS.PA", "Assurance"), "BASF": ("BAS.DE", "Industrie"),
}


def quote(ticker: str):
    hist = yf.Ticker(ticker).history(period="12d", interval="1d", auto_adjust=True)
    if hist is None or "Close" not in hist:
        return None
    prices = hist["Close"].dropna()
    if len(prices) < 2:
        return None
    value, prev = float(prices.iloc[-1]), float(prices.iloc[-2])
    if not all(math.isfinite(x) and x > 0 for x in (value, prev)):
        return None
    return {"price": round(value, 4), "pct": round(100*(value/prev-1), 2),
            "date": str(prices.index[-1].date()), "symbol": ticker}


def collect(symbols, region=None):
    output = {}
    for name, item in symbols.items():
        ticker, sector = item if isinstance(item, tuple) else (item, None)
        try:
            item = quote(ticker)
            if item:
                item.update({"name": name})
                if sector: item["sector"] = sector
                if region: item["region"] = region
                output[name] = item
            else:
                print("Cotations indisponibles", name, ticker)
        except Exception as exc:
            print("Erreur cotation", ticker, str(exc)[:160])
    return output


def session_values(items):
    """Exclude lagging symbols from rankings to avoid comparing different sessions."""
    if not items: return []
    recent = max(x["date"] for x in items.values())
    return [x for x in items.values() if x["date"] == recent]


def ranked(items):
    values = session_values(items)
    return sorted(values, key=lambda x: x["pct"], reverse=True)[:5], sorted(values, key=lambda x: x["pct"])[:5]


def get_news():
    """Headlines ONLY; never treat the title as a verified cause of price movement."""
    q = '(bourse OR Wall Street OR Nasdaq OR CAC 40 OR BCE OR Fed OR LVMH OR Nvidia) when:2d'
    url = 'https://news.google.com/rss/search?' + urlencode({'q': q, 'hl': 'fr', 'gl': 'FR', 'ceid': 'FR:fr'})
    try:
        feed = feedparser.parse(url, request_headers={'User-Agent': 'ATLAS-personal-dashboard/3.0'})
    except Exception as exc:
        print('Erreur RSS', exc)
        return []
    results, seen = [], set()
    english_markers = (' stocks ', ' shares ', ' investors ', ' earnings ', ' market ', ' jumps ', ' drops ', ' amid ', ' after ', ' says ')
    french_markers = (' le ', ' la ', ' les ', ' des ', ' une ', ' dans ', ' sur ', ' pour ', ' selon ', ' bourse', ' hausse', ' baisse', ' actions', ' marché', ' résultats', ' taux ', ' après ', ' avant ')
    fr_sources = ('zonebourse', 'boursorama', 'les échos', 'la tribune', 'le figaro', 'capital', 'bfm', 'franceinfo', 'francetv', 'investir', 'challenges', 'l\'express', 'le monde', 'abcbourse')
    for entry in feed.entries:
        title = entry.get('title','').strip()
        link = entry.get('link','').strip()
        source = entry.get('source',{}).get('title','') if entry.get('source') else ''
        # The French edition sometimes indexes English articles; skip the obvious ones.
        if not title or not link or title in seen or any(w in f' {title.lower()} ' for w in english_markers):
            continue
        if not (any(marker in f' {title.lower()} ' for marker in french_markers) or any(marker in source.lower() for marker in fr_sources)):
            continue
        seen.add(title)
        timestamp = entry.get('published','')
        try:
            timestamp = parsedate_to_datetime(timestamp).astimezone(PARIS).strftime('%d/%m/%Y %H:%M')
        except (ValueError, TypeError, OverflowError):
            timestamp = ''
        results.append({'title': title[:220], 'url': link, 'source': source[:70], 'published': timestamp[:80]})
        if len(results) >= 12: break
    return results


def lines_for(items):
    return [f"- {x['name']} : {x['pct']:+.2f} % (séance {x['date']}, prix {x['price']})" for x in items]


def build_report(now, indices, us, eu, news, weekly_lines):
    uup, udown = ranked(us); eup, edown = ranked(eu)
    out = [f"# ATLAS — Bilan du {now:%d/%m/%Y}", '',
        f"Publication : {now.strftime('%d/%m/%Y %H:%M')} (Paris). Source : Yahoo Finance via yfinance, sans garantie de temps réel.",
        "Les cotations sont les dernières disponibles, et peuvent être différées ; leur date de séance est indiquée. Une valeur publiée à 21 h ne constitue pas forcément la clôture américaine.",
        '', '## Indices et repères']
    for x in indices.values(): out.append(f"- {x['name']} : {x['pct']:+.2f} % | {x['price']} | séance {x['date']}")
    for title, data in [
        ('Grandes actions américaines — 5 hausses (échantillon de 20)',uup),
        ('Grandes actions américaines — 5 baisses (échantillon de 20)',udown),
        ('Grandes actions européennes — 5 hausses (échantillon de 20)',eup),
        ('Grandes actions européennes — 5 baisses (échantillon de 20)',edown),
    ]:
        out += ['',f'## {title}',*lines_for(data)]
    out += ['', '## Actualités françaises à consulter (titres, non vérification de causalité)']
    out += [f"- {x['title']} ({x['source']}) — {x['url']}" for x in news[:6]] or ['- Aucun titre disponible.']
    if weekly_lines: out += ['', '## Bilan hebdomadaire — observations disponibles',*weekly_lines]
    out += ['', '## Comment interpréter les hausses et baisses ?',
            "Un article d'actualité n'établit pas à lui seul la cause d'un mouvement. Consulte les annonces de sociétés et les sources originales avant de conclure. Le rapport ne contient pas encore de synthèse IA indépendante."]
    return '\n'.join(out)


def get_weekly_lines(now, indices):
    if now.weekday() != 4: return []
    matches = []
    for f in sorted(DATA.glob('snapshot-*.json')):
        try:
            obj = json.loads(f.read_text(encoding='utf-8'))
            date = dt.date.fromisoformat(obj['created'][:10])
            if date.isocalendar()[:2] == now.date().isocalendar()[:2]: matches.append(obj)
        except Exception: pass
    if not matches: return ['Historique insuffisant pour comparer le début et la fin de semaine.']
    old = matches[0]
    result = [f"Comparaison entre les instantanés du {old['created'][:10]} et du {now:%Y-%m-%d} (pas nécessairement le rendement officiel de la semaine)."]
    for k,v in indices.items():
        p = old.get('indices',{}).get(k,{}).get('price')
        if p: result.append(f"- {k} : {100*(v['price']/p-1):+.2f} % entre les instantanés")
    return result


def main():
    now = dt.datetime.now(PARIS)
    indices = collect(INDICES)
    us = collect(US, 'US')
    eu = collect(EU, 'EU')
    # Do not overwrite the last good report if a provider is unavailable.
    if len(indices) < 5 or len(us) < 10 or len(eu) < 10:
        raise RuntimeError(f"Données insuffisantes indices={len(indices)} US={len(us)} EU={len(eu)}. Publication annulée.")
    if not session_values(us) or not session_values(eu):
        raise RuntimeError('Dates de séance absentes. Publication annulée.')
    today = now.date().isoformat()
    freshness = max(indices.get(k,{}).get('date','1900-01-01') for k in ['S&P 500','Nasdaq 100','Euro Stoxx 50'])
    if (now.date() - dt.date.fromisoformat(freshness)).days > 4:
        raise RuntimeError('Aucune date de cours récente : publication annulée.')
    news = get_news()
    uup, udown = ranked(us); eup, edown = ranked(eu)
    weekly = get_weekly_lines(now, indices)
    snap = {'created':now.isoformat(), 'indices':indices, 'us':us, 'eu':eu,
            'us_up':uup, 'us_down':udown, 'eu_up':eup, 'eu_down':edown,
            'news':news, 'weekly':weekly,
            'disclaimer':'Prix Yahoo Finance via yfinance, possiblement différés et indicatifs. Classements sur 20 entreprises par région, pas sur l’ensemble du marché.'}
    report = build_report(now, indices, us, eu, news, weekly)
    (DATA/f'snapshot-{today}.json').write_text(json.dumps(snap, ensure_ascii=False, indent=2),encoding='utf-8')
    (DATA/f'report-{today}.md').write_text(report,encoding='utf-8')
    (DATA/'latest.json').write_text(json.dumps({'date':today,'report':report,'snapshot':snap},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rapport ATLAS V3 généré', now.isoformat(), 'indices', len(indices), 'US', len(us), 'EU', len(eu),'news',len(news))

if __name__ == '__main__': main()
