import re
import nltk

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
import contractions
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from transformers import pipeline
from collections import defaultdict
import os

# Setze die Umgebungsvariable, um die Cache-Warnung zu deaktivieren
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'


# Aktualisierte clean_text-Funktion zur Beibehaltung wichtiger Wörter und Kontextinformationen
def clean_text(text):
    text = contractions.fix(text)
    text = re.sub(r'\b(score|replies|body|deleted|edit|comments|comment|reply|replied|points|upvotes|downvotes)\b', '',
                  text, flags=re.IGNORECASE)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^A-Za-z0-9\s$]+', '', text)
    text = text.lower()

    # Tokenisierung
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    # Wichtige Stoppwörter beibehalten (z.B. Negationen, Hilfsverben)
    important_words = {"not", "n't", "no", "is", "are", "was", "were", "be", "has", "have", "had"}
    tokens = [word for word in tokens if word not in stop_words or word in important_words]

    # Lemmatisierung
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    cleaned_text = ' '.join(tokens)
    return cleaned_text


# Erstellen eines domänenspezifischen Wörterbuchs
financial_terms = {"drop", "crash", "bear market", "bull market", "recession", "recovery", "bubble", "growth", "profit",
                   "loss", "sell", "buy", "gain"}


# Rekursive Verarbeitung von Posts und Kommentaren unter Beibehaltung der Hierarchie
def process_post_recursive(post, parent_tickers=None):
    # Bereinige den Text des Posts
    post_text = post.get('title', '') + ' ' + post.get('selftext', '')
    cleaned_post_text = clean_text(post_text)

    # Extrahiere Ticker aus dem bereinigten Text
    current_tickers = find_tickers(cleaned_post_text)
    if not current_tickers and parent_tickers:
        # Verwende die Ticker des Elternteils, falls vorhanden
        current_tickers = parent_tickers

    # Speichere die bereinigten Texte und die Ticker im Post
    post['cleaned_text'] = cleaned_post_text
    post['tickers'] = current_tickers
    post['sentiment'] = analyze_sentiment_transformer(cleaned_post_text)

    # Verarbeitung der Kommentare (rekursiv)
    if 'comments' in post and post['comments']:
        for comment in post['comments']:
            process_comment_recursive(comment, current_tickers)


def process_comment_recursive(comment, parent_tickers=None):
    # Bereinige den Kommentartext
    cleaned_comment_text = clean_text(comment['body'])

    # Extrahiere Ticker aus dem bereinigten Text
    current_tickers = find_tickers(cleaned_comment_text)
    if not current_tickers and parent_tickers:
        # Verwende die Ticker des Elternkommentars oder Posts, wenn der Kommentar selbst keine Ticker hat
        current_tickers = parent_tickers

    # Speichere die bereinigten Texte und die Ticker im Kommentar
    comment['cleaned_text'] = cleaned_comment_text
    comment['tickers'] = current_tickers
    comment['sentiment'] = analyze_sentiment_transformer(cleaned_comment_text)

    # Verarbeitung von Antworten (rekursiv)
    if 'replies' in comment and comment['replies']:
        for reply in comment['replies']:
            process_comment_recursive(reply, current_tickers)


# Beispiel für Ticker-Liste (wie zuvor definiert)
tickers = ['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'BRK.B', 'TSLA', 'WMT',
           'JPM', 'NFLX', 'BAC', 'CRM', 'AMD', 'TMO', 'IBM', 'PM', 'DIS', 'INTC',
           'PFE', 'BA', 'UPS', 'GS', 'MMM', 'DE', 'SBUX', 'PYPL', 'DOW', 'AIG',
           'BLK', 'TGT', 'AAL', 'HPQ']

indicators = ['inflation', 'deflation', 'GDP', 'CPI', 'VIX', 'bull market', 'bear market',
              'recession', 'recovery', 'crash', 'bubble']


