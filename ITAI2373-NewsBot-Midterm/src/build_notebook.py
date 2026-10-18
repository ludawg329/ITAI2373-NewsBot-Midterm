import json,copy
nb=json.load(open('/workspace/mnb/template.ipynb'))
C={}
C[2]='''# Install required packages (run this cell first in Colab; already installed locally)
# !pip install spacy scikit-learn nltk pandas matplotlib seaborn wordcloud plotly feedparser
# !python -m spacy download en_core_web_sm
import nltk
for pkg in ['punkt','punkt_tab','stopwords','wordnet','vader_lexicon','averaged_perceptron_tagger','averaged_perceptron_tagger_eng']:
    nltk.download(pkg, quiet=True)
print("✅ NLTK data ready")'''
C[3]='''import pandas as pd, numpy as np, re, warnings, datetime as dt
import matplotlib.pyplot as plt, seaborn as sns
from wordcloud import WordCloud
from collections import Counter, defaultdict
warnings.filterwarnings('ignore')
import spacy, nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tag import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
nlp = spacy.load('en_core_web_sm')
plt.rcParams['figure.figsize'] = (10, 5)
DISCLAIMER = "Informational only, not investment, tax, or legal advice."
print("✅ Libraries loaded |", DISCLAIMER)'''
EXTRA_AFTER_4=['''### 💼 Business Case: Market NewsBot for Individual Investors & Small-Business Owners

**Target user:** an individual investor or trader who follows a watchlist (for example TSLA, HOOD, index and chip stocks), or a small-business owner who needs market, rate, and small-business news.

**Problem:** hundreds of market headlines per day; only a few move positions, taxes, or business plans.

**Value proposition:** automatically (1) route each headline into a market category, (2) tag it bullish/bearish, (3) pull out companies, tickers, $ amounts, % moves and dates, (4) match it to a configurable watchlist, and (5) roll it into a weekly Monday digest plus same-day alerts, with separate **Trading / Macro / Business** sections.

**Industry context:** this mirrors Bloomberg/Refinitiv news analytics and sell-side sentiment feeds, built here with free, open tools.

> ⚠️ **Disclaimer:** Informational only, not investment, tax, or legal advice.''',
'''# ⚙️ Configurable example watchlist and guardrails
WATCHLIST = {
    'Trading': {
        'tickers': {'TSLA': ['tesla','tsla'], 'HOOD': ['robinhood','hood'],
                    'TSM': ['tsmc','taiwan semiconductor'], 'SSNLF': ['samsung'], 'INTC': ['intel'], 'TXN': ['texas instruments']},
        'indices': ['s&p 500','s&p','spx','nasdaq','russell 2000','eafe','10-year','10y','vix','sox','semiconductor index'],
        'themes': ['ai','artificial intelligence','robotics','semiconductor','chip','options','earnings','upgrade','downgrade'],
    },
    'Macro': {
        'macro': ['fomc','fed','cpi','pce','inflation','jobs','payrolls','unemployment','prime rate','mortgage','treasury','yield'],
        'tax': ['irs','wash sale','section 1256','tax'],
        'real_estate': ['real estate','home sales'],
    },
    'Business': {  # small-business news, kept separate from trading news
        'small_business': ['small business','franchise'],
        'financing': ['sba','7(a)'],
        'business_tax': ['franchise tax'],
    },
    'DataCenters': {  # Data center builds segment
        'tickers': ['vrt','etn','gev','vst','ceg','nrg','eqix','dlr','pwr','eme','fix','anet','cien','cohr','lite','crdo','crwv','nbis',
                    'vertiv','eaton','ge vernova','vistra','constellation energy','equinix','digital realty','quanta','emcor','comfort systems',
                    'arista','ciena','coherent','lumentum','credo','coreweave','nebius'],
        'keywords': ['data center','datacenter','hyperscale','hyperscaler','megawatt','gigawatt','campus','capex','cooling',
                     'power purchase agreement','stargate','abilene'],
    },
    'Space': {  # Space segment: every hit carries a compliance-check flag
        'tickers': ['rklb','asts','lunr','pl','rdw','irdm','vsat','ba','lmt','noc','rocket lab','ast spacemobile','intuitive machines',
                    'planet labs','redwire','iridium','viasat','boeing','lockheed','northrop'],
        'keywords': ['launch','satellite','spaceflight','orbit','rocket'],
        # Starlink direct-to-cell / mobile topic (news only)
        'd2c': ['starlink','direct to cell','direct-to-cell','t-satellite','t-mobile','echostar','spectrum','fcc','globalstar',
                'tmus','sats','gsat','at&t','verizon'],
    },
    'Telecom': {  # Telecom carriers segment, linked to Starlink direct-to-cell topic
        'tickers': ['vz','tmus','vod','dtegy','amx','oran','tef','bce','rci','tu','nttyy','skm','verizon','t-mobile','vodafone',
                    'deutsche telekom','america movil','orange','telefonica','rogers','telus','ntt','sk telecom','bharti','airtel','at&t'],
        'keywords': ['wireless carrier','5g','spectrum','subscribers','direct to cell','direct-to-cell'],
    },
    'Regulatory': ['sec','finra','pattern day trader','rule 4210','t+1','options margin','federal register'],
}
ALERT_RULES = {
    'big_move_pct': 7.0,  # alert on >7% day moves for watch tickers
    'event_keywords': ['earnings','upgrade','downgrade','guidance','fomc','rate decision','cpi','halt'],
}
# Example restricted-securities list (compliance filter: some employers restrict which stocks staff may hold)
ETHICS_STATUS = {
    'BLOCK': ['BA','LMT','NOC','VSAT','SPACEX','SPCX'],
    'FLAG':  ['IRDM','RDW','RKLB','ETN','UFO','ARKX','ITA'],   # needs compliance confirmation
    'LOW':   ['ASTS','LUNR','PL'],
}
ETHICS_ALIASES = {'BOEING':'BA','LOCKHEED':'LMT','NORTHROP':'NOC','VIASAT':'VSAT','IRIDIUM':'IRDM','REDWIRE':'RDW','ROCKET LAB':'RKLB',
                  'EATON':'ETN','STARLINK':'SPACEX','AST SPACEMOBILE':'ASTS','INTUITIVE MACHINES':'LUNR','PLANET LABS':'PL'}
def ethics_status(text):
    T = ' ' + str(text).upper() + ' '
    found = {}
    for st, syms in ETHICS_STATUS.items():
        for s_ in syms:
            if re.search(r'(?<![A-Z])\\$?'+re.escape(s_)+r'(?![A-Z])', T): found[s_] = st
    for a, s_ in ETHICS_ALIASES.items():
        if a in T: found[s_] = next(st for st, l in ETHICS_STATUS.items() if s_ in l)
    return found
# Compliance filter: holdings that must be flagged or blocked (restricted list)
BLOCKED_HOLDINGS = ['spacex','spcx']
# Data-handling guardrails
GUARDRAILS = [
    'Informational only, not investment, tax, or legal advice.',
    'Use official APIs/RSS only (SEC EDGAR with declared User-Agent, Federal Register, Federal Reserve, BLS). No paywall scraping.',
    'Store headline + short excerpt (<=200 chars) + link only.',
    'Never log account numbers (redacted automatically).',
    'Business news labeled separately from trading news.',
]
DC_KEYWORDS = WATCHLIST['DataCenters']['keywords']
def is_data_center(text):
    t = str(text).lower()
    return any(re.search(r'(?<![a-z])'+re.escape(k)+r'(?![a-z])', t) for k in DC_KEYWORDS)
def redact_accounts(text):
    """Mask account-number-like digit runs (8+ digits) before anything is logged."""
    return re.sub(r'\\b\\d[\\d-]{7,}\\d\\b', '[REDACTED]', str(text))
def ethics_flag(text):
    t = str(text).lower()
    return [b for b in BLOCKED_HOLDINGS if re.search(r'\\b'+re.escape(b)+r'\\b', t)]
print("Guardrails:"); [print(" -", g) for g in GUARDRAILS]
print("Redaction test:", redact_accounts("acct 1234567890 moved"))''']
C[5]='''# Real public dataset: "Twitter Financial News" (topic + sentiment) by zeroshot on HuggingFace (MIT license)
# https://huggingface.co/datasets/zeroshot/twitter-financial-news-topic
# https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment
TOPIC_URL = 'https://huggingface.co/datasets/zeroshot/twitter-financial-news-topic/resolve/main/topic_train.csv'
SENT_URL  = 'https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment/resolve/main/sent_train.csv'
TOPIC_NAMES = {0:'Analyst Update',1:'Fed/Central Banks',2:'Company/Product News',3:'Rates/Bonds',4:'Dividend',5:'Earnings',
  6:'Energy/Oil',7:'Financials',8:'Currencies',9:'General/Opinion',10:'Metals/Materials',11:'IPO',12:'Regulation/Legal',
  13:'M&A/Investments',14:'Macro',15:'Markets',16:'Politics',17:'Personnel Change',18:'Stock Commentary',19:'Stock Movement'}
raw = pd.read_csv(TOPIC_URL)
raw['category'] = raw['label'].map(TOPIC_NAMES)
# Market categories most relevant to an investor / business owner (8 classes)
KEEP = ['Earnings','Fed/Central Banks','Macro','Rates/Bonds','Energy/Oil','M&A/Investments','Regulation/Legal','Analyst Update']
df = (raw[raw['category'].isin(KEEP)]
      .groupby('category').sample(n=250, random_state=42)
      .reset_index(drop=True))
df = df.rename(columns={'text':'content'})
df['title'] = df['content'].str.split(r'[:\\-–|]').str[0].str.slice(0, 80)
df['full_text'] = df['content']
df = df.dropna(subset=['content','category'])
df.to_csv('market_newsbot_dataset.csv', index=False)
sent_raw = pd.read_csv(SENT_URL)
sent_raw['sentiment'] = sent_raw['label'].map({0:'Bearish',1:'Bullish',2:'Neutral'})
print(f"Topic corpus: {raw.shape} -> sampled {df.shape} across {df.category.nunique()} categories")
print(f"Sentiment corpus: {sent_raw.shape}")'''
KAGGLE_MD='''### 📥 Alternative real datasets on Kaggle (verified 2026-10-14 via Kaggle API metadata)
| Dataset | URL | Content | Size / License |
|---|---|---|---|
| Financial News Headlines Data (CNBC, Guardian, Reuters) | https://www.kaggle.com/datasets/notlucasp/financial-news-headlines | Headlines, Time, Description (CNBC/Reuters/Guardian, 2017-2020) | ~11.8 MB, CC0 |
| Sentiment Analysis for Financial News (FinancialPhraseBank) | https://www.kaggle.com/datasets/ankurzing/sentiment-analysis-for-financial-news | Sentiment (positive/negative/neutral), News Headline (~4.8k rows) | ~2.7 MB, CC BY-NC-SA 4.0 |
| Daily Financial News for 6000+ Stocks | https://www.kaggle.com/datasets/miguelaenlle/massive-stock-news-analysis-db-for-nlpbacktests | headline, url, publisher, date, stock (~4M rows, 2009-2020) | ~886 MB, CC0 (sample to <=2,000) |
| Daily News for Stock Market Prediction | https://www.kaggle.com/datasets/aaron7sun/stocknews | 25 daily Reddit WorldNews headlines + DJIA label | ~14.9 MB, CC BY-NC-SA 4.0 |

This notebook uses the HuggingFace **zeroshot/twitter-financial-news** datasets because they load without credentials and already have market-topic and bullish/bearish labels. Kaggle needs a `kaggle.json` API key:
```python
!pip install kaggle
from google.colab import files; files.upload()          # upload kaggle.json
!mkdir -p ~/.kaggle && cp kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
!kaggle datasets download -d notlucasp/financial-news-headlines --unzip
cnbc = pd.read_csv('cnbc_headlines.csv').dropna()      # also reuters_headlines.csv, guardian_headlines.csv
!kaggle datasets download -d ankurzing/sentiment-analysis-for-financial-news --unzip
fpb = pd.read_csv('all-data.csv', encoding='latin-1', names=['sentiment','headline'])
```'''
C[6]='''print(df['category'].value_counts())
dc_full = raw[raw['text'].apply(is_data_center)]
print(f"\\n🏗️ Data Center Builds segment: {len(dc_full)} of {len(raw)} items in the full corpus match data-center keywords (too few/unlabeled to train; handled by a rule-based router in the final system)")
print(dc_full['text'].head(5).to_string())
print("\\nMissing values:\\n", df[['content','category']].isnull().sum())
df['char_len'] = df['content'].str.len(); df['word_len'] = df['content'].str.split().str.len()
print("\\nLength stats:\\n", df[['char_len','word_len']].describe().round(1))
fig, ax = plt.subplots(1, 2, figsize=(14, 4))
df['category'].value_counts().plot.barh(ax=ax[0], title='Articles per market category')
sns.boxplot(data=df, y='category', x='word_len', ax=ax[1]); ax[1].set_title('Words per item')
plt.tight_layout(); plt.show()
print("\\nSample:"); print(df.sample(5, random_state=1)[['category','content']].to_string())
print("\\n⚠️ Note: items are financial-news headlines/posts (avg ~", round(df.word_len.mean()), "words), not full articles.")'''
C[8]='''import nltk
for _p in ['punkt','punkt_tab','stopwords','wordnet','vader_lexicon','averaged_perceptron_tagger','averaged_perceptron_tagger_eng']:
    nltk.download(_p, quiet=True)
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
# Keep finance-meaningful words that generic stoplists drop
stop_words -= {'up','down','above','below','over','under','no','not','more','most','off'}
stop_words |= {'rt','amp','via','say','says','said'}
def clean_text(text):
    """Normalize raw market text: URLs, HTML entities, cashtags, numbers, punctuation."""
    if not isinstance(text, str) or not text.strip(): return ''
    t = text.replace('&amp;', '&')
    t = re.sub(r'https?://\\S+|www\\.\\S+', ' ', t)
    t = re.sub(r'\\$([A-Za-z]{1,5})\\b', r' ticker_\\1 ', t)          # $TSLA -> ticker_TSLA
    t = re.sub(r'(\\d+(\\.\\d+)?)\\s?%', ' pctnum ', t)                # 5.2% -> pctnum
    t = re.sub(r'\\$\\s?\\d[\\d,.]*\\s?(billion|million|bn|mln|b|m|k)?', ' moneynum ', t, flags=re.I)
    t = re.sub(r'[@#]\\w+', ' ', t)
    t = t.lower()
    t = re.sub(r'[^a-z_\\s]', ' ', t)
    return re.sub(r'\\s+', ' ', t).strip()
def preprocess_text(text, remove_stopwords=True, lemmatize=True):
    tokens = word_tokenize(clean_text(text))
    tokens = [w for w in tokens if len(w) > 1]
    if remove_stopwords: tokens = [w for w in tokens if w not in stop_words]
    if lemmatize: tokens = [lemmatizer.lemmatize(w) for w in tokens]
    return ' '.join(tokens)
for s in ["$TSLA jumps 8.5% after Q3 deliveries beat; https://t.co/x", "", None, "Fed hikes by 0.75% &amp; signals $1.2 billion QT"]:
    print(repr(s), '->', repr(preprocess_text(s)))'''
