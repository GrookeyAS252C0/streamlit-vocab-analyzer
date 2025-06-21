#!/usr/bin/env python3
"""
抽出データでのlemmatization確認ツール
"""

import json
import re
from collections import Counter
import nltk
from nltk.stem import WordNetLemmatizer

# NLTK データのダウンロード
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

def check_word_forms():
    """語形変化の例を確認"""
    lemmatizer = WordNetLemmatizer()
    
    # 抽出データを読み込み
    with open("extraction_results_pure_english.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_words = []
    for item in data.get('extracted_data', []):
        words = item.get('extracted_words', [])
        all_words.extend(words)
    
    print(f"抽出された総単語数: {len(all_words)}")
    
    # absorb関連の語形を検索
    absorb_related = [w for w in all_words if 'absorb' in w.lower()]
    print(f"absorb関連語: {absorb_related}")
    
    # 一般的な語形変化の例を確認
    word_examples = [
        'running', 'runs', 'ran', 'studies', 'studied', 'better', 'best',
        'children', 'women', 'men', 'feet', 'teeth', 'absorbed', 'absorbing'
    ]
    
    print("\n語形変化の例:")
    for word in word_examples:
        if word.lower() in [w.lower() for w in all_words]:
            lemmatized = lemmatizer.lemmatize(word.lower(), pos='v')
            lemmatized_n = lemmatizer.lemmatize(word.lower(), pos='n')
            print(f"  Found: {word} -> 動詞形: {lemmatized}, 名詞形: {lemmatized_n}")
    
    # 現在の正規化と、lemmatization付きの比較
    print("\n現在の正規化:")
    current_normalized = []
    for word in all_words:
        cleaned = re.sub(r'[^\w]', '', word.lower())
        if len(cleaned) >= 2 and not cleaned.isdigit():
            current_normalized.append(cleaned)
    
    print(f"現在の正規化後ユニーク数: {len(set(current_normalized))}")
    
    print("\nlemmatization付き正規化:")
    lemmatized_words = []
    lemmatizer = WordNetLemmatizer()
    
    for word in all_words:
        cleaned = re.sub(r'[^\w]', '', word.lower())
        if len(cleaned) >= 2 and not cleaned.isdigit():
            # 動詞として原形化
            lemmatized = lemmatizer.lemmatize(cleaned, pos='v')
            # 名詞として原形化
            lemmatized = lemmatizer.lemmatize(lemmatized, pos='n')
            lemmatized_words.append(lemmatized)
    
    print(f"lemmatization後ユニーク数: {len(set(lemmatized_words))}")
    
    # absorbが出現するかチェック
    if 'absorb' in set(lemmatized_words):
        print("✅ lemmatization後に'absorb'が発見されました")
    else:
        print("❌ lemmatization後でも'absorb'は見つかりません")
    
    # 語形変化の例を表示
    differences = []
    current_set = set(current_normalized)
    lemmatized_set = set(lemmatized_words)
    
    word_freq = Counter(all_words)
    for original_word, freq in word_freq.most_common(100):
        cleaned = re.sub(r'[^\w]', '', original_word.lower())
        if len(cleaned) >= 2:
            lemmatized = lemmatizer.lemmatize(cleaned, pos='v')
            lemmatized = lemmatizer.lemmatize(lemmatized, pos='n')
            if cleaned != lemmatized:
                differences.append((original_word, cleaned, lemmatized, freq))
    
    print(f"\n語形変化の例 (上位{min(20, len(differences))}個):")
    for orig, current, lemma, freq in differences[:20]:
        print(f"  {orig} -> {current} -> {lemma} (出現{freq}回)")

if __name__ == "__main__":
    check_word_forms()