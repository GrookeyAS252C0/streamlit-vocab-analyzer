#!/usr/bin/env python3
"""
増分PDF処理スクリプト
既存の処理済みファイルをスキップして、新しいファイルのみを処理
"""

import os
import json
from pathlib import Path
import logging

# 元のPDFTextExtractorをインポート
from pdf_text_extractor import PDFTextExtractor

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_processed_files(result_file: str = "extraction_results_pure_english.json") -> set:
    """
    既に処理済みのファイル一覧を取得
    
    Args:
        result_file: 既存の結果ファイル
        
    Returns:
        処理済みファイルのセット
    """
    processed_files = set()
    
    if os.path.exists(result_file):
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            extracted_data = data.get('extracted_data', [])
            for item in extracted_data:
                source_file = item.get('source_file', '')
                if source_file:
                    processed_files.add(source_file)
            
            logger.info(f"既存の処理済みファイル数: {len(processed_files)}")
            
        except Exception as e:
            logger.error(f"既存結果ファイル読み込みエラー: {e}")
    
    return processed_files

def merge_results(existing_file: str, new_results: list) -> dict:
    """
    既存結果と新規結果をマージ
    
    Args:
        existing_file: 既存の結果ファイル
        new_results: 新規処理結果
        
    Returns:
        マージされた結果
    """
    merged_data = {
        'extraction_summary': {},
        'extracted_data': []
    }
    
    # 既存データの読み込み
    if os.path.exists(existing_file):
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            merged_data['extracted_data'] = existing_data.get('extracted_data', [])
            logger.info(f"既存データ: {len(merged_data['extracted_data'])}ファイル")
            
        except Exception as e:
            logger.error(f"既存データ読み込みエラー: {e}")
    
    # 新規データの追加
    for result in new_results:
        # 新規データ用の形式に変換
        new_item = {
            'source_file': result['source_file'],
            'extracted_words': result['extracted_words'],
            'pure_english_text': result.get('pure_english_text', []),
            'ocr_confidence': result['processing_stats']['average_confidence'],
            'pages_processed': result['processing_stats'].get('pages_processed', result['processing_stats'].get('total_pages', 0)),
            'processing_level': result['processing_stats'].get('enhancement_level', 'aggressive')
        }
        merged_data['extracted_data'].append(new_item)
    
    # 全体統計の再計算
    all_words = []
    total_confidence = 0
    valid_confidence_count = 0
    
    for item in merged_data['extracted_data']:
        all_words.extend(item.get('extracted_words', []))
        confidence = item.get('ocr_confidence', 0)
        if confidence > 0:
            total_confidence += confidence
            valid_confidence_count += 1
    
    avg_confidence = total_confidence / valid_confidence_count if valid_confidence_count > 0 else 0
    
    merged_data['extraction_summary'] = {
        'total_source_files': len(merged_data['extracted_data']),
        'total_words_extracted': len(all_words),
        'average_ocr_confidence': avg_confidence,
        'processing_level': 'aggressive',
        'extraction_method': 'pure_english_only',
        'japanese_content': 'completely_ignored'
    }
    
    return merged_data

def process_new_pdfs_only():
    """
    新しいPDFファイルのみを処理する増分処理
    """
    pdf_folder = "./PDF"
    result_file = "extraction_results_pure_english.json"
    
    # 既存の処理済みファイルを取得
    processed_files = get_processed_files(result_file)
    
    # PDFフォルダ内の全ファイルを取得
    pdf_folder_path = Path(pdf_folder)
    if not pdf_folder_path.exists():
        raise FileNotFoundError(f"PDFフォルダが見つかりません: {pdf_folder}")
    
    all_pdf_files = list(pdf_folder_path.glob("*.pdf"))
    
    # 未処理ファイルを特定（ファイル名のみで比較）
    new_pdf_files = []
    processed_filenames = set()
    for processed_path in processed_files:
        filename = os.path.basename(processed_path)
        processed_filenames.add(filename)
    
    for pdf_file in all_pdf_files:
        filename = pdf_file.name
        if filename not in processed_filenames:
            new_pdf_files.append(pdf_file)
    
    logger.info(f"PDFファイル総数: {len(all_pdf_files)}")
    logger.info(f"処理済みファイル数: {len(processed_files)}")
    logger.info(f"新規処理対象ファイル数: {len(new_pdf_files)}")
    
    if not new_pdf_files:
        logger.info("🎉 新規処理が必要なファイルはありません！")
        return
    
    # 新規ファイルの処理
    logger.info(f"📄 新規ファイルを処理開始:")
    for pdf_file in new_pdf_files:
        logger.info(f"  - {pdf_file.name}")
    
    extractor = PDFTextExtractor()
    new_results = []
    
    for pdf_file in new_pdf_files:
        logger.info(f"🔄 処理開始: {pdf_file.name}")
        result = extractor.process_pdf(str(pdf_file), "aggressive")
        new_results.append(result)
        logger.info(f"✅ 処理完了: {pdf_file.name} - {len(result['extracted_words'])}単語抽出")
    
    # 結果のマージと保存
    if new_results:
        merged_data = merge_results(result_file, new_results)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 最終結果:")
        logger.info(f"  総ファイル数: {merged_data['extraction_summary']['total_source_files']}")
        logger.info(f"  総単語数: {merged_data['extraction_summary']['total_words_extracted']:,}")
        logger.info(f"  平均OCR信頼度: {merged_data['extraction_summary']['average_ocr_confidence']:.1%}")
        logger.info(f"💾 結果を保存: {result_file}")

if __name__ == "__main__":
    try:
        process_new_pdfs_only()
    except Exception as e:
        logger.error(f"処理エラー: {e}")
        raise