C[9]='''df['processed_text'] = df['full_text'].apply(preprocess_text)
df = df[df['processed_text'].str.len() > 0].reset_index(drop=True)
print("Docs after preprocessing:", len(df))
print(df[['content','processed_text']].head(5).to_string())
print("Avg tokens after cleaning:", round(df.processed_text.str.split().str.len().mean(), 1))'''
C[11]='''# Parameter optimization: small grid over n-grams / min_df / sublinear tf, scored by 5-fold CV
best = None
for ngr in [(1,1),(1,2)]:
    for mindf in [1,2]:
        for sub in [False, True]:
            pipe = Pipeline([('tfidf', TfidfVectorizer(ngram_range=ngr, min_df=mindf, sublinear_tf=sub, max_features=5000)),
                             ('clf', LinearSVC())])
            sc = cross_val_score(pipe, df.processed_text, df.category, cv=5, scoring='f1_macro').mean()
            print(f"ngram={ngr} min_df={mindf} sublinear={sub}: macro-F1={sc:.3f}")
            if best is None or sc > best[0]: best = (sc, ngr, mindf, sub)
print("Best TF-IDF params:", best)
tfidf_vectorizer = TfidfVectorizer(ngram_range=best[1], min_df=best[2], sublinear_tf=best[3], max_features=5000)
tfidf_matrix = tfidf_vectorizer.fit_transform(df['processed_text'])
feature_names = tfidf_vectorizer.get_feature_names_out()
print("TF-IDF matrix:", tfidf_matrix.shape)'''
C[12]='''cats = sorted(df.category.unique())
top_terms = {}
for c in cats:
    m = np.asarray(tfidf_matrix[(df.category == c).values].mean(axis=0)).ravel()
    top_terms[c] = [feature_names[i] for i in m.argsort()[::-1][:10]]
    print(f"{c:20s}: {', '.join(top_terms[c])}")
fig, axes = plt.subplots(2, 4, figsize=(20, 8))
for ax, c in zip(axes.ravel(), cats):
    text = ' '.join(df.loc[df.category == c, 'processed_text'])
    ax.imshow(WordCloud(width=400, height=300, background_color='white').generate(text)); ax.set_title(c); ax.axis('off')
plt.tight_layout(); plt.show()
# Feature importance: chi-square
chi, p = chi2(tfidf_matrix, df.category)
imp = pd.Series(chi, index=feature_names).sort_values(ascending=False).head(20)
imp[::-1].plot.barh(title='Top 20 discriminative terms (chi²)'); plt.show()'''
C[14]='''def pos_profile(text):
    tags = pos_tag(word_tokenize(re.sub(r'https?://\\S+', '', str(text))))
    groups = {'NOUN':'NN','VERB':'VB','ADJ':'JJ','ADV':'RB','NUM':'CD','PROPN':'NNP'}
    n = max(len(tags), 1)
    out = {k: sum(1 for _, t in tags if t.startswith(v) and (k != 'NOUN' or not t.startswith('NNP')))/n for k, v in groups.items()}
    return out
pos_df = pd.DataFrame(df['full_text'].apply(pos_profile).tolist())
pos_df['category'] = df['category']
print(pos_df.head())
# Grammatical patterns: most common POS bigrams
bigrams = Counter()
for t in df.full_text.head(500):
    tg = [x[1] for x in pos_tag(word_tokenize(re.sub(r'https?://\\S+','',t)))]
    bigrams.update(zip(tg, tg[1:]))
print("Top POS bigrams:", bigrams.most_common(10))'''
C[15]='''pos_by_cat = pos_df.groupby('category').mean().round(3)
print(pos_by_cat)
sns.heatmap(pos_by_cat, annot=True, cmap='YlGnBu'); plt.title('POS distribution by market category'); plt.show()
print("Writing-style notes: highest NUM share ->", pos_by_cat.NUM.idxmax(),
      "| highest VERB share ->", pos_by_cat.VERB.idxmax(), "| highest PROPN share ->", pos_by_cat.PROPN.idxmax())'''
