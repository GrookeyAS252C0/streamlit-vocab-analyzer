#!/usr/bin/env python3
"""
ReadingAssist Analyzer - Simple Streamlit Web Application
最小限の依存関係で動作する軽量版
"""

import streamlit as st
import pandas as pd
import json
import re
from pathlib import Path

# Streamlit設定
st.set_page_config(
    page_title="ReadingAssist Analyzer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def simple_word_analysis(text):
    """シンプルな単語分析"""
    # 基本的な単語抽出
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    unique_words = set(words)
    
    # 基本統計
    total_words = len(words)
    unique_word_count = len(unique_words)
    
    # 文数計算
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    # 平均文長
    avg_sentence_length = total_words / sentence_count if sentence_count > 0 else 0
    
    # 単語頻度
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # 上位頻出単語
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'total_words': total_words,
        'unique_words': unique_word_count,
        'sentences': sentence_count,
        'avg_sentence_length': avg_sentence_length,
        'top_words': top_words,
        'vocabulary_diversity': unique_word_count / total_words if total_words > 0 else 0
    }

def estimate_difficulty(analysis):
    """難易度推定"""
    avg_length = analysis['avg_sentence_length']
    diversity = analysis['vocabulary_diversity']
    
    # 簡易難易度判定
    if avg_length < 10 and diversity > 0.7:
        return "易", 30
    elif avg_length < 15 and diversity > 0.5:
        return "やや易", 45
    elif avg_length < 20 and diversity > 0.4:
        return "中", 60
    elif avg_length < 25 and diversity > 0.3:
        return "やや難", 75
    else:
        return "難", 90

def main():
    """メイン関数"""
    
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>📚 ReadingAssist Analyzer</h1>
        <p>英文読解分析ツール（軽量版）</p>
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("📋 分析設定")
        
        # テキスト入力
        input_method = st.radio(
            "入力方法を選択",
            ["テキスト直接入力", "サンプルテキスト"]
        )
        
        if input_method == "テキスト直接入力":
            user_text = st.text_area(
                "分析したい英文を入力してください",
                height=200,
                placeholder="Enter English text here..."
            )
        else:
            sample_texts = {
                "学術文章": """
                The development of artificial intelligence has revolutionized numerous industries. 
                Machine learning algorithms can now process vast amounts of data to identify patterns 
                and make predictions with remarkable accuracy. However, the implementation of these 
                technologies requires careful consideration of ethical implications and potential 
                societal impacts.
                """,
                "ニュース記事": """
                Scientists have made a breakthrough in renewable energy technology. The new solar 
                panels demonstrate significantly improved efficiency rates compared to traditional 
                models. This advancement could accelerate the global transition to sustainable 
                energy sources and reduce dependence on fossil fuels.
                """,
                "小説": """
                The old lighthouse stood silently against the stormy sky. Sarah walked slowly 
                along the rocky shore, remembering the stories her grandmother used to tell. 
                The waves crashed violently against the cliffs, creating a symphony of natural 
                sounds that seemed to echo her inner thoughts.
                """
            }
            
            selected_sample = st.selectbox("サンプルを選択", list(sample_texts.keys()))
            user_text = sample_texts[selected_sample].strip()
            st.text_area("選択されたテキスト", value=user_text, height=150, disabled=True)
        
        # 分析実行ボタン
        analyze_button = st.button("🚀 分析実行", type="primary", use_container_width=True)
    
    # メインコンテンツ
    if analyze_button and user_text.strip():
        # 分析実行
        with st.spinner("分析を実行中..."):
            analysis = simple_word_analysis(user_text)
            difficulty, score = estimate_difficulty(analysis)
        
        st.success("分析が完了しました！")
        
        # 結果表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総単語数", f"{analysis['total_words']:,}")
        with col2:
            st.metric("ユニーク単語数", f"{analysis['unique_words']:,}")
        with col3:
            st.metric("文数", analysis['sentences'])
        with col4:
            st.metric("平均文長", f"{analysis['avg_sentence_length']:.1f}語")
        
        # 難易度評価
        st.subheader("📊 難易度評価")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("難易度レベル", difficulty)
        with col2:
            st.metric("難易度スコア", f"{score}/100")
        with col3:
            st.metric("語彙多様性", f"{analysis['vocabulary_diversity']:.3f}")
        
        # 頻出単語
        if analysis['top_words']:
            st.subheader("🔥 頻出単語 Top 10")
            
            # DataFrameで表示
            word_df = pd.DataFrame(analysis['top_words'], columns=['単語', '出現回数'])
            st.dataframe(word_df, use_container_width=True)
        
        # 詳細統計
        with st.expander("📋 詳細統計"):
            st.json({
                "基本統計": {
                    "総単語数": analysis['total_words'],
                    "ユニーク単語数": analysis['unique_words'],
                    "文数": analysis['sentences'],
                    "平均文長": round(analysis['avg_sentence_length'], 2)
                },
                "読解指標": {
                    "語彙多様性": round(analysis['vocabulary_diversity'], 3),
                    "難易度レベル": difficulty,
                    "難易度スコア": score
                }
            })
        
        # 学習アドバイス
        st.subheader("💡 学習アドバイス")
        
        if score < 40:
            st.info("""
            **初級レベル**: このテキストは比較的読みやすいです。
            - 基本的な文法構造の理解を深めましょう
            - 語彙力の基礎固めを継続しましょう
            """)
        elif score < 70:
            st.warning("""
            **中級レベル**: 適度な挑戦レベルです。
            - 複文の構造理解に取り組みましょう
            - 語彙の応用力を身につけましょう
            """)
        else:
            st.error("""
            **上級レベル**: 高度な読解力が必要です。
            - 高度な語彙・表現の習得が必要です
            - 複雑な文構造の分析練習をしましょう
            """)
    
    elif analyze_button:
        st.warning("分析するテキストを入力してください。")
    
    else:
        # ウェルカムページ
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            ### 🎯 ReadingAssist Analyzer へようこそ
            
            このアプリは英文テキストの読解難易度を分析し、学習に役立つ情報を提供します。
            
            **📊 分析機能:**
            - 語彙統計（単語数、語彙多様性）
            - 文構造分析（文数、平均文長）
            - 難易度評価（初級〜上級）
            - 頻出単語ランキング
            - 学習アドバイス
            
            **🚀 使い方:**
            左のサイドバーから英文を入力し、「分析実行」ボタンをクリックしてください。
            """)

if __name__ == "__main__":
    main()