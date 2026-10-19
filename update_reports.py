"""ATLAS: update a dated markets snapshot; not guaranteed real-time.
Sources: Yahoo Finance via unofficial yfinance, optional OpenAI synthesis.
Run at 23h Paris Mon-Fri via GitHub Actions; validate market data before publication.
"""
import os, json, datetime, pathlib, math
from zoneinfo import ZoneInfo
import yfinance as yf

ROOT=pathlib.Path(__file__).parent
OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)
INDICES={'S&P 500':'^GSPC','Nasdaq 100':'^NDX','Dow Jones':'^DJI','Euro Stoxx 50':'^STOXX50E','CAC 40':'^FCHI','DAX':'^GDAXI','Marchés émergents (ETF EEM)':'EEM','VIX':'^VIX','US 10Y (^TNX)':'^TNX','EUR/USD':'EURUSD=X','Brent':'BZ=F'}
US={'Apple':'AAPL','Microsoft':'MSFT','Nvidia':'NVDA','Alphabet':'GOOGL','Amazon':'AMZN','Meta':'META','Tesla':'TSLA','Broadcom':'AVGO','JPMorgan':'JPM','Berkshire Hathaway B':'BRK-B','Eli Lilly':'LLY','Visa':'V','Walmart':'WMT','Netflix':'NFLX','AMD':'AMD','Intel':'INTC','Palantir':'PLTR','Salesforce':'CRM','Oracle':'ORCL','UnitedHealth':'UNH'}
EU={'ASML':'ASML.AS','SAP':'SAP.DE','Siemens':'SIE.DE','LVMH':'MC.PA','TotalEnergies':'TTE.PA','Schneider Electric':'SU.PA','Airbus':'AIR.PA','Sanofi':'SAN.PA','Allianz':'ALV.DE','BNP Paribas':'BNP.PA','Air Liquide':'AI.PA','Inditex':'ITX.MC','Adyen':'ADYEN.AS','Infineon':'IFX.DE','Deutsche Telekom':'DTE.DE','Banco Santander':'SAN.MC','EssilorLuxottica':'EL.PA','Hermès':'RMS.PA','AXA':'CS.PA','BASF':'BAS.DE'}

def hist_quote(symbol):
    df=yf.Ticker(symbol).history(period='12d',interval='1d',auto_adjust=True)
    closes=df['Close'].dropna()
    if len(closes)<2: return None
    last,prior=float(closes.iloc[-1]),float(closes.iloc[-2])
    if not math.isfinite(last) or not math.isfinite(prior) or prior<=0: return None
    return {'price':round(last,4),'pct':round((last/prior-1)*100,2),'date':str(closes.index[-1].date()),'symbol':symbol}

def fetch(names):
    res={}
    for name,symbol in names.items():
        try:
            q=hist_quote(symbol)
            if q:res[name]=q
            else:print('Missing',name,symbol)
        except Exception as exc: print('Error',name,symbol,repr(exc))
    return res

def ranks(items):
    arr=[{'name':n,**q} for n,q in items.items()]
    return sorted(arr,key=lambda a:a['pct'],reverse=True)[:5],sorted(arr,key=lambda a:a['pct'])[:5]

def formatline(name,q):return f"{name}: {q['pct']:+.2f}% (clôture {q['date']}; valeur {q['price']})"

def main():
    now=datetime.datetime.now(ZoneInfo('Europe/Paris'))
    idx=fetch(INDICES);us=fetch(US);eu=fetch(EU)
    # Never publish or overwrite a report containing an empty market snapshot.
    if len(idx)<5 or len(us)<10 or len(eu)<8: raise RuntimeError('Données insuffisantes : publication annulée')
    winners_us,losers_us=ranks(us);winners_eu,losers_eu=ranks(eu)
    common_dates=[q['date'] for n,q in idx.items() if n in ['S&P 500','Nasdaq 100','Euro Stoxx 50']]
    if any((now.date()-datetime.date.fromisoformat(d)).days>4 for d in common_dates):raise RuntimeError('Cotations trop anciennes')
    lines=['# Rapport de marché — '+now.strftime('%d/%m/%Y'),'', 'Source des prix : Yahoo Finance via bibliothèque non officielle yfinance. Cours de clôture, potentiellement différés, pas de garantie de disponibilité ou de fiabilité.','', '## Indices et indicateurs']
    lines += ['- '+formatline(n,q) for n,q in idx.items()]
    lines += ['', '## Actions américaines : classement SUR UNE SÉLECTION DE 20 VALEURS (pas tout le S&P 500)', '### Top 5']
    lines += ['- '+formatline(a['name'],a) for a in winners_us]
    lines += ['### Flop 5']+['- '+formatline(a['name'],a) for a in losers_us]
    lines += ['', '## Actions européennes : classement SUR UNE SÉLECTION DE 20 VALEURS (pas tout l’Euro Stoxx 50)','### Top 5']
    lines += ['- '+formatline(a['name'],a) for a in winners_eu]
    lines += ['### Flop 5']+['- '+formatline(a['name'],a) for a in losers_eu]
    lines += ['', '## Lecture prudente', 'Les variations ne prouvent pas à elles seules pourquoi un titre monte ou baisse. Vérifier résultats, communiqués et articles datés avant d’attribuer une cause.', '']
    report='\n'.join(lines)
    today=now.strftime('%Y-%m-%d')
    # Weekly Friday summary uses persisted snapshots; doesn't pretend to be entire Friday analysis if days are missing.
    if now.weekday()==4:
        snapshots=[]
        for p in sorted(OUT.glob('snapshot-*.json'))[-10:]:
            try:
                s=json.loads(p.read_text()); d=datetime.date.fromisoformat(s['created'][:10]);
                if d.isocalendar()[:2]==now.date().isocalendar()[:2]:snapshots.append(s)
            except (ValueError,KeyError):pass
        if snapshots:
            first=snapshots[0]
            weekly=['','## Bilan hebdomadaire (échantillon des instantanés disponibles)',f"Période couverte : {first['created'][:10]} au {today}."]
            for name, q in idx.items():
                old=first['indices'].get(name)
                if old and old['price']:
                    weekly.append(f"- {name}: {(q['price']/old['price']-1)*100:+.2f}% entre les instantanés (ne représente pas nécessairement la performance officielle lundi-vendredi)")
            report+='\n'.join(weekly)+'\n'
    snapshot={'created':now.isoformat(),'indices':idx,'us':us,'eu':eu,'us_up':winners_us,'us_down':losers_us,'eu_up':winners_eu,'eu_down':losers_eu}
    (OUT/f'snapshot-{today}.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2))
    (OUT/f'report-{today}.md').write_text(report,encoding='utf-8')
    (OUT/'latest.json').write_text(json.dumps({'date':today,'report':report,'snapshot':snapshot},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Report published',today)

if __name__=='__main__':main()
