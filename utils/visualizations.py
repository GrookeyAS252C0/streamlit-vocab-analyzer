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
    選択された大学の単語帳別カバレッジ率・抽出精度比較棒グラフ
    
    Args:
        data: 選択された大学のみのフィルタ済み分析データ
        
    Returns:
        Plotly棒グラフ
    """
    university_analysis = data.get('university_analysis', {})
    
    if not university_analysis:
        # データがない場合の空チャート
        fig = go.Figure()
        fig.add_annotation(
            text="選択された大学がありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(title='単語帳別 カバレッジ率・抽出精度比較', height=400)
        return fig
    
    # 選択された大学の語彙データを統合
    vocab_stats = {}
    total_words = 0
    
    # 重み付き平均の計算
    for univ_name, univ_data in university_analysis.items():
        univ_total_words = univ_data.get('total_words', 0)
        total_words += univ_total_words
        vocab_coverage = univ_data.get('vocabulary_coverage', {})
        
        for vocab_name, vocab_data in vocab_coverage.items():
            if vocab_name not in vocab_stats:
                vocab_stats[vocab_name] = {
                    'weighted_coverage': 0,
                    'weighted_precision': 0,
                    'total_matched': 0
                }
            
            coverage_rate = vocab_data.get('target_coverage_rate', 0)
            precision_rate = vocab_data.get('extraction_precision', 0)
            matched_count = vocab_data.get('matched_words_count', 0)
            
            vocab_stats[vocab_name]['weighted_coverage'] += coverage_rate * univ_total_words
            vocab_stats[vocab_name]['weighted_precision'] += precision_rate * univ_total_words
            vocab_stats[vocab_name]['total_matched'] += matched_count
    
    # 平均値を計算
    vocabularies = list(vocab_stats.keys())
    coverage_rates = []
    precision_rates = []
    
    for vocab_name in vocabularies:
        if total_words > 0:
            avg_coverage = vocab_stats[vocab_name]['weighted_coverage'] / total_words
            avg_precision = vocab_stats[vocab_name]['weighted_precision'] / total_words
        else:
            avg_coverage = 0
            avg_precision = 0
            
        coverage_rates.append(round(avg_coverage, 1))
        precision_rates.append(round(avg_precision, 1))
    
    fig = go.Figure(data=[
        go.Bar(name='カバレッジ率', x=vocabularies, y=coverage_rates, marker_color='#FF6B6B'),
        go.Bar(name='抽出精度', x=vocabularies, y=precision_rates, marker_color='#4ECDC4')
    ])
    
    fig.update_layout(
        barmode='group',
        title='選択大学の単語帳別 カバレッジ率・抽出精度比較',
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
    選択された大学の単語帳カバレッジ率 vs 抽出精度の散布図
    
    Args:
        data: 選択された大学のみのフィルタ済み分析データ
        
    Returns:
        Plotly散布図
    """
    university_analysis = data.get('university_analysis', {})
    
    if not university_analysis:
        # データがない場合の空チャート
        fig = go.Figure()
        fig.add_annotation(
            text="選択された大学がありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font_size=16
        )
        fig.update_layout(title='カバレッジ率 vs 抽出精度', height=500)
        return fig
    
    # 選択された大学の語彙データを統合
    vocab_stats = {}
    total_words = 0
    
    # 重み付き平均の計算
    for univ_name, univ_data in university_analysis.items():
        univ_total_words = univ_data.get('total_words', 0)
        total_words += univ_total_words
        vocab_coverage = univ_data.get('vocabulary_coverage', {})
        
        for vocab_name, vocab_data in vocab_coverage.items():
            if vocab_name not in vocab_stats:
                vocab_stats[vocab_name] = {
                    'weighted_coverage': 0,
                    'weighted_precision': 0,
                    'total_matched': 0
                }
            
            coverage_rate = vocab_data.get('target_coverage_rate', 0)
            precision_rate = vocab_data.get('extraction_precision', 0)
            matched_count = vocab_data.get('matched_words_count', 0)
            
            vocab_stats[vocab_name]['weighted_coverage'] += coverage_rate * univ_total_words
            vocab_stats[vocab_name]['weighted_precision'] += precision_rate * univ_total_words
            vocab_stats[vocab_name]['total_matched'] += matched_count
    
    fig = go.Figure()
    
    for vocab_name, stats in vocab_stats.items():
        if total_words > 0:
            avg_coverage = stats['weighted_coverage'] / total_words
            avg_precision = stats['weighted_precision'] / total_words
        else:
            avg_coverage = 0
            avg_precision = 0
            
        matched_words = stats['total_matched']
        
        fig.add_trace(go.Scatter(
            x=[avg_coverage],
            y=[avg_precision],
            mode='markers+text',
            text=[vocab_name],
            textposition="top center",
            marker=dict(
                size=max(10, matched_words/20),  # サイズは一致語数に比例
                opacity=0.7
            ),
            name=vocab_name,
            hovertemplate=f"<b>{vocab_name}</b><br>" +
                         f"カバレッジ率: {avg_coverage:.1f}%<br>" +
                         f"抽出精度: {avg_precision:.1f}%<br>" +
                         f"一致語数: {matched_words}<extra></extra>"
        ))
    
    fig.update_layout(
        title='選択大学の単語帳 カバレッジ率 vs 抽出精度',
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

def create_sentence_statistics_chart(data: Dict) -> go.Figure:
    """
    大学別文章統計棒グラフ
    
    Args:
        data: 分析データ
        
    Returns:
        Plotly棒グラフ
    """
    university_data = data.get('university_analysis', {})
    universities = []
    sentences = []
    avg_words = []
    
    for univ, info in university_data.items():
        universities.append(univ.replace('早稲田大学_', '早大_'))  # 短縮表示
        sentences.append(info.get('total_sentences', 0))
        avg_words.append(info.get('avg_words_per_sentence', 0))
    
    # サブプロット作成
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('文の数', '1文あたりの平均語数'),
        vertical_spacing=0.15
    )
    
    # 文の数
    fig.add_trace(
        go.Bar(x=universities, y=sentences, name='文の数', marker_color='#4ECDC4'),
        row=1, col=1
    )
    
    # 1文あたりの平均語数
    fig.add_trace(
        go.Bar(x=universities, y=avg_words, name='平均語数/文', marker_color='#96CEB4'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="大学別文章統計"
    )
    
    # X軸ラベルを斜めに
    fig.update_xaxes(tickangle=45)
    
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