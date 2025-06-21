#!/usr/bin/env python3
"""
大学データのデバッグスクリプト
"""

import json

def debug_university_data():
    """現在の大学データをデバッグ"""
    
    # Streamlit用データを確認
    with open('streamlit-vocab-analyzer/data/analysis_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("📊 現在のデータ状況:")
    print(f"  総ファイル数: {data['overall_summary']['total_source_files']}")
    print(f"  総単語数: {data['overall_summary']['total_words_extracted']:,}")
    
    print("\n🏫 大学・学部一覧:")
    universities = list(data.get('university_analysis', {}).keys())
    for i, univ in enumerate(universities, 1):
        univ_data = data['university_analysis'][univ]
        print(f"  {i}. {univ}")
        print(f"     単語数: {univ_data.get('total_words', 0):,}")
        print(f"     OCR信頼度: {univ_data.get('ocr_confidence', 0):.1f}%")
        print(f"     ページ数: {univ_data.get('pages_processed', 0)}")
    
    print(f"\n📝 合計大学・学部数: {len(universities)}")
    
    # 問題のある大学名をチェック
    print("\n🔍 名前形式チェック:")
    for univ in universities:
        if len(univ) > 50:
            print(f"  ⚠️  長すぎる名前: {univ}")
        if any(char in univ for char in ['/', '\\', '<', '>']):
            print(f"  ⚠️  特殊文字含む: {univ}")

if __name__ == "__main__":
    debug_university_data()