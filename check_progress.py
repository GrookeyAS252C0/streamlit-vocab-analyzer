#!/usr/bin/env python3
"""
PDF処理進行状況チェックスクリプト
"""

import json
import os
from datetime import datetime

def check_processing_progress():
    """処理進行状況をチェック"""
    
    print("📊 PDF処理進行状況チェック")
    print("=" * 50)
    
    # PDFファイル一覧取得
    pdf_files = [f for f in os.listdir("PDF/") if f.endswith('.pdf')]
    print(f"📁 処理対象PDFファイル数: {len(pdf_files)}")
    
    # 抽出結果ファイル確認
    result_file = "extraction_results_pure_english.json"
    if os.path.exists(result_file):
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extracted_data = data.get('extracted_data', [])
        processed_files = len(extracted_data)
        
        print(f"✅ 処理完了ファイル数: {processed_files}/{len(pdf_files)}")
        print(f"📈 処理進捗: {processed_files/len(pdf_files)*100:.1f}%")
        
        if extracted_data:
            print("\n🎯 処理済みファイル:")
            total_words = 0
            total_confidence = 0
            
            for item in extracted_data:
                source_file = item.get('source_file', 'N/A')
                word_count = len(item.get('extracted_words', []))
                confidence = item.get('ocr_confidence', 0)
                pages = item.get('pages_processed', 0)
                
                total_words += word_count
                total_confidence += confidence
                
                print(f"  📄 {source_file}")
                print(f"     単語数: {word_count:,}, OCR信頼度: {confidence:.1%}, ページ数: {pages}")
            
            if extracted_data:
                avg_confidence = total_confidence / len(extracted_data)
                print(f"\n📊 統計:")
                print(f"  総単語数: {total_words:,}")
                print(f"  平均OCR信頼度: {avg_confidence:.1%}")
        
        # 未処理ファイル
        processed_sources = [item.get('source_file', '') for item in extracted_data]
        pending_files = []
        
        for pdf_file in pdf_files:
            pdf_path = f"PDF/{pdf_file}"
            if pdf_path not in processed_sources:
                pending_files.append(pdf_file)
        
        if pending_files:
            print(f"\n⏳ 未処理ファイル ({len(pending_files)}個):")
            for file in pending_files:
                print(f"  📄 {file}")
        else:
            print("\n🎉 全ファイル処理完了!")
    
    else:
        print("❌ 抽出結果ファイルが見つかりません")
        print("💡 処理を開始してください: python pdf_text_extractor.py")
    
    print("\n" + "=" * 50)
    print(f"🕐 チェック時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_processing_progress()