# Funktionen zur Ticker-Erkennung und Sentiment-Analyse (wie zuvor definiert)
def find_tickers(text):
    found_tickers = []
    for ticker in tickers + indicators:
        # Verwende reguläre Ausdrücke, um sicherzustellen, dass Ticker als eigenständige Wörter erkannt werden
        pattern = r'\b' + re.escape(ticker.lower()) + r'\b'
        if re.search(pattern, text.lower()):
            found_tickers.append(ticker)
    return list(set(found_tickers))


# Verwenden von BERT für die Sentiment-Analyse (mit spezifiziertem Modell)
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")


def analyze_sentiment_transformer(text):
    result = sentiment_pipeline(text)[0]
    # Konvertiere das Ergebnis in einen Compound-Score ähnlich VADER (-1 bis 1)
    if result['label'] == 'NEGATIVE':
        return -result['score']
    else:
        return result['score']


# Beispielpost (vereinfacht)
post = {"title": "Tesla drops below $1 trillion market cap", "selftext": "https://finance.yahoo.com/news/tesla-drops-below-1-trillion-market-cap-154047937.html\n\nOver the weekend CEO Elon Musk said he could sell more stock, in what many saw as an off-color response to a tweet from Senator Bernie Sanders. \n\nMusk sold about $6.9 billion in shares last week, sending the stock price lower. Tesla shares are down more than 15% over the last five sessions. \n\nIt seem Elon will keep selling Telsa stocks this week to finish his 10% goal. Investors can start a small position this week under 1k as tesla is still the industry leader and very far ahead for many competitors. If the stock really drop back to $900, then it could consider to add more position.", "id": "qujwyc", "created_utc": 1636992779.0, "score": 547, "upvote_ratio": 0.92, "num_comments": 142, "comments": [{"body": "a pullback was inevitable with the kind of run up the stock had", "score": 245, "replies": [{"body": "Tell that to NET. Up 300% since May, no signs of slowing down.", "score": 8, "replies": [{"body": "There's a very big difference between adding 50% in a month when you're already a 800b company, compared to adding 300% over 6 months when you're a 15b company\n\nBtw, 50% increase every month for 6 months would result in an increase of over 1000%", "score": 3, "replies": []}, {"body": "I bought net last year because I know the industry and know how big it is and needed. Saw it was undervalued. Sold it at the beginning of the year to fomo in gme and Crypto. Fucked up", "score": 1, "replies": [{"body": "Seriously dude. I got scared in the May dip after there was a huge revision to the mean of P/S consolidation of the entire industry to 20. I thought NET was overvalued back then and reduced my position rather than loading up. Worst decision I ever made.", "score": 1, "replies": []}]}]}, {"body": "are you referring to the run up since 2019?\n\nedit: /s", "score": 63, "replies": [{"body": "No, I'm talking about the 50% runup that happened in the last month", "score": 77, "replies": [{"body": "I just want reddit to pullback the stupid app update that makes me have to click view more replies.\n\nOtherwise I am not selling.\n\nEdit: click to the side of the top bar on similar stories and hit the option to hide that. Maybe it was just my new phone.", "score": 7, "replies": []}]}]}, {"body": "No! Tesla is a 10 trillion company. Also I'm 110 percent serious. Dm me 4 dd", "score": 11, "replies": [{"body": "I already knew that when it was 300bln market cap.", "score": 3, "replies": []}, {"body": "This guy is drunk. Ignore.", "score": 1, "replies": [{"body": "I gave this gal the DD via DM and now she's being gluttonous. wants it all for her self", "score": 2, "replies": []}]}]}, {"body": "I wonder if you would be saying this had Elon not rugged shareholders. Again.", "score": 1, "replies": [{"body": "https://www.reddit.com/r/teslainvestorsclub/comments/qjjbjp/tsla_daily_investor_discussion_october_31_2021/hiv8yob/\n\nI would say that and I did actually say that", "score": 1, "replies": [{"body": "I’m just saying, Elon should change his name to Aladdin because that guy takes his shareholders on a magic carpet ride at least 3x a year. \n\nI’m saying he rugs. Hard.", "score": 3, "replies": [{"body": "He does, but you kinda sign up for that when you invest in one of his companies imo. If someone isn't okay with investing a company with a CEO as eccentric and at times erratic as Musk, then as an investor it's probably best to just steer clear of the companies where he runs things", "score": 1, "replies": []}]}]}]}, {"body": "Impossible", "score": -1, "replies": [{"body": "Tesla will be 2x apple by 2024-2025", "score": 3, "replies": []}]}]}, {"body": "Andddd it’s back lol", "score": 45, "replies": [{"body": "Great idea! Let's do a post everytime Tesla drops below or crosses $1t market cap.", "score": 11, "replies": []}]}, {"body": "> start a small position at 1k\n\nBruh it literally doubled in like 2 months. Is this really a dip? Lol\n\nIf you didn't buy it when it was at 500 5 months ago, why get in at 900 now? Litetally nothing has changed for the company other than the movement (hype) of the stock.", "score": 243, "replies": [{"body": "yea but 100k cars from hertz? you're telling me a 5 billion dollar sale isn't worth an increase of like 500billion in market cap?\n\n/s", "score": 23, "replies": [{"body": "Rivian market cap is 100bln+,", "score": 5, "replies": [{"body": "When do u think is a good time to invest in it? It just went public..now?", "score": 2, "replies": [{"body": "I really wish I bought Rivian (short to mid term) with the IPO as its gone up 50% but I'm new to investing and I was sure it was egregiously overvalued and destined to plummet almost instantly considering it hadn't sold a single car yet had a market cap of 110b.\n\nI've come to learn that the stock market is irrational and stock prices are gauged on a popularity contest (at the moment at least).", "score": 1, "replies": []}]}]}]}, {"body": "This is how a 50%+ draw down starts. \n\n&#x200B;\n\nSounds like you'd be fine if it already 50% gained in the passed few months... but 50% gain and 50% loss are two totally different things, few understand this.", "score": 12, "replies": [{"body": "I think the biggest difference people should keep in mind is:\n\nAfter 50% gain it takes a 33% drop to be back to the initial investment.\n\nAfter a 50% loss it takes a 100% increase to be back to the initial investment.", "score": 17, "replies": [{"body": "RIGGEDemote:free\\_emotes\\_pack:cry", "score": 1, "replies": []}]}]}, {"body": "From q2 to q3, Automotive margins went from 28.4 to 30.5%, operating margin went from 11 to 14.6%, free cash flow increased by $700m, production up 15% qoq.\n\nTwo new factories on the cusp of starting production to continue growth.\n\nYes it’s still richly valued but saying nothing has changed is just ignoring their growth and advantages.", "score": 56, "replies": [{"body": "Yeh he didn't mean literally nothing has changed, what you listed is the minimum for such a massive valuation not a reason for it to double.", "score": 77, "replies": [{"body": "[deleted]", "score": 19, "replies": [{"body": "It’s consistently been overvalued.  Don’t think it’s going to stop now.  I’m not suggesting to buy, because I don’t and wouldn’t.  But this stock doesn’t follow traditional logic, nor will it until the entire market crashes.", "score": 2, "replies": []}, {"body": "No. Do a DCF. Or lookup Gary Black's on Twitter (@garyblack00)", "score": 1, "replies": []}]}]}, {"body": "Margins change was actual news, but the rest was known way ahead of the price run-up. All you had to do was search gigafactory on youtube, there's like 24/7 surveillance on Tesla and Spacex sites.", "score": 4, "replies": []}, {"body": "This justifies 1T valuation, yeah?", "score": 1, "replies": []}, {"body": "You should be a Tesla salesman 'cause you just made me buy more Tesla stocks. Lol jk", "score": -3, "replies": [{"body": "Yes, it’s time to admit that the great product Tesla sells is stock!\n\nThe cars are just an advertisement for the stock.", "score": 28, "replies": []}]}]}, {"body": "It had already hit $900 per share in January though.", "score": 0, "replies": []}, {"body": "That's very true, but the new factories are coming online soon.\n\nCould see more production = more revenue.\n\nNot to mention the selling pressure will be gone for awhile. Musk, his brother and other executives sold.\n\nGood to load up in $900-1,000 range for the next run up.\n\nInfrastructure bill has EV related items too.", "score": -12, "replies": [{"body": "Everything is made up and the points don't matter.", "score": 10, "replies": []}]}, {"body": "Bears will grasp at anything these days", "score": -4, "replies": []}, {"body": "Dude, $1k fair price if it’s going to $2k next", "score": 1, "replies": []}]}, {"body": "Wait did he get kicked out of the 4 comma club? what a loser", "score": 67, "replies": [{"body": "cuz dumbass elon runs his fucking mouth, at least that iv is juicy for selling options", "score": 7, "replies": [{"body": "[deleted]", "score": 8, "replies": [{"body": "i just sell calls lol i learn my lesson not to trade that thing", "score": 4, "replies": [{"body": "Selling Tesla calls is the lesson?  Doesn't that work well until the stock randomly has 3 or 4 hundred billion flow into it over a week or two?", "score": 2, "replies": [{"body": "Assuming the previous commenter meant covered calls", "score": 2, "replies": []}, {"body": "yeah i lost my shares at 800 early this year due to covered calling being hit, but i wheel them back with cash puts later in march or april..forgot about the exact time.. i just wanna get about 100\\~200 dollars per 100 shares per week", "score": 1, "replies": [{"body": "Dumb question, but don’t you need like a lot of cash sitting around to do that?", "score": 1, "replies": [{"body": "You need 100 shares.", "score": 1, "replies": [{"body": "Cash covered puts I mean.  To Sell a 980 strike put don’t you need 98000$ in cash?", "score": 1, "replies": []}]}]}]}]}, {"body": "[deleted]", "score": 0, "replies": [{"body": "You can buy fractional shares depending on what service you are using for investing, you don’t need to buy a full share in that case.", "score": 2, "replies": []}]}]}]}]}]}, {"body": "Nah, the ceo is too unstable for my investment.", "score": 101, "replies": [{"body": "CEO not unstable enough for my investment", "score": 35, "replies": []}, {"body": "I prefer a CEO like theranos who was way more stable in her interviews and presentations!", "score": 8, "replies": [{"body": "this was clearly sarcasm lol", "score": 11, "replies": []}, {"body": "I mean at least Tesla has the tech", "score": 1, "replies": []}, {"body": "I agree, she's everything the world needs, she should be president.", "score": 1, "replies": []}]}, {"body": "That's true, but he also thinks way ahead of the others. There are very few CEO's who do things the way he does", "score": -10, "replies": [{"body": "I agree he thinks ahead and can do great things in his private companies,, but his emotion and ego need some taming. I call it childish, and I don't want to invest in a public company with a childish CEO. I hope the board put a leash on him.", "score": 56, "replies": [{"body": "The board. You mean where his brother sits? Where Murdoch sits? Where Larry \"Oracle\" Ellison sits? The board is designed to let Elon do whatever he wants.", "score": 15, "replies": [{"body": "Exactly. That's why investing in this company now would be a bad idea.", "score": 12, "replies": []}]}, {"body": "Well you missed out. Tesla investors over the years has learned to deal with it and has made tremendous returns. You just suck it up and figure when Elon goes  bipolar to cause the stock drops, use the opportunity to buy the dip.", "score": 5, "replies": [{"body": "Lol I got some good returns over the years by investing in the company and i do expect the company to grow more, but CEO doesn't seem to give a fuck about investors, does he? I probably will continue investing when my valuation of the company and its stability fit my taste, but I won't stay a fanboy like many here.", "score": 2, "replies": []}]}, {"body": "I make money off war, cigarettes, china, guns, alcohol, pandemics...  and ain't gonna stop At a Bernie bully.", "score": -16, "replies": []}]}, {"body": "Because it's better to be evil behind the curtain", "score": 5, "replies": []}]}, {"body": "So you want a stable genius?", "score": 0, "replies": [{"body": "No, a CEO. This is a stock subreddit, so you can call him a genius in other subreddits if you want.", "score": 6, "replies": [{"body": "Tesla is where it is mostly because Elon is who he is.\n\nIf you want a standard boring CEO that's fine - there are 1000 other companies to invest in. Tesla's CEO doesn't think or behave like anybody else. That's not news to anybody. And this unconventional behavior swings both ways - genius ideas, stupid tweets.\n\nEither take the good with the bad, or find some other company to invest in. Because \"just the good parts of Elon\" is not on the menu.", "score": -1, "replies": [{"body": "Yup, hence my post. Thanks for your suggestion.", "score": 9, "replies": []}]}, {"body": "tesla would be like VW without Elon and be failing lol", "score": 1, "replies": []}]}]}, {"body": "Lol doubled from 580 to 1200 in half a year - you’re scared of a small dip?", "score": -20, "replies": [{"body": "Did I say scared? Do you put your emotion to your investment decision?", "score": 16, "replies": [{"body": "Lol I’m inferring from your bad comment, that you’re scared, you don’t have to say something for people to comprehend your being afraid. I don’t like elon, I like the company. I’ve been buying and holding since 2013", "score": -15, "replies": [{"body": "Oh, saying he is unstable is saying I'm afraid or scared. Ok fanboy investor, you don't have to say you don't like Elon since clearly you took offense to it lol.", "score": 11, "replies": [{"body": "[deleted]", "score": -7, "replies": [{"body": "Scared, afraid, triggerred. Nice vocabulary, fanboy lol", "score": 8, "replies": [{"body": "[deleted]", "score": 1, "replies": [{"body": "That literally sounds like you though. Saying someone is ‘triggered’ because they don’t rock with a CEO? So much projection lol. And this is coming from a Tesla bull but you types make us look bad", "score": 3, "replies": []}]}]}, {"body": "If you’ve been buying and holding TSLA since 2013 you’re a billionaire and should be a happy and famous philanthropist, not have have petty arguments.", "score": 4, "replies": [{"body": "You don’t even know how much I bought so how can you say how much I have? I am however in the double, club very comfortably so I am pretty happy yes. Just crazy to see all these people crying about Elon and the stock all the time especially in this sub. It’s a public forum so I have the freedom to say what I want when I want right?", "score": -2, "replies": []}]}]}]}]}]}]}, {"body": "\"Daddy plays 5d chess... You don't know anything\" /r/Elonmusk", "score": -2, "replies": []}]}, {"body": "Looks like it’s close to back to above again.", "score": 8, "replies": []}, {"body": "There's no guarantee he's gonna finish selling the entire 10% this week. If institutions jump in, we could see the stock sliding quite a bit. I'm surprised they've not shorted the stock even after knowing that Elon is selling...where's Melvin?", "score": 12, "replies": [{"body": "They may be short on the Nasdaq instead...there is less reward there but recent history has shown that the Nasdaq can slide up to 12% when Tesla gets hit hard (not saying that this is going to happen, if it does see any kind of dip it'll probably just be 3-4%)...while Tesla is less predictable.", "score": 3, "replies": []}, {"body": "Interesting take… would love it to bait some Tesla short sellers to come in, Elon reverses, then squeezes  🍋 when life gives you lemons!", "score": 1, "replies": []}]}, {"body": "Oh no!\n\nAnyway...", "score": 18, "replies": []}, {"body": "Sike", "score": 6, "replies": []}, {"body": "For 13 minutes", "score": 7, "replies": []}, {"body": " I’ll buy in at 300 , buying at 900 is a joke", "score": 7, "replies": []}, {"body": "[deleted]", "score": 11, "replies": [{"body": "He said the stock price was so high when it went over 420. It was a pot joke. He’s never said it was overvalued. Only people who never read the tweet and believe whatever misinformation bs they hear believe he said it was overvalued. \nPeople can believe the price is overvalued if they want but anyone who says Elon said that is a liar or misinformed.", "score": -7, "replies": [{"body": "The CEO has a fiduciary duty to the shareholders not to make statements that can be readily construed in a way that harms them.\n\nThen again, Elon Musk and fiduciary duty are antonyms at this point.", "score": 19, "replies": []}, {"body": "He said \"Tesla stock price too high imo\"\n\nThe price was ~700 at the time (pre-split). Wasn't a joke about weed. https://twitter.com/elonmusk/status/1256239815256797184?t=KcdmeSWDOjMMol4qa7UsMg&s=19\n\n In fact, Tesla and Elon have been consistently displaying they believe the stock is overvalued. From issuing new stock, to selling it, to literally saying so out loud. \n\nWhat does it take for people to understand that?", "score": 9, "replies": [{"body": "You mean the time he tweeted at 08:11 California time on 5/1 (1-May), and then announced a 5 for 1 split on 8/11 (8-Aug)?\n\nIt was trolling and hinting at a split. Stock \"price\" too high. Hence reduced by a split.", "score": -1, "replies": [{"body": "Yeah, he definitely was hinting at a split that occured at 3x the price. Makes sense.", "score": -2, "replies": [{"body": "08:11 5/1 - tweet.  \n8/11 5:1 - split announcement. \n\nCall that a coincidence if you'd like. It was trolling.", "score": 2, "replies": []}]}]}, {"body": "He has never said the company is overvalued. You inferred it. Go ahead and believe whatever misinformation you want to believe or want to spread. \n\nElon has talked about his motivation to keep the share price “low.” It is harder for stock-based compensation and ESPP with a higher price. Also, while fractional shares are pretty common in the US, they are not as common outside the US and he wants employees and Tesla supporters to more easily be able to acquire shares.", "score": -2, "replies": []}, {"body": "It was a joke about weed and the price had just crossed 420 earlier that week. The fact that the upcoming stock split was announced May 20th wasn’t a coincidence either. Stock split early foreshadowing and weed joke from guy who always foreshadows and makes weed jokes. So weird. \nBut believe he meant he thinks it was overvalued if you want. \nI think the price per share is too high too. But not overvalued by market cap. Just so my stance is perfectly clear for your simple understanding of words. \nAnd ya there’s a reason why price per share actually matters. \nBuying calls on a $1000 share price is very different capital usage than buying calls on a $100 share price. In case you are too simple to realize that price per share does actually matter and serve an important purpose for trading.", "score": -9, "replies": [{"body": "The price was not anywhere near 420 in May 2020. You're just plain wrong.", "score": 4, "replies": []}]}]}, {"body": "What are you smoking? Man", "score": 1, "replies": []}]}, {"body": "People also seem to ignore the whole day was rather red today, lots of big stocks dropped hard and then rebounded a bit.\n\nAlways gotta look at the whole market if you see some stock crash, because sometimes it's all coming down for whatever reason and not just the one you're looking at.", "score": 0, "replies": []}]}, {"body": "It’s funny of a lot of you because all I see is the atmosphere of this sub changed to a little negative or distrust to Elon Musk when the stock pulled back from ATH. People start back to talk a little about production and valuation, instead of purely potential, to justify your argument and fulfil your ego.\n\nWhen it’s 1200 you all keep saying 3000 next week sth like that and pedestalising Elon Musk like a God. And now suddenly some say Elon Musk can’t be trusted that much. Some of you really are hilarious.", "score": 8, "replies": [{"body": "Definitely agree on that, i noticed it too.", "score": 2, "replies": []}, {"body": "The Reddit Hive Mind", "score": 0, "replies": []}]}, {"body": "What he gonna do with all that cash? Invest in Tesla?", "score": 2, "replies": [{"body": "Bitcoin.", "score": -2, "replies": []}, {"body": "Texas Institute of Technology and Science", "score": 1, "replies": []}]}, {"body": "What if he's really just selling because he knows tsla is overvalued here, and the drama is just to offset the panic that would otherwise arise.", "score": 2, "replies": []}, {"body": "We will see ATH at $2T soon", "score": 2, "replies": []}, {"body": "Tesla is ridiculous, I think whats happened is this easy credit from low interest rates has increased disposable income by a huge amount, and stocks have become a kind of casino due to such a large investment by the large unwashed masses of average people who have never touched stocks before recently.\n\nIt almost seems like a case study.  My aunt and 21 year old daughter is now into stocks, these people fall for multilevel marketing and they are investing now, things are crazy.", "score": 2, "replies": []}, {"body": "https://www.youtube.com/watch?v=Gd6aLnPHqeE", "score": 1, "replies": []}, {"body": "hey man u guys ever gonna give luccid and rivian a shot? those companies wanna be on the frontpage every day too, take a brearher u guys", "score": -12, "replies": [{"body": "You must not have been lurking on here this weekend, because Rivian has definitely been talked about quite a bit...but it's mostly not in a positive manner.", "score": 6, "replies": [{"body": "i lurk everywhere sir.. let me search it for a sec", "score": 0, "replies": []}]}]}, {"body": "It didn't even take the liquidity at 480 but this run up could definitely cause a free fall. I would be cautious putting any positions in the current value it is in", "score": 1, "replies": []}, {"body": "https://youtu.be/N4vIBijzg4w", "score": 1, "replies": []}, {"body": "hmmm", "score": 1, "replies": []}, {"body": "Happy I sold my newly long term shares before then. Get fucked tax man.", "score": 1, "replies": []}, {"body": "It puts the lotion on its skin or else it buys the calls again", "score": 1, "replies": []}, {"body": "As it should", "score": 1, "replies": []}, {"body": "TSLA on that early Black Friday sale gang", "score": 1, "replies": []}, {"body": "TSLA $1,200 buy end of year.  I buy everyday.  Can’t wait for Q4 Deliveries.", "score": 1, "replies": []}, {"body": "Someone hack elon musk's twitter to save us", "score": 1, "replies": []}, {"body": "Should we set up Gofundme for Elon or will he be ok?", "score": 1, "replies": []}, {"body": "Always buy the dip", "score": 1, "replies": []}, {"body": "So? Is there any significance to the \"sub 1T above 1T\" thing that I'm missing? \n\nIs that any different from e.g. \"sub 927bn\" to \"above 927bn\" in any way?", "score": 1, "replies": []}]}


