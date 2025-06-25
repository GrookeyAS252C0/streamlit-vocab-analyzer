#!/usr/bin/env python3
"""
target1200.csvの全ての単語を完全に組み込み語彙データに反映するスクリプト
"""

import pandas as pd
import os

def extract_complete_target1200():
    """target1200.csvから全ての単語を正確に抽出"""
    
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target1200_path = os.path.join(parent_dir, 'target1200.csv')
    
    try:
        print(f"Reading {target1200_path}...")
        df = pd.read_csv(target1200_path, encoding='utf-8-sig')
        print(f"  Columns: {list(df.columns)}")
        print(f"  Shape: {df.shape}")
        
        # '英語'列から全ての単語を抽出（大文字小文字を保持）
        if '英語' in df.columns:
            words = df['英語'].dropna().astype(str).str.strip()
            # 空文字列を除外
            words = words[words.str.len() > 0]
            # 重複削除（大文字小文字を区別しない）
            word_set = set()
            for word in words:
                word_set.add(word.lower())  # 小文字に統一
            
            unique_words = sorted(list(word_set))
            print(f"  Extracted {len(unique_words)} unique words (lowercase normalized)")
            return unique_words
        else:
            print(f"  ERROR: Column '英語' not found!")
            return []
            
    except Exception as e:
        print(f"  ERROR reading {target1200_path}: {str(e)}")
        return []

def update_vocab_data_with_complete_target1200(target1200_words):
    """vocab_data.pyを完全なtarget1200データで更新"""
    
    # 現在のvocab_data.pyを読み込み
    with open('vocab_data.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 新しいTARGET_1200_WORDSセクションを生成
    target1200_section = "TARGET_1200_WORDS = {\n"
    
    # 10単語ずつ改行して見やすく整形
    for i in range(0, len(target1200_words), 10):
        batch = target1200_words[i:i+10]
        # アポストロフィーをエスケープ処理
        escaped_words = [word.replace("'", "\\'") for word in batch]
        line = "    " + ", ".join([f"'{word}'" for word in escaped_words])
        if i + 10 < len(target1200_words):
            line += ","
        target1200_section += line + "\n"
    
    target1200_section += "}\n\n"
    
    # 既存のTARGET_1200_WORDSを削除
    if 'TARGET_1200_WORDS = {' in content:
        start = content.find('TARGET_1200_WORDS = {')
        # 対応する}を見つける
        brace_count = 0
        end = start
        for i, char in enumerate(content[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        
        # 次の改行まで削除
        while end < len(content) and content[end] in '\n':
            end += 1
        
        content = content[:start] + content[end:]
    
    # TARGET_1400_WORDSの前に挿入
    if 'TARGET_1400_WORDS = {' in content:
        insertion_point = content.find('TARGET_1400_WORDS = {')
        content = content[:insertion_point] + target1200_section + content[insertion_point:]
    else:
        # ファイルの最初に追加
        content = target1200_section + content
    
    # ファイルに書き込み
    with open('vocab_data.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ vocab_data.py が更新されました！")
    print(f"   Target 1200: {len(target1200_words)} words (完全版)")

def main():
    """メイン処理"""
    print("=== Target 1200完全版データ更新開始 ===")
    
    # target1200.csvから全ての単語を抽出
    target1200_words = extract_complete_target1200()
    
    if target1200_words:
        print(f"\n=== 抽出結果 ===")
        print(f"TARGET_1200_WORDS: {len(target1200_words)} words")
        print(f"最初の10語: {target1200_words[:10]}")
        print(f"最後の10語: {target1200_words[-10:]}")
        
        # vocab_data.pyファイルを更新
        print(f"\n=== vocab_data.py 更新中 ===")
        update_vocab_data_with_complete_target1200(target1200_words)
        
        print(f"\n✅ 完了！Target 1200の全{len(target1200_words)}語が基礎語彙として設定されました。")
    else:
        print(f"❌ target1200.csvの読み込みに失敗しました。")

if __name__ == "__main__":
    main()