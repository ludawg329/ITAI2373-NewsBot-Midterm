# Market NewsBot Intelligence System: Midterm Report

**Author:** Wayne Lu (individual project)  
**Course:** ITAI 2373, Natural Language Processing, Houston Community College  
**Instructor:** Professor Sridhar Ganti  
**Date:** October 17, 2026  
**GitHub repository:** <https://github.com/ludawg329/ITAI2373-NewsBot-Midterm>  
**Video demo (MT_Video_Wayne_Lu_ITAI2373):** [Google Drive](https://drive.google.com/file/d/1LzK4pnQjD2_BJWwEYr7jhDtCB8t2vte5/view) (5:13). Backup: [GitHub copy](https://github.com/ludawg329/ITAI2373-NewsBot-Midterm/blob/main/ITAI2373-NewsBot-Midterm/demo/MT_Video_Wayne_Lu_ITAI2373.mp4)  

> Informational only, not investment, tax, or legal advice.

## 1. Summary
I built a NewsBot that reads market news, sorts each article into a topic, scores its tone as bullish, bearish, or neutral, pulls out the people, companies, places, dates, and dollar amounts, and checks it against a watchlist. It is trained on 1,703 full Reuters news articles in six market topics. I compared eight ways of sorting articles and let the scores pick the winner. The winner was right 95.0% of the time on 341 articles it had never seen. My tone checker was right 78% of the time, compared with 56% for a basic word-list tool. The whole project runs on free tools in one Jupyter notebook.

## 2. The Problem and Who It Is For (Module 1)
Every day there are hundreds of market headlines, and only a few affect a given investor's positions, taxes, or business plans. Reading all of them is not realistic for most people. The target user is an individual investor or trader, or a small business owner, who needs the important news pulled out and labeled.

The bot follows an example watchlist I set up: TSLA and HOOD; AI, chip, and robotics companies; data center builds; space stocks; Starlink's move into phone service; the big three U.S. carriers and international carriers; and Fed and economy news. Any report of a Tesla and SpaceX merger gets a priority alert. The bot builds a Monday digest and keeps business news separate from trading news. Large companies pay for news tools like this from Bloomberg and Refinitiv. This is a free, personal version.

## 3. Data
- **Topic data:** Reuters-21578, a public collection of full Reuters newswire stories from 1987 (Kaggle mirror: thedevastator/uncovering-financial-insights-with-the-reuters-2, CC0). The notebook loads the same collection from the NLTK data mirror, so no Kaggle login is needed. I requested instructor approval for this dataset through Canvas on October 14, 2026.
- **Cleanup:** I kept stories with exactly one topic, dropped stubs under 20 words, and removed 53 exact duplicate stories before splitting the data, so no story could appear in both training and testing.
- **Final set:** 1,703 articles with no missing values, about 172 words on average: Earnings 333, Acquisitions 333, Crude Oil 317, Trade 286, Money/FX 249, Interest Rates 185.
- **Tone data:** Reuters has no tone labels, so I trained the tone checker on Financial PhraseBank (Malo et al., 2014), 4,211 financial news sentences labeled by finance experts.
- **New articles for testing:** live headlines from the Federal Reserve and SEC press release feeds, plus a few clearly marked made-up test headlines used only to check the alert and ethics rules.

My first version used headlines only and reached about 87.5% accuracy. I moved to full articles because the assignment requires substantial text.

## 4. How the System Works
1. **Cleaning (Module 2):** lowercases the text, strips links and symbols, splits it into words, removes filler words, and reduces words to their base form. I kept words like "up," "down," and "not" because they matter in market news.
2. **Important words (Module 3):** scores which words stand out in each topic. I tested eight settings and kept the best. Top words make sense: "oil, crude, barrel, OPEC" for Crude Oil and "trade, Japan, export, tariff" for Trade.
3. **Grammar patterns (Module 4):** labels each word as a noun, verb, number, and so on, then compares topics.
4. **Sentence structure (Module 5):** finds who did what to whom in each sentence, such as "subsidiary, ended, offer."
5. **Tone (Module 6):** a trained bullish/bearish/neutral checker, compared with a basic word-list tool (VADER).
6. **Topic sorting (Module 7):** eight approaches compared using five practice rounds on the training set, then one final test on the 20% held back.
7. **Names and numbers (Module 8):** finds people, companies, places, dates, and money, plus custom rules for stock tickers and percentages.
8. **Putting it together:** one function runs an article through every step, adds watchlist matches, alerts, and ethics labels, and builds the Monday digest.

## 5. Results

| Approach | Practice-round accuracy | Final test accuracy |
|---|---|---|
| **Meaning-based reader (mpnet) + simple scorer (selected)** | **95.9%** | **95.0%** |
| Word and letter-pattern scorer | 95.5% | 94.4% |
| Same, with tuned settings | 95.4% | 94.4% |
| Three models voting together | 95.1% | 94.7% |
| Word-based scorer (two versions) | 94.7-94.8% | 94.1-94.4% |
| Word-count models (two versions) | 91.3-92.4% | 92.1-92.4% |

The model was picked automatically by its practice-round accuracy, not by me. Twelve test articles (3.5%) were nearly identical to training articles. Without them, accuracy was 95.7%, so the score is not coming from repeats. Trade was sorted perfectly. Interest Rates was the weakest (81% of those articles found). It was mixed up with Money/FX 7 times, which makes sense because both cover central banks and rates.

**Tone:** 78% correct on 843 held-out PhraseBank sentences, compared with 56% for the basic word-list tool.

## 6. What the Analysis Found
- **Earnings stories are the most emotional.** They had the highest bearish share (35%) and the highest bullish share (30%). Acquisition stories were 92% neutral.
- **Each topic has its own writing style.** About 19% of the words in Earnings stories are numbers. Trade stories use the most action words. Acquisition stories have the most names.
- **Trade stories are the most global.** They mention about 8.4 places per article and the most dollar amounts.
- **The most mentioned names fit 1987.** They include Reagan, Treasury Secretary James Baker, OPEC, GATT, the Treasury, and the Fed.
- **The name finder makes mistakes.** It treated "cts" (cents) as a company 568 times. Automatic tools still need a human check.

## 7. Business Recommendations
1. Send Earnings news to same-day alerts, since it carries the strongest tone in both directions.
2. Let the bot file articles automatically, but send low-confidence ones to a manual review.
3. Use the dollar amounts and percentages it finds to rank Earnings and Acquisitions news in the Monday digest.
4. Keep business news in its own section, separate from trading news.

## 8. Limits and Ethics
- **Old data:** the topic model learned from 1987 news. On modern headlines it can be wrong. It filed a Tesla earnings headline and most current SEC press releases under Acquisitions. For now, the watchlist and alert rules carry more weight than the topic label.
- **Tone accuracy:** 78% means about one in five tone calls is wrong. The tone checker was trained on single sentences, so its scores on whole articles are an estimate.
- **Not advice:** every output is labeled informational only.
- **Restricted list:** some employers restrict which stocks their staff can hold. The bot supports a restricted list. My example list blocks Boeing, Lockheed Martin, Northrop Grumman, Viasat, and SpaceX, and flags others such as Rocket Lab and Iridium. These are shown as news only, never as trade ideas.
- **Sources:** only public, official feeds. Nothing behind a paywall is scraped.

## 9. Future Work
Retrain on modern full-length financial articles. Teach the name finder to recognize tickers and my watchlist companies directly. Add a simple web page for pasting in an article. Run it on a schedule so the Monday digest builds itself.

## 10. Sources and Tools
- Reuters-21578 (Lewis, 1997), via NLTK data and Kaggle (thedevastator/uncovering-financial-insights-with-the-reuters-2).
- Malo, P., et al. (2014). Financial PhraseBank. Hugging Face takala/financial_phrasebank, CC BY-NC-SA 3.0.
- Federal Reserve and SEC public press release feeds.
- Tools: Python, pandas, scikit-learn, NLTK (including VADER), spaCy en_core_web_sm, sentence-transformers all-mpnet-base-v2, matplotlib, seaborn, Jupyter.
- An AI assistant helped with coding and debugging, as the course allows.
