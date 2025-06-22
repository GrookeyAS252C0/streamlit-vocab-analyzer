#!/usr/bin/env python3
"""
PDFフォルダを監視し、未処理ファイルを自動検出してOCR処理＋語彙分析を実行し、
extraction_results_pure_english.jsonに増分データを追記するスクリプト
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Set
from pdf_text_extractor import PDFTextExtractor
from vocabulary_analyzer_multi import MultiVocabularyAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IncrementalProcessor:
    def __init__(self, pdf_folder: str = "PDF", extraction_results_file: str = "extraction_results_pure_english.json"):
        """
        増分処理クラス
        
        Args:
            pdf_folder: PDFファイルが格納されているフォルダ
            extraction_results_file: 抽出結果を保存するJSONファイル
        """
        self.pdf_folder = Path(pdf_folder)
        self.extraction_results_file = Path(extraction_results_file)
        self.extractor = PDFTextExtractor()
        self.analyzer = MultiVocabularyAnalyzer()
        
    def get_processed_files(self) -> Set[str]:
        """
        既に処理済みのファイル一覧を取得
        
        Returns:
            処理済みファイル名のセット
        """
        if not self.extraction_results_file.exists():
            logger.info(f"{self.extraction_results_file} が存在しないため、新規作成します")
            return set()
        
        try:
            with open(self.extraction_results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            processed_files = set()
            for entry in data.get('extracted_data', []):
                source_file = entry.get('source_file', '')
                if source_file:
                    # ファイル名のみを抽出（パスを除去）
                    filename = Path(source_file).name
                    processed_files.add(filename)
            
            logger.info(f"処理済みファイル数: {len(processed_files)}")
            return processed_files
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"extraction_results_pure_english.jsonの読み込みエラー: {e}")
            return set()
    
    def get_pdf_files(self) -> List[Path]:
        """
        PDFフォルダ内のPDFファイル一覧を取得
        
        Returns:
            PDFファイルのパスのリスト
        """
        if not self.pdf_folder.exists():
            logger.error(f"PDFフォルダが存在しません: {self.pdf_folder}")
            return []
        
        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        logger.info(f"PDFフォルダ内のファイル数: {len(pdf_files)}")
        return pdf_files
    
    def detect_unprocessed_files(self) -> List[Path]:
        """
        未処理のPDFファイルを検出
        
        Returns:
            未処理PDFファイルのパスのリスト
        """
        processed_files = self.get_processed_files()
        pdf_files = self.get_pdf_files()
        
        unprocessed_files = []
        for pdf_file in pdf_files:
            if pdf_file.name not in processed_files:
                unprocessed_files.append(pdf_file)
        
        logger.info(f"未処理ファイル数: {len(unprocessed_files)}")
        for file in unprocessed_files:
            logger.info(f"  📄 未処理: {file.name}")
        
        return unprocessed_files
    
    def process_single_file(self, pdf_file: Path) -> Dict:
        """
        単一PDFファイルをOCR処理
        
        Args:
            pdf_file: 処理するPDFファイルのパス
            
        Returns:
            抽出結果の辞書
        """
        logger.info(f"🚀 OCR処理開始: {pdf_file.name}")
        
        try:
            # OCR処理実行
            extracted_data = self.extractor.process_pdf(
                str(pdf_file), 
                enhancement_level="aggressive"
            )
            
            if extracted_data and extracted_data.get('extracted_words'):
                logger.info(f"✅ OCR処理完了: {pdf_file.name} - {len(extracted_data['extracted_words'])}語抽出")
                return extracted_data
            else:
                logger.warning(f"⚠️  OCR処理で有効な英語が抽出されませんでした: {pdf_file.name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ OCR処理エラー: {pdf_file.name} - {str(e)}")
            return None
    
    def append_to_extraction_results(self, new_data: Dict) -> bool:
        """
        新しいデータをextraction_results_pure_english.jsonに追記
        
        Args:
            new_data: 追加するデータ
            
        Returns:
            成功したかどうか
        """
        try:
            # 既存データを読み込み
            if self.extraction_results_file.exists():
                with open(self.extraction_results_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                # 新規作成
                existing_data = {
                    "extraction_summary": {
                        "total_source_files": 0,
                        "total_words_extracted": 0,
                        "average_ocr_confidence": 0.0,
                        "processing_level": "aggressive",
                        "extraction_method": "pure_english_only",
                        "japanese_content": "completely_ignored"
                    },
                    "extracted_data": []
                }
            
            # 新しいデータを追加
            existing_data["extracted_data"].append(new_data)
            
            # サマリーを更新
            all_entries = existing_data["extracted_data"]
            total_files = len(all_entries)
            total_words = sum(entry.get("word_count", 0) for entry in all_entries)
            confidences = [entry.get("ocr_confidence", 0.0) for entry in all_entries if entry.get("ocr_confidence")]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            existing_data["extraction_summary"].update({
                "total_source_files": total_files,
                "total_words_extracted": total_words,
                "average_ocr_confidence": avg_confidence
            })
            
            # ファイルに保存
            with open(self.extraction_results_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ データ追記完了: {new_data['source_file']}")
            logger.info(f"   📊 現在の総ファイル数: {total_files}")
            logger.info(f"   📈 現在の総単語数: {total_words:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ データ追記エラー: {str(e)}")
            return False
    
    def run_vocabulary_analysis(self) -> bool:
        """
        語彙分析を実行
        
        Returns:
            成功したかどうか
        """
        try:
            logger.info("🔍 語彙分析開始...")
            self.analyzer.run_analysis()
            logger.info("✅ 語彙分析完了")
            return True
        except Exception as e:
            logger.error(f"❌ 語彙分析エラー: {str(e)}")
            return False
    
    def process_all_unprocessed(self) -> int:
        """
        すべての未処理ファイルを処理
        
        Returns:
            処理したファイル数
        """
        unprocessed_files = self.detect_unprocessed_files()
        
        if not unprocessed_files:
            logger.info("✅ 未処理ファイルはありません")
            return 0
        
        processed_count = 0
        
        for pdf_file in unprocessed_files:
            logger.info(f"📄 処理中 ({processed_count + 1}/{len(unprocessed_files)}): {pdf_file.name}")
            
            # OCR処理
            extracted_data = self.process_single_file(pdf_file)
            
            if extracted_data:
                # データ追記
                if self.append_to_extraction_results(extracted_data):
                    processed_count += 1
                else:
                    logger.error(f"❌ データ追記失敗: {pdf_file.name}")
            else:
                logger.warning(f"⚠️  処理スキップ: {pdf_file.name}")
        
        if processed_count > 0:
            logger.info(f"🔍 新しいファイルが追加されたため語彙分析を実行します...")
            self.run_vocabulary_analysis()
        
        logger.info(f"🎉 処理完了: {processed_count}/{len(unprocessed_files)} ファイルを処理しました")
        return processed_count


def main():
    """メイン処理"""
    print("🚀 増分PDFプロセッサー開始")
    print("=" * 60)
    
    processor = IncrementalProcessor()
    
    # 未処理ファイルの検出と処理
    processed_count = processor.process_all_unprocessed()
    
    if processed_count > 0:
        print(f"\n✅ {processed_count} ファイルの処理が完了しました")
        print("📊 最新の分析結果:")
        print("   • extraction_results_pure_english.json - 抽出データ")
        print("   • multi_vocabulary_analysis_report.json - 語彙分析結果")
    else:
        print("\n✅ すべてのファイルは既に処理済みです")
    
    print("=" * 60)
    print("🎯 今後の使用方法:")
    print("   1. 新しいPDFファイルをPDF/フォルダに追加")
    print("   2. このスクリプト (python incremental_processor.py) を実行")
    print("   3. 自動的に未処理ファイルのみが処理されます")


if __name__ == "__main__":
    main()