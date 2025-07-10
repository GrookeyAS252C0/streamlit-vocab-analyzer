#!/usr/bin/env python3
import json
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re

def main():
    # Initialize
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    def normalize_word(word):
        # Basic cleaning
        word = re.sub(r"[^\w]", "", word.lower())
        
        # Filter short words and numbers
        if len(word) < 2 or word.isdigit():
            return None
            
        # Skip stop words
        if word in stop_words:
            return None
            
        # Lemmatization
        try:
            lemmatized = lemmatizer.lemmatize(word, pos="v")  # as verb
            lemmatized = lemmatizer.lemmatize(lemmatized, pos="n")  # as noun
            return lemmatized
        except:
            return word

    # Test with grew
    test_word = "grew"
    normalized = normalize_word(test_word)
    print(f"{test_word} -> {normalized}")

    # Load Target 1400 vocabulary 
    df = pd.read_csv("/Users/takashikemmoku/Desktop/analysisdashboard/target1400.csv", encoding="utf-8-sig")

    # Check if grow is in the original CSV
    grow_matches = df[df["単語"].str.lower() == "grow"]
    print(f"Original grow matches in Target 1400: {len(grow_matches)}")
    if not grow_matches.empty:
        found_word = grow_matches.iloc[0]["単語"]
        print(f"Found: {found_word}")

    # Normalize Target 1400 words the same way
    target_normalized = set()
    for word in df["単語"]:
        word_str = str(word).strip()
        if word_str and word_str != "nan":
            # Apply same normalization
            cleaned = re.sub(r"[^\w]", "", word_str.lower())
            if len(cleaned) >= 2 and not cleaned.isdigit():
                lemmatized_v = lemmatizer.lemmatize(cleaned, pos="v")
                lemmatized_n = lemmatizer.lemmatize(lemmatized_v, pos="n")
                target_normalized.add(lemmatized_n)

    print(f"Target 1400 normalized words: {len(target_normalized)}")

    if normalized in target_normalized:
        print(f"✓ {normalized} IS in normalized Target 1400")
    else:
        print(f"✗ {normalized} is NOT in normalized Target 1400")
        
    # Show some Target 1400 words that start with g
    g_words = [w for w in target_normalized if w.startswith("g")]
    print(f"Words starting with g in Target 1400: {sorted(g_words)[:10]}")

if __name__ == "__main__":
    main()