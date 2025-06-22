#!/usr/bin/env python3
"""
最新のOCR結果と語彙分析結果からStreamlit用データを生成
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

def extract_university_name(source_file):
    """ファイル名から大学・学部名を抽出"""
    filename = Path(source_file).stem
    
    # 大学名・学部名の抽出パターン
    if "早稲田大学" in filename:
        if "法学部" in filename:
            return "早稲田大学_法学部"
        elif "政治経済学部" in filename:
            return "早稲田大学_政治経済学部"
        elif "商学部" in filename:
            return "早稲田大学_商学部"
        elif "文学部" in filename:
            return "早稲田大学_文学部"
        elif "文化構想学部" in filename:
            return "早稲田大学_文化構想学部"
        elif "教育学部" in filename:
            return "早稲田大学_教育学部"
        elif "社会科学部" in filename:
            return "早稲田大学_社会科学部"
        elif "人間科学部" in filename:
            return "早稲田大学_人間科学部"
        elif "国際教養学部" in filename:
            return "早稲田大学_国際教養学部"
        elif "理工学部" in filename or "基幹理工" in filename:
            return "早稲田大学_理工学部"
    elif "東京大学" in filename:
        return "東京大学"
    
    return filename

def load_extraction_results():
    """OCR抽出結果の読み込み"""
    extraction_file = "/Users/takashikemmoku/Desktop/wordsearch/extraction_results_pure_english.json"
    if not os.path.exists(extraction_file):
        print(f"❌ OCR結果ファイルが見つかりません: {extraction_file}")
        return None
    
    try:
        with open(extraction_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ OCR結果読み込みエラー: {e}")
        return None

def load_vocabulary_analysis():
    """語彙分析結果の読み込み"""
    vocab_file = "/Users/takashikemmoku/Desktop/wordsearch/multi_vocabulary_analysis_report.json"
    if not os.path.exists(vocab_file):
        print(f"❌ 語彙分析ファイルが見つかりません: {vocab_file}")
        return None
    
    try:
        with open(vocab_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 語彙分析読み込みエラー: {e}")
        return None

def calculate_sentence_stats(english_passages):
    """英文パッセージから文の統計を計算"""
    if not english_passages:
        return {"total_sentences": 0, "avg_words_per_sentence": 0.0, "total_words_in_sentences": 0}
    
    total_sentences = 0
    total_words = 0
    
    for passage in english_passages:
        # 文を分割（.、!、?で終わる文を検出）
        sentences = re.split(r'[.!?]+', passage)
        # 空文字列を除去し、意味のある文のみカウント（短すぎる文は除外）
        valid_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        total_sentences += len(valid_sentences)
        
        # 各文の単語数をカウント
        for sentence in valid_sentences:
            words = sentence.split()
            total_words += len(words)
    
    avg_words_per_sentence = total_words / total_sentences if total_sentences > 0 else 0.0
    
    return {
        "total_sentences": total_sentences,
        "avg_words_per_sentence": round(avg_words_per_sentence, 1),
        "total_words_in_sentences": total_words
    }

def create_streamlit_data():
    """Streamlit用データ作成"""
    print("🔄 Streamlit用データ生成開始...")
    
    # データ読み込み
    extraction_data = load_extraction_results()
    vocab_data = load_vocabulary_analysis()
    
    if not extraction_data or not vocab_data:
        return False
    
    # 基本構造作成
    streamlit_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source_files": ["extraction_results_pure_english.json", "multi_vocabulary_analysis_report.json"],
            "data_version": "2.0"
        }
    }
    
    # overall_summary作成
    extraction_summary = extraction_data.get("extraction_summary", {})
    streamlit_data["overall_summary"] = {
        "total_source_files": extraction_summary.get("total_source_files", 0),
        "total_words_extracted": extraction_summary.get("total_words_extracted", 0),
        "average_ocr_confidence": round(extraction_summary.get("average_ocr_confidence", 0) * 100, 2),
        "analysis_timestamp": datetime.now().isoformat(),
        "vocabulary_books": ["Target 1900", "Target 1400", "システム英単語", "LEAP", "鉄壁"]
    }
    
    # vocabulary_summary作成
    multi_vocab_coverage = vocab_data.get("multi_vocabulary_coverage", {})
    vocab_coverage = multi_vocab_coverage.get("vocabulary_coverage", {})
    streamlit_data["vocabulary_summary"] = vocab_coverage
    
    # university_analysis作成
    university_analysis = {}
    extracted_data = extraction_data.get("extracted_data", [])
    university_vocab_data = vocab_data.get("university_analysis", {})
    
    print(f"🔍 語彙分析データの大学キー: {list(university_vocab_data.keys())}")
    
    for item in extracted_data:
        source_file = item.get("source_file", "")
        university_name = extract_university_name(source_file)
        
        # 文章統計を計算
        english_passages = item.get("english_passages", [])
        sentence_stats = calculate_sentence_stats(english_passages)
        
        
        # OCRデータ
        ocr_info = {
            "source_file": source_file,
            "total_words": item.get("word_count", 0),
            "unique_words": len(item.get("extracted_words", [])),
            "ocr_confidence": round(item.get("ocr_confidence", 0) * 100, 2),
            "pages_processed": item.get("pages_processed", 0),
            "total_sentences": sentence_stats["total_sentences"],
            "avg_words_per_sentence": sentence_stats["avg_words_per_sentence"]
        }
        
        # 語彙分析データを統合（複数のキー形式を試行）
        vocab_coverage = None
        potential_keys = [
            university_name,  # 早稲田大学_法学部
            university_name.split('_')[0],  # 早稲田大学
            source_file.replace('.pdf', ''),  # 元ファイル名
            source_file  # PDFファイル名
        ]
        
        for key in potential_keys:
            if key in university_vocab_data:
                vocab_coverage = university_vocab_data[key].get("vocabulary_coverage", {})
                print(f"✅ マッチ: {university_name} -> {key}")
                break
        
        if vocab_coverage:
            ocr_info["vocabulary_coverage"] = vocab_coverage
        else:
            print(f"⚠️  語彙データなし: {university_name}")
            # デフォルトの語彙カバレッジ（データがない場合）
            ocr_info["vocabulary_coverage"] = {
                "Target 1900": {"matched_words_count": 0, "target_coverage_rate": 0.0, "extraction_precision": 0.0},
                "Target 1400": {"matched_words_count": 0, "target_coverage_rate": 0.0, "extraction_precision": 0.0},
                "システム英単語": {"matched_words_count": 0, "target_coverage_rate": 0.0, "extraction_precision": 0.0},
                "LEAP": {"matched_words_count": 0, "target_coverage_rate": 0.0, "extraction_precision": 0.0},
                "鉄壁": {"matched_words_count": 0, "target_coverage_rate": 0.0, "extraction_precision": 0.0}
            }
        
        university_analysis[university_name] = ocr_info
    
    streamlit_data["university_analysis"] = university_analysis
    
    # 全体の文章統計を計算
    total_sentences = sum([info.get("total_sentences", 0) for info in university_analysis.values()])
    total_words_in_sentences = sum([info.get("avg_words_per_sentence", 0) * info.get("total_sentences", 0) for info in university_analysis.values()])
    overall_avg_words = total_words_in_sentences / total_sentences if total_sentences > 0 else 0
    
    streamlit_data["sentence_statistics"] = {
        "total_sentences": total_sentences,
        "overall_avg_words_per_sentence": round(overall_avg_words, 1)
    }
    
    
    # データ保存
    output_file = "../data/analysis_data.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(streamlit_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Streamlit用データ生成完了: {output_file}")
        print(f"📊 大学数: {len(university_analysis)}")
        print(f"📚 単語帳数: {len(streamlit_data['vocabulary_summary'])}")
        print(f"📈 総単語数: {streamlit_data['overall_summary']['total_words_extracted']:,}")
        
        # 大学リスト表示
        print("\n🏫 含まれる大学・学部:")
        for i, univ in enumerate(university_analysis.keys(), 1):
            print(f"  {i}. {univ}")
        
        return True
        
    except Exception as e:
        print(f"❌ データ保存エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 Streamlit用データ処理開始")
    
    if create_streamlit_data():
        print("\n🎉 処理完了!")
    else:
        print("\n❌ 処理失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()