#!/usr/bin/env python3
"""
データ処理ユーティリティ
既存の分析結果JSONをStreamlit用に軽量化・標準化
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def extract_streamlit_data(multi_vocab_report_path: str, output_path: str = None) -> Dict:
    """
    既存の複数単語帳分析レポートからStreamlit用データを抽出
    
    Args:
        multi_vocab_report_path: 複数単語帳分析レポートのパス
        output_path: 出力ファイルパス（Noneの場合は自動生成）
        
    Returns:
        Streamlit用の軽量化データ
    """
    
    # 元データ読み込み
    with open(multi_vocab_report_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # メタデータ抽出
    metadata = original_data.get('analysis_metadata', {})
    extraction_summary = metadata.get('extraction_summary', {})
    
    # 全体サマリー
    overall_summary = {
        "total_source_files": extraction_summary.get('total_source_files', 0),
        "total_words_extracted": extraction_summary.get('total_words_extracted', 0),
        "average_ocr_confidence": round(extraction_summary.get('average_ocr_confidence', 0) * 100, 2),
        "analysis_timestamp": metadata.get('analysis_timestamp', ''),
        "vocabulary_books": metadata.get('vocabulary_books', [])
    }
    
    # 複数単語帳カバレッジデータ
    vocab_coverage = original_data.get('multi_vocabulary_coverage', {}).get('vocabulary_coverage', {})
    
    # 単語帳別サマリー（軽量化）
    vocabulary_summary = {}
    for vocab_name, vocab_data in vocab_coverage.items():
        vocabulary_summary[vocab_name] = {
            "target_total_words": vocab_data.get('target_total_words', 0),
            "matched_words_count": vocab_data.get('matched_words_count', 0),
            "target_coverage_rate": vocab_data.get('target_coverage_rate', 0),
            "extraction_precision": vocab_data.get('extraction_precision', 0)
        }
    
    # 大学別分析データ
    university_analysis = original_data.get('university_analysis', {})
    
    # 大学別データの軽量化
    university_summary = {}
    for univ_name, univ_data in university_analysis.items():
        # 各単語帳のカバレッジデータを軽量化
        vocab_coverage_light = {}
        vocab_coverage_data = univ_data.get('vocabulary_coverage', {})
        
        for vocab_name, vocab_stats in vocab_coverage_data.items():
            vocab_coverage_light[vocab_name] = {
                "matched_words_count": vocab_stats.get('matched_words_count', 0),
                "target_coverage_rate": vocab_stats.get('target_coverage_rate', 0),
                "extraction_precision": vocab_stats.get('extraction_precision', 0)
            }
        
        university_summary[univ_name] = {
            "source_file": univ_data.get('source_file', ''),
            "total_words": univ_data.get('total_words', 0),
            "unique_words": univ_data.get('unique_words', 0),
            "ocr_confidence": round(univ_data.get('ocr_confidence', 0) * 100, 2),
            "pages_processed": univ_data.get('pages_processed', 0),
            "vocabulary_coverage": vocab_coverage_light
        }
    
    # 最頻出単語（上位10語のみ）
    word_frequencies = original_data.get('multi_vocabulary_coverage', {}).get('word_frequencies', {})
    top_words = dict(list(word_frequencies.items())[:10])
    
    # Streamlit用データ構造
    streamlit_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source_file": multi_vocab_report_path,
            "data_version": "1.0"
        },
        "overall_summary": overall_summary,
        "vocabulary_summary": vocabulary_summary,
        "university_analysis": university_summary,
        "top_frequent_words": top_words
    }
    
    # ファイル出力
    if output_path is None:
        output_path = "streamlit-vocab-analyzer/data/analysis_data.json"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(streamlit_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Streamlit用データを生成しました: {output_file}")
    print(f"📊 データサマリー:")
    print(f"  - 大学数: {len(university_summary)}")
    print(f"  - 単語帳数: {len(vocabulary_summary)}")
    print(f"  - 総単語数: {overall_summary['total_words_extracted']:,}")
    print(f"  - 平均OCR信頼度: {overall_summary['average_ocr_confidence']:.1f}%")
    
    return streamlit_data

def create_university_metadata():
    """
    大学・学部メタデータの作成
    """
    university_metadata = {
        "universities": {
            "早稲田大学_法学部": {
                "full_name": "早稲田大学 法学部",
                "short_name": "早稲田法",
                "category": "私立",
                "region": "関東",
                "color": "#8B0000"
            },
            "早稲田大学_政治経済学部": {
                "full_name": "早稲田大学 政治経済学部",
                "short_name": "早稲田政経",
                "category": "私立",
                "region": "関東", 
                "color": "#DC143C"
            },
            "東京大学": {
                "full_name": "東京大学",
                "short_name": "東大",
                "category": "国立",
                "region": "関東",
                "color": "#191970"
            }
        },
        "vocabulary_books": {
            "Target 1900": {"color": "#FF6B6B", "description": "定番の大学受験単語帳"},
            "Target 1400": {"color": "#4ECDC4", "description": "基礎レベル重視の単語帳"},
            "システム英単語": {"color": "#45B7D1", "description": "システマティックな学習"},
            "LEAP": {"color": "#96CEB4", "description": "4技能対応単語帳"},
            "鉄壁": {"color": "#FFEAA7", "description": "難関大学対策単語帳"}
        }
    }
    
    metadata_path = "streamlit-vocab-analyzer/data/university_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(university_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 大学メタデータを作成しました: {metadata_path}")
    return university_metadata

if __name__ == "__main__":
    # 既存データの変換
    input_file = "multi_vocabulary_analysis_report.json"
    
    print("🔄 Streamlit用データ変換開始...")
    
    # メインデータ変換
    streamlit_data = extract_streamlit_data(input_file)
    
    # メタデータ作成
    university_metadata = create_university_metadata()
    
    print("✅ データ変換完了！")