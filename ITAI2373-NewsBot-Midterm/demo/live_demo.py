"""Market NewsBot: lightweight live demo (Wayne Lu, ITAI 2373, Oct 17, 2026).

Rebuilds the notebook's selected topic model (mpnet sentence embeddings + Logistic Regression, trained on the
same 80% training split of data/reuters_newsbot_dataset.csv using the cached embeddings), the Financial
PhraseBank Bullish/Bearish/Neutral tone model, and spaCy entity extraction, then runs NEW articles through them:
live Federal Reserve / SEC press-release headlines fetched at run time plus two clearly marked [SYNTHETIC]
test headlines that exercise the watchlist / ethics alerts.  Run from the ITAI2373-NewsBot-Midterm folder:
    python demo/live_demo.py
Informational only, not investment, tax, or legal advice.
"""
import hashlib, html, io, json, re, sys, urllib.request, zipfile
import numpy as np, pandas as pd, spacy, nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

for p in ['punkt', 'punkt_tab', 'stopwords', 'wordnet']: nltk.download(p, quiet=True)
lem = WordNetLemmatizer(); sw = (set(stopwords.words('english')) - {'up','down','above','below','over','under','no','not','more','most','off'}) | {'rt','amp','via','say','says','said'}
def clean_text(t):
    if not isinstance(t, str) or not t.strip(): return ''
    t = t.replace('&amp;', '&'); t = re.sub(r'https?://\S+|www\.\S+', ' ', t)
    t = re.sub(r'\$([A-Za-z]{1,5})\b', r' ticker_\1 ', t); t = re.sub(r'(\d+(\.\d+)?)\s?%', ' pctnum ', t)
    t = re.sub(r'\$\s?\d[\d,.]*\s?(billion|million|bn|mln|b|m|k)?', ' moneynum ', t, flags=re.I)
    t = re.sub(r'[@#]\w+', ' ', t).lower(); t = re.sub(r'[^a-z_\s]', ' ', t); return re.sub(r'\s+', ' ', t).strip()
def preprocess_text(t):
    return ' '.join(lem.lemmatize(w) for w in word_tokenize(clean_text(t)) if len(w) > 1 and w not in sw)

# 1) Topic model: same split as the notebook (80/20 stratified, random_state=42), cached mpnet embeddings
df = pd.read_csv('data/reuters_newsbot_dataset.csv')
z = np.load('data/reuters_mpnet_embeddings.npz'); cache = dict(zip(z['keys'], z['vecs']))
h = lambda t: hashlib.md5(t.encode('utf-8')).hexdigest()
X_tr, X_te, y_tr, y_te = train_test_split(df.full_text, df.category.values, test_size=0.2, random_state=42, stratify=df.category.values)
emb = lambda texts: np.vstack([cache[h(t)] for t in texts])
topic = LogisticRegression(C=10, max_iter=3000).fit(emb(X_tr), y_tr)
print(f"Topic model rebuilt on {len(X_tr)} training articles; held-out accuracy {accuracy_score(y_te, topic.predict(emb(X_te))):.3f} on {len(X_te)} test articles")
from sentence_transformers import SentenceTransformer
st = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device='cpu'); st.max_seq_length = 256

