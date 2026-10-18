# NewsBot Reflective Journal

**Wayne Lu** | ITAI 2373, Houston Community College | Professor Sridhar Ganti | October 17, 2026  
**Project:** Market NewsBot | **Repository:** <https://github.com/ludawg329/ITAI2373-NewsBot-Midterm>  

## Technical Integration Challenges
**Most challenging:** getting good data. My first version used short headlines and reached about 87.5% accuracy, but the assignment asks for full articles, not headlines. I switched to the Reuters-21578 collection of full newswire stories and requested approval from my instructor through Canvas on October 14. The catch is that these stories are from 1987, so the bot learned 1987 market language. When I fed it a modern Tesla earnings headline, it filed it under Acquisitions. The SEC press releases from this month also mostly landed in Acquisitions. That taught me a model is only as current as the data it learned from.

**Duplicates:** Reuters sometimes sent the same story twice. I found and removed 53 exact copies before splitting the data, so the bot could not "study" an article and then get tested on the same one. I also flagged 12 test articles that were nearly identical to training articles and reported the score both with and without them (95.0% vs. 95.7%).

**Combining the pieces:** the bot cleans each article, sorts it into one of six topics, scores the tone as bullish, bearish, or neutral, pulls out names, companies, places, dates, and dollar amounts, and then checks it against my watchlist. Each step needed the text in a slightly different shape, so I built one function that runs an article through every step and returns a single result. I also had to add rules where the data had nothing to teach. Only 5 of 6,141 Reuters stories mention anything like a data center, so data center news is caught by a keyword rule instead of the trained model.

**Most useful technique:** the topic sorting. I tried eight different approaches and let the scores pick the winner instead of my opinion. The winner reads each article for overall meaning and was right 95.9% of the time in practice rounds and 95.0% on 341 articles it had never seen. The simplest approach still got about 92%, which surprised me. The topic it misses most is Interest Rates, which it confuses with Money/FX. That makes sense because both talk about central banks and rates.

## Business Value Assessment
I built this to follow market news for trading and business decisions. Every day there are hundreds of market headlines and only a few matter to any one reader. The bot sorts the news, marks the tone, pulls out the key numbers and companies, and flags items on a watchlist, such as TSLA, HOOD, and Fed news. Any news about a possible Tesla and SpaceX merger gets a priority alert. It rolls everything into a Monday digest with trading news kept separate from business news. The same idea could help a small investment shop, a business owner tracking suppliers, or a newsroom sorting stories. One finding with real value: Earnings stories carried both the most bearish (35%) and most bullish (30%) tone of any topic, while Acquisition stories were 92% neutral. For a trader, that means earnings news deserves same-day attention.

**Ethical considerations:** automated news reading has real risks. A wrong label or tone score could push someone into a bad trade, so every output says it is informational only and not investment, tax, or legal advice. The tone checker is right about 78% of the time (a basic word-list tool scored 56%), so roughly one in five calls is wrong. Some employers also restrict which stocks their staff can hold, so I added a restricted list. The bot blocks or flags those names (in my example list, Boeing, Lockheed Martin, and SpaceX) and shows them as news only, never as a trade idea. Last, the bot only reads public, official feeds and never scrapes paid content.

## My Contributions
Since I worked alone, I was responsible for all of it: the business case, collecting and cleaning the data, removing duplicates, the word-importance and grammar analysis, sentence structure, tone scoring, topic sorting and model comparison, finding names and numbers, the watchlist, alerts, ethics filter, Monday digest, the GitHub repository, the report, the video demo, and this reflection.

## Future Enhancements
The biggest upgrade is current data. I want to retrain on modern full-length financial articles so it stops thinking like 1987. I would also teach it to recognize stock tickers and space and telecom companies directly instead of relying on keyword lists, add a simple web page where I can paste an article and see results, and run it on a schedule so the Monday digest builds itself. I would also like to measure the tone checker on full articles, not just single sentences.

## Professional Development Impact
**Future learning:** I am most interested in the topics coming next in this course, like finding hidden themes in news, and in the newer language models that read for meaning, since that approach won here.

**Portfolio value:** this project shows I can take a messy real-world problem, test my work honestly, and explain the results in plain terms. When I talk to employers, I will lead with the problem it solves, the 95% result on unseen articles, and the honest limits: the 1987 data and the 78% tone accuracy. It also shows the bot can follow fast-moving industries, since it already tracks data center builds, chip makers, and carriers.