C[17]='''def syntax_features(text):
    doc = nlp(re.sub(r'https?://\\S+', '', str(text)))
    svo = []
    for tok in doc:
        if tok.pos_ == 'VERB':
            subj = [w.text for w in tok.lefts if w.dep_ in ('nsubj','nsubjpass')]
            obj = [w.text for w in tok.rights if w.dep_ in ('dobj','attr','pobj','dative')]
            if subj and obj: svo.append((subj[0], tok.lemma_, obj[0]))
    depth = max([len(list(t.ancestors)) for t in doc] or [0])
    return {'svo': svo, 'n_subj': sum(t.dep_.startswith('nsubj') for t in doc), 'n_dobj': sum(t.dep_=='dobj' for t in doc),
            'n_prep': sum(t.dep_=='prep' for t in doc), 'tree_depth': depth,
            'agents': [t.text for t in doc if t.dep_ == 'nsubj'], 'patients': [t.text for t in doc if t.dep_ in ('dobj','nsubjpass')]}
syn = df['full_text'].apply(syntax_features)
syn_df = pd.DataFrame(syn.tolist()); syn_df['category'] = df['category']
print(syn_df.groupby('category')[['n_subj','n_dobj','n_prep','tree_depth']].mean().round(2))
print("\\nSample subject-verb-object relations (semantic roles: agent-action-patient):")
for r in [x for x in syn_df.svo if x][:12]: print("  ", r)
verbs = Counter(v for l in syn_df.svo for _, v, _ in l)
print("\\nMost common action verbs:", verbs.most_common(15))'''
C[18]='''from spacy import displacy
sample = "Tesla raised its delivery forecast after the Fed cut rates by 25 basis points."
doc = nlp(sample)
try:
    from IPython.display import display, HTML
    display(HTML(displacy.render(doc, style='dep', jupyter=False, options={'compact': True})))
except Exception:
    pass
for t in doc: print(f"{t.text:12s} {t.dep_:10s} head={t.head.text}")'''
C[20]='''sia = SentimentIntensityAnalyzer()
def analyze_sentiment(text):
    if not text or pd.isna(text): return {'compound':0,'pos':0,'neu':1,'neg':0,'label':'neutral'}
    s = sia.polarity_scores(str(text))
    s['label'] = 'positive' if s['compound'] >= 0.05 else 'negative' if s['compound'] <= -0.05 else 'neutral'
    return s
# Domain model: bullish/bearish classifier trained on the labeled Twitter Financial News Sentiment set
s_tr, s_te = train_test_split(sent_raw, test_size=0.2, random_state=42, stratify=sent_raw.sentiment)
market_sent_model = Pipeline([('tfidf', TfidfVectorizer(preprocessor=preprocess_text, ngram_range=(1,2), min_df=2, sublinear_tf=True)),
                              ('clf', LogisticRegression(max_iter=2000, class_weight='balanced'))])
market_sent_model.fit(s_tr.text, s_tr.sentiment)
sp = market_sent_model.predict(s_te.text)
print("Bullish/Bearish/Neutral model (held-out):"); print(classification_report(s_te.sentiment, sp))
vader_map = s_te.text.apply(lambda t: {'positive':'Bullish','negative':'Bearish','neutral':'Neutral'}[analyze_sentiment(t)['label']])
print(f"VADER baseline accuracy on same test set: {accuracy_score(s_te.sentiment, vader_map):.3f}")
# Emotional tone lexicon (finance-flavoured fear/greed/uncertainty)
EMOTION_LEX = {'fear': ['fear','panic','crash','plunge','selloff','recession','default','risk','worry','slump','tumble'],
               'greed': ['rally','surge','soar','record','beat','boom','jump','upgrade','bull','gain'],
               'uncertainty': ['may','could','uncertain','volatile','volatility','unclear','probe','investigation','delay'],
               'trust': ['guidance','reaffirm','stable','dividend','approve','approved','agreement']}
def emotion_scores(text):
    toks = preprocess_text(text).split(); n = max(len(toks), 1)
    return {e: sum(t in ws for t in toks)/n for e, ws in EMOTION_LEX.items()}
sentiment_df = df[['category','full_text']].copy()
v = df['full_text'].apply(analyze_sentiment)
sentiment_df['full_sentiment'] = v.apply(lambda s: s['compound']); sentiment_df['pos_score'] = v.apply(lambda s: s['pos'])
sentiment_df['neu_score'] = v.apply(lambda s: s['neu']); sentiment_df['neg_score'] = v.apply(lambda s: s['neg'])
sentiment_df['full_label'] = v.apply(lambda s: s['label'])
sentiment_df['market_sentiment'] = market_sent_model.predict(df['full_text'])
sentiment_df = pd.concat([sentiment_df, pd.DataFrame(df['full_text'].apply(emotion_scores).tolist())], axis=1)
print(sentiment_df.head())'''
C[21]='''print(sentiment_df.groupby('category')[['full_sentiment','pos_score','neu_score','neg_score']].agg(['mean']).round(3))
mdist = pd.crosstab(sentiment_df.category, sentiment_df.market_sentiment, normalize='index').round(3)
print("\\nBullish/Bearish mix by category:\\n", mdist)
fig, ax = plt.subplots(1, 3, figsize=(20, 5))
mdist.plot.barh(stacked=True, ax=ax[0], color=['#d62728','#2ca02c','#999999']); ax[0].set_title('Market sentiment by category')
sns.boxplot(data=sentiment_df, y='category', x='full_sentiment', ax=ax[1]); ax[1].set_title('VADER compound by category')
sns.heatmap(sentiment_df.groupby('category')[list(EMOTION_LEX)].mean(), annot=True, fmt='.3f', cmap='magma', ax=ax[2]); ax[2].set_title('Emotional tone')
plt.tight_layout(); plt.show()
print("Most bearish category:", mdist['Bearish'].idxmax(), "| most bullish:", mdist['Bullish'].idxmax())'''
C[23]='''from scipy.sparse import hstack, csr_matrix
X_text = df['processed_text']; y = df['category'].values
# Extra dense features (scaled to [0,1]) appended to TF-IDF: sentiment, length, POS shares
extra = np.column_stack([(sentiment_df.full_sentiment.values+1)/2, sentiment_df.pos_score, sentiment_df.neg_score,
                         np.clip(df.word_len/60, 0, 1), pos_df[['NOUN','VERB','ADJ','NUM','PROPN']].values])
X_tr_txt, X_te_txt, e_tr, e_te, y_train, y_test = train_test_split(X_text, extra, y, test_size=0.2, random_state=42, stratify=y)
vec = TfidfVectorizer(ngram_range=best[1], min_df=best[2], sublinear_tf=best[3], max_features=5000)
X_train = hstack([vec.fit_transform(X_tr_txt), csr_matrix(e_tr)]).tocsr()
X_test  = hstack([vec.transform(X_te_txt),  csr_matrix(e_te)]).tocsr()
print("Train:", X_train.shape, "Test:", X_test.shape)'''
C[24]='''classifiers = {'Naive Bayes': MultinomialNB(alpha=0.3), 'Complement NB': ComplementNB(alpha=0.3),
               'Logistic Regression': LogisticRegression(max_iter=2000, C=5), 'Linear SVM': LinearSVC(C=1.0)}
results, trained_models = {}, {}
for name, clf in classifiers.items():
    clf.fit(X_train, y_train); pred = clf.predict(X_test)
    cv = cross_val_score(clf, X_train, y_train, cv=5, scoring='accuracy').mean()
    results[name] = {'accuracy': accuracy_score(y_test, pred), 'macro_f1': f1_score(y_test, pred, average='macro'), 'cv_acc': cv, 'predictions': pred}
    trained_models[name] = clf
    print(f"{name:20s} test acc={results[name]['accuracy']:.3f} macro-F1={results[name]['macro_f1']:.3f} CV acc={cv:.3f}")
# Optimization: feature selection + C tuning for SVM
gs = GridSearchCV(Pipeline([('sel', SelectKBest(chi2)), ('clf', LinearSVC())]),
                  {'sel__k': [1000, 2500, 'all'], 'clf__C': [0.3, 1, 3]}, cv=5, scoring='f1_macro')
gs.fit(X_train, y_train); pred = gs.predict(X_test)
results['Tuned SVM + chi2'] = {'accuracy': accuracy_score(y_test, pred), 'macro_f1': f1_score(y_test, pred, average='macro'), 'cv_acc': gs.best_score_, 'predictions': pred}
trained_models['Tuned SVM + chi2'] = gs.best_estimator_
print("Tuned:", gs.best_params_, f"test acc={results['Tuned SVM + chi2']['accuracy']:.3f}")
res_df = pd.DataFrame({k: {m: v[m] for m in ['accuracy','macro_f1','cv_acc']} for k, v in results.items()}).T.round(3)
print(res_df); res_df.plot.bar(rot=15, title='Model comparison'); plt.ylim(0, 1); plt.show()
best_model_name = res_df['macro_f1'].idxmax(); print("🏆 Best model:", best_model_name)'''
C[25]='''best_model = trained_models[best_model_name]; best_predictions = results[best_model_name]['predictions']
print(classification_report(y_test, best_predictions))
labels = sorted(np.unique(y)); cm = confusion_matrix(y_test, best_predictions, labels=labels)
plt.figure(figsize=(10, 8)); sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.title(f'Confusion Matrix - {best_model_name}'); plt.ylabel('True'); plt.xlabel('Predicted'); plt.xticks(rotation=45); plt.show()
off = cm.copy(); np.fill_diagonal(off, 0); i, j = np.unravel_index(off.argmax(), off.shape)
print(f"Most common confusion: {labels[i]} -> {labels[j]} ({off[i,j]} items)")'''
C[27]='''TICKER_RE = re.compile(r'\\$[A-Z]{1,5}\\b')
PCT_RE = re.compile(r'[-+]?\\d+(?:\\.\\d+)?\\s?%')
def extract_entities(text):
    if not text or pd.isna(text): return []
    t = re.sub(r'https?://\\S+', '', str(text)).replace('&amp;', '&')
    ents = [{'text': e.text, 'label': e.label_, 'start': e.start_char, 'end': e.end_char} for e in nlp(t).ents]
    ents += [{'text': m.group(), 'label': 'TICKER', 'start': m.start(), 'end': m.end()} for m in TICKER_RE.finditer(t)]   # custom rule-based NER
    if not any(e['label'] == 'PERCENT' for e in ents):
        ents += [{'text': m.group(), 'label': 'PERCENT', 'start': m.start(), 'end': m.end()} for m in PCT_RE.finditer(t)]
    return ents
rows = []
for idx, r in df.iterrows():
    for e in extract_entities(r.full_text): rows.append({**e, 'doc_id': idx, 'category': r.category})
entities_df = pd.DataFrame(rows)
print("Entities extracted:", len(entities_df)); print(entities_df.head(10))'''
C[28]='''FOCUS = ['ORG','TICKER','MONEY','PERCENT','DATE','PERSON','GPE']
print(entities_df.label.value_counts().head(12))
ebc = entities_df[entities_df.label.isin(FOCUS)].groupby(['category','label']).size().unstack(fill_value=0)
ebc_norm = ebc.div(df.category.value_counts(), axis=0).round(2)
print("\\nEntities per item by category:\\n", ebc_norm)
sns.heatmap(ebc_norm, annot=True, cmap='Greens'); plt.title('Entity density by market category'); plt.show()
for lab in ['ORG','TICKER','MONEY','PERSON','GPE']:
    print(f"Top {lab}:", entities_df[entities_df.label == lab].text.value_counts().head(8).to_dict())
# Relationship mapping: ORG/TICKER co-occurrence within the same item
co = Counter()
for _, g in entities_df[entities_df.label.isin(['ORG','TICKER','PERSON'])].groupby('doc_id'):
    u = sorted(set(g.text))
    co.update((a, b) for i, a in enumerate(u) for b in u[i+1:])
print("\\nTop entity co-occurrences:", co.most_common(10))'''
C[30]='''def create_comprehensive_analysis():
    ins = {'dataset_overview': {'items': len(df), 'categories': df.category.nunique(), 'avg_words': round(df.word_len.mean(), 1)},
           'classification_performance': {'best_model': best_model_name, **res_df.loc[best_model_name].to_dict()},
           'sentiment_insights': {'most_bearish': mdist['Bearish'].idxmax(), 'most_bullish': mdist['Bullish'].idxmax(),
                                  'overall_mix': sentiment_df.market_sentiment.value_counts(normalize=True).round(3).to_dict()},
           'entity_insights': {'top_orgs': entities_df[entities_df.label=='ORG'].text.value_counts().head(5).to_dict(),
                               'money_heaviest_category': ebc_norm['MONEY'].idxmax() if 'MONEY' in ebc_norm else None},
           'linguistic_patterns': {'most_numeric': pos_by_cat.NUM.idxmax(), 'most_verb': pos_by_cat.VERB.idxmax()},
           'business_recommendations': []}
    r = ins['business_recommendations']
    r.append(f"Route {ins['sentiment_insights']['most_bearish']} headlines to same-day alerts: highest bearish share (hedge/put review).")
    r.append(f"Classifier ({best_model_name}, macro-F1 {ins['classification_performance']['macro_f1']:.2f}) is reliable enough to auto-file headlines; review low-confidence items manually.")
    r.append("Use MONEY/PERCENT entities to rank Earnings and M&A items by size of number for the Monday digest.")
    r.append("Keep Business items in a separate digest section from trading news (guardrail).")
    return ins
insights = create_comprehensive_analysis()
import json as _j; print(_j.dumps(insights, indent=2, default=str))'''
C[32]='''class NewsBotIntelligenceSystem:
    """Market NewsBot: preprocess -> classify -> sentiment -> entities -> watchlist/alerts -> digest."""
    def __init__(self, classifier, vectorizer, sentiment_model, sentiment_analyzer):
        self.classifier, self.vectorizer = classifier, vectorizer
        self.sentiment_model, self.sia, self.nlp = sentiment_model, sentiment_analyzer, nlp
    def preprocess_article(self, title, content):
        full = f"{title}. {content}" if content else str(title)
        return full, preprocess_text(full)
    def _features(self, full, proc):
        s = self.sia.polarity_scores(full); p = pos_profile(full)
        e = np.array([[(s['compound']+1)/2, s['pos'], s['neg'], min(len(full.split())/60, 1)] + [p[k] for k in ['NOUN','VERB','ADJ','NUM','PROPN']]])
        return hstack([self.vectorizer.transform([proc]), csr_matrix(e)]).tocsr()
    def classify_article(self, full, proc):
        X = self._features(full, proc); cat = self.classifier.predict(X)[0]
        try:
            d = self.classifier.decision_function(X)[0]; conf = float(np.exp(d.max())/np.exp(d).sum())
        except Exception: conf = float('nan')
        return cat, conf
    def watchlist_hits(self, full):
        t = ' ' + full.lower() + ' '; hits = defaultdict(list)
        for sym, al in WATCHLIST['Trading']['tickers'].items():
            if f'${sym.lower()}' in t or any(re.search(r'\\b'+re.escape(a)+r'\\b', t) for a in al): hits['Trading'].append(sym)
        for sec, groups in WATCHLIST.items():
            items = groups.values() if isinstance(groups, dict) else [groups]
            for lst in items:
                if sec in ('DataCenters', 'Space', 'Telecom') and lst is groups.get('tickers'):
                    hits[sec] += [k.upper() for k in lst if f'${k}' in t or (len(k) > 4 and k in t)]; continue
                if isinstance(lst, dict): continue
                for kw in lst:
                    if re.search(r'(?<![a-z])'+re.escape(kw)+r'(?![a-z])', t): hits[sec].append(kw)
        return {k: sorted(set(v)) for k, v in hits.items() if v}
    def alerts(self, full, hits, ents):
        out = []; t = full.lower()
        pcts = [abs(float(re.sub(r'[^\\d.]', '', e['text']) or 0)) for e in ents if e['label'] == 'PERCENT']
        if 'TSLA' in hits.get('Trading', []) or 'HOOD' in hits.get('Trading', []):
            if any(p > ALERT_RULES['big_move_pct'] for p in pcts): out.append('BIG MOVE >7% on watch ticker')
            out += [f'EVENT: {k}' for k in ALERT_RULES['event_keywords'] if k in t]
        if 'Space' in hits: out.append('ETHICS CHECK: verify against restricted list before any trade')
        if 'Space' in hits and any(k in WATCHLIST['Space']['d2c'] for k in hits['Space']):
            out.append('D2C NEWS ONLY: SpaceX/Starlink is on the restricted list; public exposure = TMUS, SATS, ASTS, GSAT, IRDM')
        # Priority topic: Tesla/SpaceX merger rumors
        if re.search(r'\\b(tesla|tsla|spacex|musk)\\b', t) and re.search(r'\\b(merger|merge|acquisition|acquire|combination|combine|ipo|xai)\\b', t):
            out.insert(0, 'PRIORITY ALERT: Tesla/SpaceX merger-rumor topic [ETHICS BLOCK: SpaceX, news OK, holding blocked]')
        es = ethics_status(full)
        for sym, st in es.items():
            if st in ('BLOCK', 'FLAG'): out.append(f'ETHICS {st}: {sym} (news only, not a trade idea)')
        if ethics_flag(full): out.append('ETHICS BLOCK: restricted holding (SpaceX/SPCX) - news only, do not trade')
        return out
    def process_article(self, title, content='', link=''):
        title, content = redact_accounts(title), redact_accounts(content)
        if content and content.strip().lower().startswith(str(title).strip().lower()[:40]): content = content[len(title):].strip()
        full, proc = self.preprocess_article(title, content)
        cat, conf = self.classify_article(full, proc)
        if is_data_center(full): cat, conf = 'Data Center Builds', 1.0  # rule-based category (no labeled training data for it)
        ents = extract_entities(full); hits = self.watchlist_hits(full)
        return {'title': redact_accounts(title)[:200], 'excerpt': redact_accounts(content)[:200], 'link': link,
                'category': cat, 'confidence': round(conf, 3), 'market_sentiment': self.sentiment_model.predict([full])[0],
                'vader_compound': self.sia.polarity_scores(full)['compound'],
                'entities': [(e['text'], e['label']) for e in ents if e['label'] in FOCUS],
                'watchlist': hits, 'ethics_status': ethics_status(full), 'alerts': self.alerts(full, hits, ents)}
    def generate_insights(self, results):
        r = pd.DataFrame(results)
        return {'n': len(r), 'categories': r.category.value_counts().to_dict(), 'sentiment': r.market_sentiment.value_counts().to_dict(),
                'alerts': int(r.alerts.apply(len).astype(bool).sum())}
    def weekly_digest(self, results, max_bullets=8):
        """Monday digest: separate Trading / Macro / Business sections, 'so what' line + source link each."""
        lines = [f"📬 MARKET NEWSBOT DIGEST, week of {dt.date.today():%Y-%m-%d}"]
        for sec in ['Trading', 'DataCenters', 'Space', 'Telecom', 'Macro', 'Business']:
            items = [x for x in results if sec in x['watchlist'] or (sec == 'Macro' and 'Regulatory' in x['watchlist'])][:max_bullets]
            lines.append(f"\\n== {sec} ==" + ("" if items else "\\n  (no matching items this week)"))
            for x in items:
                lines.append(f"• [{x['category']} | {x['market_sentiment']}] {x['title'][:110]}\\n   {''.join(f'[ETHICS {v}: {k}] ' for k, v in x['ethics_status'].items() if v in ('BLOCK','FLAG'))}{'⚠️ ETHICS CHECK: verify against restricted list before any trade. ' if sec == 'Space' else ''}So what: {'news only (ethics-restricted), not a trade idea' if any(v in ('BLOCK','FLAG') for v in x['ethics_status'].values()) else x['market_sentiment'].lower() + ' read'} for "
                             f"{', '.join(x['watchlist'][sec] if sec in x['watchlist'] else x['watchlist'].get('Regulatory', []))}. Source: {x['link'] or 'n/a'}")
        lines.append(f"\\n{DISCLAIMER}")
        return '\\n'.join(lines)
newsbot = NewsBotIntelligenceSystem(trained_models[best_model_name] if best_model_name != 'Tuned SVM + chi2' else gs.best_estimator_,
                                    vec, market_sent_model, sia)
print("✅ NewsBot ready with", best_model_name)'''
C[33]='''# 1) SYNTHETIC test items (clearly labeled: written for this demo, NOT real news) to exercise the alert rules
synthetic_tests = [
    {'title': '[SYNTHETIC] Tesla shares jump 9% after earnings beat; analysts issue upgrade', 'content': 'Tesla ($TSLA) reported quarterly revenue of $25 billion, beating estimates.'},
    {'title': '[SYNTHETIC] Fed holds rates steady, signals CPI still too high', 'content': 'The FOMC kept the target range unchanged; 10-year yield rose to 4.3%.'},
    {'title': '[SYNTHETIC] SBA expands 7(a) loans for small franchise owners', 'content': 'Account 123456789012 example to test redaction.'},
    {'title': '[SYNTHETIC] Hyperscaler adds 1.2 gigawatt data center campus in Abilene, Texas', 'content': 'The Stargate site signed a power purchase agreement; Vertiv to supply cooling.'},
    {'title': '[SYNTHETIC] Rocket Lab ($RKLB) wins satellite launch contract', 'content': ''},
    {'title': '[SYNTHETIC] FCC approves EchoStar spectrum sale to SpaceX for Starlink direct-to-cell', 'content': 'T-Mobile T-Satellite expands coverage.'},
    {'title': '[SYNTHETIC] Verizon and Vodafone report 5G subscriber growth; Boeing and Eaton shares fall', 'content': ''},
    {'title': '[SYNTHETIC] Report: Musk weighs Tesla and SpaceX combination ahead of xAI deal', 'content': ''},
    {'title': '[SYNTHETIC] SpaceX tender offer values company at $350 billion', 'content': ''},
]
# 2) LIVE real headlines from free official RSS feeds (headline + short excerpt + link only)
live = []
try:
    import feedparser
    FEEDS = {'Federal Reserve': 'https://www.federalreserve.gov/feeds/press_all.xml',
             'SEC Press': 'https://www.sec.gov/news/pressreleases.rss'}
    import urllib.request
    for src, url in FEEDS.items():
        req = urllib.request.Request(url, headers={'User-Agent': 'MarketNewsBot student project (HCC ITAI 2373)'})  # declared UA per SEC policy
        f = feedparser.parse(urllib.request.urlopen(req, timeout=15).read())
        for e in f.entries[:4]:
            live.append({'title': e.get('title', ''), 'content': re.sub('<[^>]+>', '', e.get('summary', ''))[:200], 'link': e.get('link', ''), 'source': src})
except Exception as ex:
    print("Live feed unavailable (offline?):", ex)
print(f"Live headlines fetched: {len(live)}")
all_results = []
for a in synthetic_tests + live:
    r = newsbot.process_article(a['title'], a.get('content', ''), a.get('link', ''))
    all_results.append(r)
    print(f"\\n📰 {r['title'][:100]}\\n   Category: {r['category']} (conf {r['confidence']}) | Sentiment: {r['market_sentiment']} (VADER {r['vader_compound']:+.2f})")
    print(f"   Entities: {r['entities'][:8]}\\n   Watchlist: {r['watchlist']}\\n   Alerts: {r['alerts']}")
print("\\n", newsbot.generate_insights(all_results))
print("\\n" + newsbot.weekly_digest(all_results))'''
for i,c in enumerate(nb['cells']):
    if c['cell_type']=='code':
        c['source']=C[i]; c['outputs']=[]; c['execution_count']=None
cells=[]
for i,c in enumerate(nb['cells']):
    cells.append(c)
    if i==5:
        cells.append({'cell_type':'markdown','metadata':{},'source':KAGGLE_MD})
    if i==4:
        cells.append({'cell_type':'markdown','metadata':{},'source':EXTRA_AFTER_4[0]})
        cells.append({'cell_type':'code','metadata':{},'outputs':[],'execution_count':None,'source':EXTRA_AFTER_4[1]})
s=''.join(cells[0]['source'])
s=s.replace('# 🤖 NewsBot Intelligence System','# 🤖 Market NewsBot Intelligence System').replace('Politics, Sports, Technology, Business, Entertainment, Health','market categories (Earnings, Fed/Central Banks, Macro, Rates/Bonds, Energy/Oil, M&A, Regulation/Legal, Analyst Update)')
cells[0]['source']=s+'\n\n> ⚠️ **Informational only, not investment, tax, or legal advice.**'
nb['cells']=cells
json.dump(nb,open('/workspace/marketnewsbot/MarketNewsBot.ipynb','w'),indent=1)
