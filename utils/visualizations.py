#!/usr/bin/env python3
"""
可視化ユーティリティ
Plotly、Streamlit用のチャート生成関数
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional

def create_coverage_radar_chart(data: Dict, universities: List[str]) -> go.Figure:
    """
    複数大学の単語帳カバレッジ率レーダーチャート
    
    Args:
        data: 分析データ
        universities: 表示する大学リスト
        
    Returns:
        Plotlyレーダーチャート
    """
    fig = go.Figure()
    
    vocabulary_list = list(data.get('vocabulary_summary', {}).keys())
    university_data = data.get('university_analysis', {})
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    for i, university in enumerate(universities):
        univ_info = university_data.get(university, {})
        vocab_coverage = univ_info.get('vocabulary_coverage', {})
        
        # 各単語帳のカバレッジ率を取得
        coverage_rates = []
        for vocab in vocabulary_list:
            rate = vocab_coverage.get(vocab, {}).get('target_coverage_rate', 0)
            coverage_rates.append(rate)
        
        fig.add_trace(go.Scatterpolar(
            r=coverage_rates,
            theta=vocabulary_list,
            fill='toself',
            name=university,
            line_color=colors[i % len(colors)]
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(40, max([max(coverage_rates) for coverage_rates in [
                    [university_data.get(univ, {}).get('vocabulary_coverage', {}).get(vocab, {}).get('target_coverage_rate', 0) 
                     for vocab in vocabulary_list] for univ in universities
                ] if coverage_rates]))]
            )
        ),
        showlegend=True,
        title="大学別 単語帳カバレッジ率比較",
        height=500
    )
    
    return fig

def create_vocabulary_comparison_bar(data: Dict) -> go.Figure:
    """
    単語帳別カバレッジ率・抽出精度比較棒グラフ
    
    Args:
        data: 分析データ
        
    Returns:
        Plotly棒グラフ
    """
    vocab_data = data.get('vocabulary_summary', {})
    
    vocabularies = list(vocab_data.keys())
    coverage_rates = [vocab_data[vocab].get('target_coverage_rate', 0) for vocab in vocabularies]
    precision_rates = [vocab_data[vocab].get('extraction_precision', 0) for vocab in vocabularies]
    
    fig = go.Figure(data=[
        go.Bar(name='カバレッジ率', x=vocabularies, y=coverage_rates, marker_color='#FF6B6B'),
        go.Bar(name='抽出精度', x=vocabularies, y=precision_rates, marker_color='#4ECDC4')
    ])
    
    fig.update_layout(
        barmode='group',
        title='単語帳別 カバレッジ率・抽出精度比較',
        xaxis_title='単語帳',
        yaxis_title='率 (%)',
        height=400
    )
    
    return fig

def create_university_heatmap(data: Dict) -> go.Figure:
    """
    大学×単語帳のカバレッジ率ヒートマップ
    
    Args:
        data: 分析データ
        
    Returns:
        Plotlyヒートマップ
    """
    university_data = data.get('university_analysis', {})
    vocabulary_list = list(data.get('vocabulary_summary', {}).keys())
    university_list = list(university_data.keys())
    
    # 大学名を短縮表示用に変換
    def shorten_university_name(name):
        if "早稲田大学_" in name:
            return name.replace("早稲田大学_", "早大_")
        elif "東京大学" in name:
            return "東大"
        return name
    
    shortened_university_list = [shorten_university_name(univ) for univ in university_list]
    
    # ヒートマップ用データ作成
    heatmap_data = []
    for university in university_list:
        row = []
        vocab_coverage = university_data[university].get('vocabulary_coverage', {})
        for vocab in vocabulary_list:
            rate = vocab_coverage.get(vocab, {}).get('target_coverage_rate', 0)
            row.append(rate)
        heatmap_data.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=vocabulary_list,
        y=shortened_university_list,
        colorscale='RdYlBu_r',
        text=[[f"{val:.1f}%" for val in row] for row in heatmap_data],
        texttemplate="%{text}",
        textfont={"size": 9},
        hoverongaps=False,
        customdata=university_list,  # 元の大学名をホバー情報として保持
        hovertemplate='<b>%{customdata}</b><br>%{x}: %{z:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='大学×単語帳 カバレッジ率ヒートマップ',
        xaxis_title='単語帳',
        yaxis_title='大学・学部',
        height=max(400, len(university_list) * 25)  # 大学数に応じて高さを調整
    )
    
    return fig

def create_scatter_coverage_precision(data: Dict) -> go.Figure:
    """
    カバレッジ率 vs 抽出精度の散布図
    
    Args:
        data: 分析データ
        
    Returns:
        Plotly散布図
    """
    vocab_data = data.get('vocabulary_summary', {})
    
    fig = go.Figure()
    
    for vocab_name, vocab_info in vocab_data.items():
        coverage = vocab_info.get('target_coverage_rate', 0)
        precision = vocab_info.get('extraction_precision', 0)
        matched_words = vocab_info.get('matched_words_count', 0)
        
        fig.add_trace(go.Scatter(
            x=[coverage],
            y=[precision],
            mode='markers+text',
            text=[vocab_name],
            textposition="top center",
            marker=dict(
                size=matched_words/10,  # サイズは一致語数に比例
                opacity=0.7
            ),
            name=vocab_name,
            hovertemplate=f"<b>{vocab_name}</b><br>" +
                         f"カバレッジ率: {coverage:.1f}%<br>" +
                         f"抽出精度: {precision:.1f}%<br>" +
                         f"一致語数: {matched_words}<extra></extra>"
        ))
    
    fig.update_layout(
        title='単語帳 カバレッジ率 vs 抽出精度',
        xaxis_title='カバレッジ率 (%)',
        yaxis_title='抽出精度 (%)',
        showlegend=False,
        height=500
    )
    
    return fig

def create_ocr_confidence_gauge(confidence: float) -> go.Figure:
    """
    OCR信頼度ゲージチャート
    
    Args:
        confidence: OCR信頼度（0-100）
        
    Returns:
        Plotlyゲージチャート
    """
    # 色の決定
    if confidence >= 95:
        color = "#00ff00"  # 緑
    elif confidence >= 90:
        color = "#ffff00"  # 黄色
    else:
        color = "#ff0000"  # 赤
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "OCR信頼度"},
        delta = {'reference': 95},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 80], 'color': "lightgray"},
                {'range': [80, 90], 'color': "yellow"},
                {'range': [90, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig

def create_word_frequency_chart(word_freq_data: Dict, top_n: int = 10) -> go.Figure:
    """
    頻出単語棒グラフ
    
    Args:
        word_freq_data: 単語頻度データ
        top_n: 表示する単語数
        
    Returns:
        Plotly棒グラフ
    """
    # 上位N語を取得
    sorted_words = sorted(word_freq_data.items(), key=lambda x: x[1], reverse=True)[:top_n]
    words, frequencies = zip(*sorted_words) if sorted_words else ([], [])
    
    fig = go.Figure([go.Bar(
        x=list(words),
        y=list(frequencies),
        marker_color='#96CEB4'
    )])
    
    fig.update_layout(
        title=f'最頻出単語 TOP {top_n}',
        xaxis_title='単語',
        yaxis_title='出現回数',
        height=400
    )
    
    return fig

def create_performance_metrics_table(data: Dict, universities: List[str]) -> pd.DataFrame:
    """
    大学別パフォーマンステーブル作成
    
    Args:
        data: 分析データ
        universities: 対象大学リスト
        
    Returns:
        パフォーマンステーブルのDataFrame
    """
    university_data = data.get('university_analysis', {})
    
    table_data = []
    for university in universities:
        univ_info = university_data.get(university, {})
        vocab_coverage = univ_info.get('vocabulary_coverage', {})
        
        # 最高カバレッジ率を持つ単語帳を特定
        best_vocab = max(vocab_coverage.items(), 
                        key=lambda x: x[1].get('target_coverage_rate', 0)) if vocab_coverage else (None, {})
        
        table_data.append({
            '大学・学部': university,
            '総単語数': univ_info.get('total_words', 0),
            'ユニーク単語数': univ_info.get('unique_words', 0),
            'OCR信頼度(%)': univ_info.get('ocr_confidence', 0),
            '処理ページ数': univ_info.get('pages_processed', 0),
            '最適単語帳': best_vocab[0] if best_vocab[0] else 'N/A',
            '最高カバレッジ率(%)': round(best_vocab[1].get('target_coverage_rate', 0), 1) if best_vocab[1] else 0
        })
    
    return pd.DataFrame(table_data)