#!/usr/bin/env python3
import json
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter

def main():
    # Initialize
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    def normalize_word(word):
        # Basic cleaning - same as vocabulary_analyzer_multi.py
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

    # Load Gakushuin JSON
    with open('/Users/takashikemmoku/Downloads/学習院大学_2024年度_英語_法学部.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    extracted_words = data['content']['extracted_words']
    print(f"Total extracted words: {len(extracted_words)}")
    
    # Normalize words
    normalized_words = []
    for word in extracted_words:
        normalized = normalize_word(word)
        if normalized:
            normalized_words.append(normalized)
    
    print(f"Normalized words: {len(normalized_words)}")
    unique_normalized = set(normalized_words)
    print(f"Unique normalized words: {len(unique_normalized)}")
    
    # Check for grew/grow
    print(f"\nChecking for 'grew' and 'grow':")
    print(f"'grew' in original: {'grew' in extracted_words}")
    print(f"'grow' in normalized: {'grow' in unique_normalized}")
    
    # Load Target 1400
    df = pd.read_csv("/Users/takashikemmoku/Desktop/analysisdashboard/target1400.csv", encoding="utf-8-sig")
    
    # Normalize Target 1400 vocabulary 
    target_normalized = set()
    for word in df["単語"]:
        word_str = str(word).strip()
        if word_str and word_str != "nan":
            cleaned = re.sub(r"[^\w]", "", word_str.lower())
            if len(cleaned) >= 2 and not cleaned.isdigit():
                lemmatized_v = lemmatizer.lemmatize(cleaned, pos="v")
                lemmatized_n = lemmatizer.lemmatize(lemmatized_v, pos="n")
                target_normalized.add(lemmatized_n)

    print(f"\nTarget 1400 normalized vocabulary size: {len(target_normalized)}")
    
    # Find matches and unmatched
    matched_words = unique_normalized.intersection(target_normalized)
    unmatched_from_extracted = unique_normalized - target_normalized
    
    print(f"\nMatches with Target 1400: {len(matched_words)}")
    print(f"Unmatched from extracted: {len(unmatched_from_extracted)}")
    
    # Check grow specifically
    if 'grow' in matched_words:
        print("✓ 'grow' IS matched with Target 1400")
    elif 'grow' in unmatched_from_extracted:
        print("✗ 'grow' is in UNMATCHED list (カバー外)")
        print("This is the issue!")
    else:
        print("? 'grow' not found in either list")
    
    # Show some unmatched words starting with 'g'
    unmatched_g = [w for w in unmatched_from_extracted if w.startswith('g')]
    if unmatched_g:
        print(f"\nUnmatched words starting with 'g': {sorted(unmatched_g)[:10]}")

if __name__ == "__main__":
    main()