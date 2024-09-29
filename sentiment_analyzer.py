from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
    
    if sentiment_score < -0.5:
        return "very negative", sentiment_score
    elif sentiment_score < 0:
        return "negative", sentiment_score
    elif sentiment_score == 0:
        return "neutral", sentiment_score
    elif sentiment_score <= 0.5:
        return "positive", sentiment_score
    else:
        return "very positive", sentiment_score
