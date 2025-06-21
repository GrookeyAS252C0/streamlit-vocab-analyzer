import json
from pdf_text_extractor import PDFTextExtractor

# デバッグ用スクリプト
extractor = PDFTextExtractor()

# 結果を読み込み
with open('extraction_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print("=== OCR結果の分析 ===")
for result in results:
    print(f"\nPDF: {result['pdf_path']}")
    print(f"処理ページ数: {result['pages_processed']}")
    
    for i, raw_text in enumerate(result['raw_ocr_text']):
        print(f"\n--- ページ {i+1} ---")
        print("OCR結果:")
        print(raw_text[:200] + "..." if len(raw_text) > 200 else raw_text)
        
        # 言語判定テスト
        is_english = extractor.is_english_text(raw_text)
        print(f"英語判定: {is_english}")
        
        # 英単語抽出テスト
        words = extractor.extract_english_words(raw_text)
        print(f"抽出単語数: {len(words)}")
        if words:
            print(f"抽出単語例: {words[:10]}")
        
        # 英語部分のみ抽出テスト
        english_lines = []
        for line in raw_text.split('\n'):
            if line.strip() and extractor.is_english_text(line):
                english_lines.append(line)
                
        print(f"英語行数: {len(english_lines)}")
        if english_lines:
            print("英語行例:")
            for line in english_lines[:3]:
                print(f"  {line}")