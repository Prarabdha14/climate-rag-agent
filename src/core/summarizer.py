# src/core/summarizer.py
import nltk
import re
from heapq import nlargest

# --- CRITICAL FIX FOR RENDER DEPLOYMENT ---
# Automatically download missing NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK 'punkt'...")
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("Downloading NLTK 'punkt_tab'...")
    try:
        nltk.download('punkt_tab')
    except:
        pass # Fallback for older NLTK versions

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Downloading NLTK 'stopwords'...")
    nltk.download('stopwords')
# ------------------------------------------

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

class ExtractiveSummarizer:
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = set()

    def summarize(self, text, num_sentences=5):
        if not text:
            return ""
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            # Fallback if tokenizer fails
            print(f"Tokenizer error: {e}")
            sentences = text.split('. ')

        if len(sentences) <= num_sentences:
            return text

        word_frequencies = {}
        for word in word_tokenize(text.lower()):
            if word not in self.stop_words and word.isalnum():
                if word not in word_frequencies:
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1

        if not word_frequencies:
            return " ".join(sentences[:num_sentences])

        max_frequency = max(word_frequencies.values())
        for word in word_frequencies.keys():
            word_frequencies[word] = (word_frequencies[word] / max_frequency)

        sentence_scores = {}
        for sent in sentences:
            for word in word_tokenize(sent.lower()):
                if word in word_frequencies:
                    if len(sent.split(' ')) < 30:
                        if sent not in sentence_scores:
                            sentence_scores[sent] = word_frequencies[word]
                        else:
                            sentence_scores[sent] += word_frequencies[word]

        summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
        return ' '.join(summary_sentences)

    def summarize_all(self, text):
        return {
            "one_line": self.summarize(text, 1),
            "three_bullets": self.summarize(text, 3),
            "five_sentence": self.summarize(text, 5)
        }