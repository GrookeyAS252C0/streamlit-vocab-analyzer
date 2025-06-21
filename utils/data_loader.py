#!/usr/bin/env python3
"""
Streamlit用データ読み込みユーティリティ
"""

import json
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, List, Tuple, Optional

@st.cache_data
def load_analysis_data(data_path: str = "data/analysis_data.json") -> Dict:
    """
    分析データの読み込み（キャッシュ付き）
    
    Args:
        data_path: データファイルのパス
        
    Returns:
        分析データ辞書
    """
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"データファイルが見つかりません: {data_path}")
        return {}
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return {}

@st.cache_data
def load_university_metadata(metadata_path: str = "data/university_metadata.json") -> Dict:
    """
    大学メタデータの読み込み（キャッシュ付き）
    
    Args:
        metadata_path: メタデータファイルのパス
        
    Returns:
        大学メタデータ辞書
    """
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
    except FileNotFoundError:
        st.error(f"メタデータファイルが見つかりません: {metadata_path}")
        return {"universities": {}, "vocabulary_books": {}}
    except Exception as e:
        st.error(f"メタデータ読み込みエラー: {e}")
        return {"universities": {}, "vocabulary_books": {}}

def get_university_list(data: Dict) -> List[str]:
    """
    大学・学部リストの取得
    
    Args:
        data: 分析データ
        
    Returns:
        大学・学部名のリスト
    """
    return list(data.get('university_analysis', {}).keys())

def get_vocabulary_list(data: Dict) -> List[str]:
    """
    単語帳リストの取得
    
    Args:
        data: 分析データ
        
    Returns:
        単語帳名のリスト
    """
    return list(data.get('vocabulary_summary', {}).keys())

def create_university_dataframe(data: Dict) -> pd.DataFrame:
    """
    大学別データのDataFrame作成
    
    Args:
        data: 分析データ
        
    Returns:
        大学別データのDataFrame
    """
    university_data = data.get('university_analysis', {})
    
    df_data = []
    for univ_name, univ_info in university_data.items():
        row = {
            'university': univ_name,
            'total_words': univ_info.get('total_words', 0),
            'unique_words': univ_info.get('unique_words', 0),
            'ocr_confidence': univ_info.get('ocr_confidence', 0),
            'pages_processed': univ_info.get('pages_processed', 0)
        }
        
        # 各単語帳のデータを追加
        vocab_coverage = univ_info.get('vocabulary_coverage', {})
        for vocab_name, vocab_stats in vocab_coverage.items():
            row[f'{vocab_name}_coverage'] = vocab_stats.get('target_coverage_rate', 0)
            row[f'{vocab_name}_precision'] = vocab_stats.get('extraction_precision', 0)
            row[f'{vocab_name}_matched'] = vocab_stats.get('matched_words_count', 0)
        
        df_data.append(row)
    
    return pd.DataFrame(df_data)

def create_vocabulary_dataframe(data: Dict) -> pd.DataFrame:
    """
    単語帳別データのDataFrame作成
    
    Args:
        data: 分析データ
        
    Returns:
        単語帳別データのDataFrame
    """
    vocabulary_data = data.get('vocabulary_summary', {})
    
    df_data = []
    for vocab_name, vocab_info in vocabulary_data.items():
        df_data.append({
            'vocabulary': vocab_name,
            'total_words': vocab_info.get('target_total_words', 0),
            'matched_words': vocab_info.get('matched_words_count', 0),
            'coverage_rate': vocab_info.get('target_coverage_rate', 0),
            'extraction_precision': vocab_info.get('extraction_precision', 0)
        })
    
    return pd.DataFrame(df_data)

def get_university_vocab_data(data: Dict, university: str, vocabulary: str) -> Dict:
    """
    特定の大学・単語帳の詳細データ取得
    
    Args:
        data: 分析データ
        university: 大学・学部名
        vocabulary: 単語帳名
        
    Returns:
        詳細データ辞書
    """
    university_data = data.get('university_analysis', {}).get(university, {})
    vocab_coverage = university_data.get('vocabulary_coverage', {})
    
    return vocab_coverage.get(vocabulary, {})

def calculate_summary_stats(data: Dict) -> Dict:
    """
    全体サマリー統計の計算
    
    Args:
        data: 分析データ
        
    Returns:
        サマリー統計辞書
    """
    overall = data.get('overall_summary', {})
    
    # 大学別統計
    university_data = data.get('university_analysis', {})
    
    total_pages = sum(univ.get('pages_processed', 0) for univ in university_data.values())
    avg_ocr_confidence = sum(univ.get('ocr_confidence', 0) for univ in university_data.values()) / len(university_data) if university_data else 0
    
    # 単語帳別最高カバレッジ率
    vocab_summary = data.get('vocabulary_summary', {})
    best_vocab = max(vocab_summary.items(), key=lambda x: x[1].get('target_coverage_rate', 0)) if vocab_summary else (None, {})
    
    return {
        'total_universities': len(university_data),
        'total_vocabulary_books': len(vocab_summary),
        'total_words_extracted': overall.get('total_words_extracted', 0),
        'total_pages_processed': total_pages,
        'average_ocr_confidence': round(avg_ocr_confidence, 1),
        'best_vocabulary': best_vocab[0],
        'best_coverage_rate': best_vocab[1].get('target_coverage_rate', 0) if best_vocab[1] else 0
    }

def filter_universities_by_criteria(data: Dict, min_coverage: float = 0, vocabulary: str = None) -> List[str]:
    """
    条件に基づく大学フィルタリング
    
    Args:
        data: 分析データ
        min_coverage: 最小カバレッジ率
        vocabulary: 対象単語帳（Noneの場合は全体）
        
    Returns:
        条件を満たす大学リスト
    """
    university_data = data.get('university_analysis', {})
    filtered_universities = []
    
    for univ_name, univ_info in university_data.items():
        vocab_coverage = univ_info.get('vocabulary_coverage', {})
        
        if vocabulary:
            # 特定単語帳でのフィルタリング
            vocab_stats = vocab_coverage.get(vocabulary, {})
            coverage_rate = vocab_stats.get('target_coverage_rate', 0)
            if coverage_rate >= min_coverage:
                filtered_universities.append(univ_name)
        else:
            # 全単語帳での最高カバレッジ率でフィルタリング
            max_coverage = max((stats.get('target_coverage_rate', 0) for stats in vocab_coverage.values()), default=0)
            if max_coverage >= min_coverage:
                filtered_universities.append(univ_name)
    
    return filtered_universities