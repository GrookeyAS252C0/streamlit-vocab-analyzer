#!/usr/bin/env python3
"""
正規化処理デバッグツール
"""

import pandas as pd
import re
import json
from collections import Counter

def debug_target1900_loading():
    """Target 1900の読み込みプロセスをデバッグ"""
    print("=== Target 1900 読み込みデバッグ ===")
    
    # CSV読み込み
    df = pd.read_csv("target1900.csv", encoding='utf-8-sig')
    print(f"CSVロード成功: {len(df)} 行")
    print(f"列名: {df.columns.tolist()}")
    
    # appealを含む行を検索
    appeal_rows = df[df['word'].str.contains('appeal', case=False, na=False)]
    print(f"\n'appeal'を含む行:")
    for idx, row in appeal_rows.iterrows():
        print(f"  行{idx}: {row['word']} -> 正規化: '{normalize_word(row['word'])}'")
    
    # 全単語の正規化をテスト
    target_words = set()
    debug_words = []
    
    for word in df['word'].dropna():
        word = str(word).strip().lower()
        if word:
            cleaned_word = re.sub(r'[^\w]', '', word.lower())
            if len(cleaned_word) >= 2 and not cleaned_word.isdigit():
                target_words.add(cleaned_word)
                if 'appeal' in word:
                    debug_words.append((word, cleaned_word))
    
    print(f"\nTarget 1900 正規化結果:")
    print(f"総単語数: {len(target_words)}")
    print(f"appealデバッグ: {debug_words}")
    print(f"'appeal' in target_words: {'appeal' in target_words}")
    
    return target_words

def debug_extracted_loading():
    """抽出データの読み込みプロセスをデバッグ"""
    print("\n=== 抽出データ読み込みデバッグ ===")
    
    with open("extraction_results_pure_english.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 全ての抽出単語を収集
    all_extracted_words = []
    for item in data.get('extracted_data', []):
        words = item.get('extracted_words', [])
        all_extracted_words.extend(words)
    
    print(f"抽出単語総数: {len(all_extracted_words)}")
    
    # appealを含む単語を検索
    appeal_words = [w for w in all_extracted_words if 'appeal' in w.lower()]
    print(f"'appeal'を含む単語: {appeal_words}")
    
    # 正規化
    normalized_words = []
    debug_appeals = []
    
    for word in all_extracted_words:
        cleaned_word = re.sub(r'[^\w]', '', word.lower())
        if len(cleaned_word) >= 2 and not cleaned_word.isdigit():
            normalized_words.append(cleaned_word)
            if 'appeal' in cleaned_word:
                debug_appeals.append((word, cleaned_word))
    
    print(f"正規化後ユニーク単語数: {len(set(normalized_words))}")
    print(f"appealデバッグ: {debug_appeals}")
    print(f"'appeal' in normalized_words: {'appeal' in normalized_words}")
    
    return set(normalized_words)

def normalize_word(word):
    """単語正規化関数（デバッグ用）"""
    cleaned_word = re.sub(r'[^\w]', '', word.lower())
    if len(cleaned_word) >= 2 and not cleaned_word.isdigit():
        return cleaned_word
    return ""

def main():
    target_words = debug_target1900_loading()
    extracted_words = debug_extracted_loading()
    
    print("\n=== 一致分析 ===")
    matched = target_words.intersection(extracted_words)
    print(f"一致単語数: {len(matched)}")
    
    if 'appeal' in target_words and 'appeal' not in extracted_words:
        print("❌ 'appeal'はTarget 1900にあるが抽出データにない")
    elif 'appeal' not in target_words and 'appeal' in extracted_words:
        print("❌ 'appeal'は抽出データにあるがTarget 1900にない")
    elif 'appeal' in target_words and 'appeal' in extracted_words:
        print("✅ 'appeal'は両方に存在")
    else:
        print("❓ 'appeal'は両方に存在しない")

if __name__ == "__main__":
    main()