# Verarbeitung des Posts unter Beibehaltung der Struktur
process_post_recursive(post)


# Funktion zur Zusammenfassung der Ergebnisse
def summarize_results(post):
    ticker_counts = defaultdict(int)
    ticker_sentiments = defaultdict(list)
    ticker_messages = defaultdict(list)

    def collect_data(item):
        tickers = item.get('tickers', [])
        sentiment = item.get('sentiment', 0)
        cleaned_text = item.get('cleaned_text', '')
        for ticker in tickers:
            ticker_counts[ticker] += 1
            ticker_sentiments[ticker].append(sentiment)
            ticker_messages[ticker].append(cleaned_text)
        # Prüfe auf Kommentare oder Antworten
        if 'comments' in item and item['comments']:
            for comment in item['comments']:
                collect_data(comment)
        if 'replies' in item and item['replies']:
            for reply in item['replies']:
                collect_data(reply)

    # Daten aus dem Post sammeln
    collect_data(post)

    # Durchschnittliches Sentiment pro Ticker berechnen
    ticker_avg_sentiment = {}
    for ticker, sentiments in ticker_sentiments.items():
        avg_sentiment = sum(sentiments) / len(sentiments)
        ticker_avg_sentiment[ticker] = avg_sentiment

    # Ergebnisse anzeigen
    for ticker in ticker_counts:
        print(f"Ticker: {ticker}")
        print(f"Anzahl der Nachrichten: {ticker_counts[ticker]}")
        print(f"Durchschnittlicher Sentiment-Score: {ticker_avg_sentiment[ticker]:.2f}")
        print("Nachrichten, die zum Sentiment beigetragen haben:")
        for message in ticker_messages[ticker]:
            print(f"- {message}")
        print("---")


# Zusammenfassung der Ergebnisse
summarize_results(post)