# 2) Tone model: Financial PhraseBank (66% agreement), same settings as the notebook
FPB = 'https://huggingface.co/datasets/takala/financial_phrasebank/resolve/main/data/FinancialPhraseBank-v1.0.zip'
zf = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(FPB, timeout=60).read()))
lines = zf.read('FinancialPhraseBank-v1.0/Sentences_66Agree.txt').decode('latin-1').splitlines()
s = pd.DataFrame([l.rsplit('@', 1) for l in lines if '@' in l], columns=['text', 'label'])
s['sentiment'] = s.label.str.strip().map({'negative': 'Bearish', 'positive': 'Bullish', 'neutral': 'Neutral'})
s = s.dropna().drop_duplicates('text').reset_index(drop=True)
s_tr, s_te = train_test_split(s, test_size=0.2, random_state=42, stratify=s.sentiment)
tone = Pipeline([('tfidf', TfidfVectorizer(preprocessor=preprocess_text, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
                 ('clf', LogisticRegression(max_iter=2000, class_weight='balanced'))]).fit(s_tr.text, s_tr.sentiment)
print(f"Tone model held-out accuracy: {accuracy_score(s_te.sentiment, tone.predict(s_te.text)):.3f} on {len(s_te)} sentences")
nlp = spacy.load('en_core_web_sm')

# 3) Watchlist / ethics rules (subset of the notebook's rules)
WATCH = {'TSLA': ['tesla', 'tsla'], 'HOOD': ['robinhood'], 'Fed/Rates': ['federal reserve', 'fomc', 'interest rate', 'discount rate'],
         'Data centers': ['data center', 'hyperscaler', 'gigawatt'], 'SEC/Regulatory': ['sec ', 'securities and exchange commission']}
BLOCK = {'BA': ['boeing'], 'LMT': ['lockheed'], 'NOC': ['northrop'], 'VSAT': ['viasat'], 'SpaceX': ['spacex', 'spcx']}
def process(title, content=''):
    title, content = html.unescape(title), html.unescape(content)
    if content and content.strip().lower().startswith(title.strip().lower()[:40]): content = content[len(title):].strip(' .')
    full = f"{title}. {content}" if content else title; t = ' ' + full.lower() + ' '
    cat = topic.predict(st.encode([full], normalize_embeddings=True))[0]
    conf = float(topic.predict_proba(st.encode([full], normalize_embeddings=True)).max())
    if any(k in t for k in WATCH['Data centers']): cat, conf = 'Data Center Builds (rule)', 1.0
    ents = list(dict.fromkeys((e.text, e.label_) for e in nlp(full).ents if e.label_ in ('ORG', 'PERSON', 'GPE', 'DATE', 'MONEY', 'PERCENT')))
    hits = [k for k, al in WATCH.items() if any(a in t for a in al)]
    alerts = [f'ETHICS BLOCK: {k} (news only, not a trade idea)' for k, al in BLOCK.items() if any(a in t for a in al)]
    if re.search(r'\b(tesla|spacex|musk)\b', t) and re.search(r'\b(merger|merge|combination|combine|acquire|acquisition)\b', t):
        alerts.insert(0, 'PRIORITY ALERT: Tesla/SpaceX merger topic')
    return {'title': title[:140], 'category': cat, 'confidence': round(conf, 2), 'tone': tone.predict([full])[0],
            'entities': ents[:6], 'watchlist': hits, 'alerts': alerts}

articles = []
for src, url in {'Federal Reserve': 'https://www.federalreserve.gov/feeds/press_all.xml',
                 'SEC': 'https://www.sec.gov/news/pressreleases.rss'}.items():
    try:
        import feedparser
        req = urllib.request.Request(url, headers={'User-Agent': 'MarketNewsBot student project (HCC ITAI 2373)'})
        for e in feedparser.parse(urllib.request.urlopen(req, timeout=20).read()).entries[:2]:
            articles.append({'source': f'LIVE {src} feed', 'title': e.get('title', ''), 'content': re.sub('<[^>]+>', '', e.get('summary', ''))[:300]})
    except Exception as ex:
        print('Feed unavailable:', src, ex)
articles += [
    {'source': 'SYNTHETIC test (not real news)', 'title': '[SYNTHETIC] Report: Musk weighs Tesla and SpaceX combination ahead of xAI deal', 'content': ''},
    {'source': 'SYNTHETIC test (not real news)', 'title': '[SYNTHETIC] Hyperscaler adds 1.2 gigawatt data center campus in Abilene, Texas', 'content': ''},
]
out = []
for a in articles:
    r = {'source': a['source'], **process(a['title'], a['content'])}; out.append(r)
    print(f"\n[{r['source']}] {r['title']}\n  Topic: {r['category']} (conf {r['confidence']}) | Tone: {r['tone']}\n  Entities: {r['entities']}\n  Watchlist: {r['watchlist']} | Alerts: {r['alerts']}")
if len(sys.argv) > 1: json.dump(out, open(sys.argv[1], 'w'), indent=1)
print('\nInformational only, not investment, tax, or legal advice.')
