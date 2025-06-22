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
    elif "慶應義塾大学" in filename:
        if "医学部" in filename:
            return "慶應義塾大学_医学部"
        elif "薬学部" in filename:
            return "慶應義塾大学_薬学部"
        elif "経済学部" in filename:
            return "慶應義塾大学_経済学部"
        elif "商学部" in filename:
            return "慶應義塾大学_商学部"
        elif "法学部" in filename:
            return "慶應義塾大学_法学部"
        elif "文学部" in filename:
            return "慶應義塾大学_文学部"
        elif "理工学部" in filename:
            return "慶應義塾大学_理工学部"
        elif "環境情報学部" in filename:
            return "慶應義塾大学_環境情報学部"
        elif "総合政策学部" in filename:
            return "慶應義塾大学_総合政策学部"
        elif "看護医療学部" in filename:
            return "慶應義塾大学_看護医療学部"
    
    return filename

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

def create_university_consolidated_data(university_analysis):
    """大学統合データを生成（学部データを統合）"""
    consolidated = {}
    
    # 大学ごとにグループ化
    university_groups = {}
    for univ_name, univ_data in university_analysis.items():
        if "_" in univ_name:
            base_univ = univ_name.split("_")[0]
        else:
            base_univ = univ_name
        
        if base_univ not in university_groups:
            university_groups[base_univ] = []
        university_groups[base_univ].append((univ_name, univ_data))
    
    # 複数学部がある大学のみ統合データを作成
    for base_univ, departments in university_groups.items():
        if len(departments) > 1:  # 複数学部がある場合のみ
            print(f"🔄 {base_univ}の統合データを作成中... ({len(departments)}学部)")
            
            # 基本統計の合算
            total_words = sum([data.get("total_words", 0) for _, data in departments])
            total_unique_words = sum([data.get("unique_words", 0) for _, data in departments])
            total_pages = sum([data.get("pages_processed", 0) for _, data in departments])
            total_sentences = sum([data.get("total_sentences", 0) for _, data in departments])
            
            # 平均値の計算
            avg_confidence = sum([data.get("ocr_confidence", 0) for _, data in departments]) / len(departments)
            total_words_in_sentences = sum([data.get("avg_words_per_sentence", 0) * data.get("total_sentences", 0) for _, data in departments])
            avg_words_per_sentence = total_words_in_sentences / total_sentences if total_sentences > 0 else 0
            
            # 語彙カバレッジの統合（重み付き平均）
            vocabulary_coverage = {}
            for vocab_name in ["Target 1900", "Target 1400", "システム英単語", "LEAP", "鉄壁"]:
                total_matched = 0
                weighted_coverage = 0
                weighted_precision = 0
                total_weight = 0
                
                for _, data in departments:
                    dept_coverage = data.get("vocabulary_coverage", {}).get(vocab_name, {})
                    matched_count = dept_coverage.get("matched_words_count", 0)
                    coverage_rate = dept_coverage.get("target_coverage_rate", 0)
                    precision = dept_coverage.get("extraction_precision", 0)
                    dept_words = data.get("total_words", 0)
                    
                    total_matched += matched_count
                    if dept_words > 0:
                        weighted_coverage += coverage_rate * dept_words
                        weighted_precision += precision * dept_words
                        total_weight += dept_words
                
                # 重み付き平均を計算
                avg_coverage = weighted_coverage / total_weight if total_weight > 0 else 0
                avg_precision = weighted_precision / total_weight if total_weight > 0 else 0
                
                vocabulary_coverage[vocab_name] = {
                    "matched_words_count": total_matched,
                    "target_coverage_rate": round(avg_coverage, 2),
                    "extraction_precision": round(avg_precision, 2)
                }
            
            # 統合データを作成
            consolidated_key = f"{base_univ}（全学部）"
            consolidated[consolidated_key] = {
                "source_file": f"{base_univ}_統合データ",
                "total_words": total_words,
                "unique_words": total_unique_words,
                "ocr_confidence": round(avg_confidence, 2),
                "pages_processed": total_pages,
                "total_sentences": total_sentences,
                "avg_words_per_sentence": round(avg_words_per_sentence, 1),
                "vocabulary_coverage": vocabulary_coverage,
                "is_consolidated": True,  # 統合データフラグ
                "department_count": len(departments),
                "departments": [name for name, _ in departments]
            }
            
            print(f"✅ {consolidated_key}: {len(departments)}学部統合完了")
    
    return consolidated

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
    
    # overall_summary作成（実際の集計データから計算）
    extraction_summary = extraction_data.get("extraction_summary", {})
    
    # 実データから統計を計算
    extracted_data = extraction_data.get("extracted_data", [])
    
    # 各アイテムから単語数を計算
    total_words_calculated = 0
    for item in extracted_data:
        extracted_words_count = len(item.get("extracted_words", []))
        # 文章統計がある場合はそれも考慮
        if "total_sentences" in item and "avg_words_per_sentence" in item:
            sentence_word_count = int(item.get("total_sentences", 0) * item.get("avg_words_per_sentence", 0))
            total_words_calculated += max(extracted_words_count, sentence_word_count)
        else:
            total_words_calculated += extracted_words_count
    
    total_files = len(extracted_data)
    
    # OCR信頼度の計算（0でない値のみ）
    ocr_confidences = [item.get("ocr_confidence", 0) for item in extracted_data if item.get("ocr_confidence", 0) > 0]
    avg_ocr_confidence = sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 0
    
    streamlit_data["overall_summary"] = {
        "total_source_files": total_files,
        "total_words_extracted": total_words_calculated,
        "average_ocr_confidence": round(avg_ocr_confidence * 100, 2) if avg_ocr_confidence < 1 else round(avg_ocr_confidence, 2),
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
        
        # 文章統計を取得または計算
        if "total_sentences" in item and "avg_words_per_sentence" in item:
            # 既に計算済みの場合はそれを使用
            sentence_stats = {
                "total_sentences": item.get("total_sentences", 0),
                "avg_words_per_sentence": item.get("avg_words_per_sentence", 0.0)
            }
        else:
            # 未計算の場合は新たに計算
            english_passages = item.get("english_passages", []) or item.get("pure_english_text", [])
            sentence_stats = calculate_sentence_stats(english_passages)
        
        # 単語数の計算（extracted_wordsの数とavg_words_per_sentence * total_sentencesの最大値を使用）
        extracted_words_count = len(item.get("extracted_words", []))
        sentence_word_count = int(sentence_stats["total_sentences"] * sentence_stats["avg_words_per_sentence"])
        total_words = max(extracted_words_count, sentence_word_count)
        
        # OCRデータ
        ocr_info = {
            "source_file": source_file,
            "total_words": total_words,
            "unique_words": extracted_words_count,
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
    
    # 大学統合データを生成
    university_consolidated = create_university_consolidated_data(university_analysis)
    print(f"🔍 統合データ生成結果: {len(university_consolidated)}件")
    for key in university_consolidated.keys():
        print(f"  - {key}")
    
    # 学部別データと統合データを結合
    combined_analysis = {**university_analysis, **university_consolidated}
    print(f"🔍 結合後データ: 学部{len(university_analysis)} + 統合{len(university_consolidated)} = 総計{len(combined_analysis)}")
    streamlit_data["university_analysis"] = combined_analysis
    
    # 全体の文章統計を計算（学部別データのみを使用）
    total_sentences = sum([info.get("total_sentences", 0) for info in university_analysis.values()])
    total_words_in_sentences = sum([info.get("avg_words_per_sentence", 0) * info.get("total_sentences", 0) for info in university_analysis.values()])
    overall_avg_words = total_words_in_sentences / total_sentences if total_sentences > 0 else 0
    
    streamlit_data["sentence_statistics"] = {
        "total_sentences": total_sentences,
        "overall_avg_words_per_sentence": round(overall_avg_words, 1)
    }
    
    # データ保存
    output_file = "data/analysis_data.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(streamlit_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Streamlit用データ生成完了: {output_file}")
        print(f"📊 学部別データ: {len(university_analysis)}")
        print(f"🏫 統合データ: {len(university_consolidated)}")
        print(f"📊 総エントリ数: {len(combined_analysis)}")
        print(f"📚 単語帳数: {len(streamlit_data['vocabulary_summary'])}")
        print(f"📈 総単語数: {streamlit_data['overall_summary']['total_words_extracted']:,}")
        print(f"📝 総文数: {streamlit_data['sentence_statistics']['total_sentences']:,}")
        print(f"📖 平均語数/文: {streamlit_data['sentence_statistics']['overall_avg_words_per_sentence']:.1f}")
        
        # 学部別データ表示
        print("\n🏫 学部別データ:")
        for i, univ in enumerate(university_analysis.keys(), 1):
            sentences = university_analysis[univ].get('total_sentences', 0)
            avg_words = university_analysis[univ].get('avg_words_per_sentence', 0)
            print(f"  {i}. {univ}: {sentences}文, {avg_words:.1f}語/文")
        
        # 統合データ表示
        if university_consolidated:
            print("\n🏛️ 大学統合データ:")
            for i, (univ, data) in enumerate(university_consolidated.items(), 1):
                sentences = data.get('total_sentences', 0)
                avg_words = data.get('avg_words_per_sentence', 0)
                dept_count = data.get('department_count', 0)
                print(f"  {i}. {univ}: {sentences}文, {avg_words:.1f}語/文 ({dept_count}学部統合)")
        
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