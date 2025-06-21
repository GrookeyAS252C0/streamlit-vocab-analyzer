#!/usr/bin/env python3
"""
大学入試英単語分析 Streamlit アプリ
OCR処理結果の可視化・比較分析ダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import (
    load_analysis_data, 
    load_university_metadata,
    get_university_list,
    get_vocabulary_list,
    create_university_dataframe,
    create_vocabulary_dataframe,
    calculate_summary_stats
)
from utils.visualizations import (
    create_coverage_radar_chart,
    create_vocabulary_comparison_bar,
    create_university_heatmap,
    create_scatter_coverage_precision,
    create_ocr_confidence_gauge,
    create_word_frequency_chart,
    create_performance_metrics_table
)

# ページ設定
st.set_page_config(
    page_title="大学入試英単語分析ダッシュボード",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2E86AB;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """メイン関数"""
    
    # データ読み込み
    data = load_analysis_data()
    metadata = load_university_metadata()
    
    if not data:
        st.error("データの読み込みに失敗しました。")
        return
    
    # メインタイトル
    st.markdown('<div class="main-header">📚 大学入試英単語分析ダッシュボード</div>', unsafe_allow_html=True)
    
    # サイドバー
    setup_sidebar(data, metadata)
    
    # メインコンテンツ
    if st.session_state.get('page', 'overview') == 'overview':
        show_overview_page(data, metadata)
    elif st.session_state.get('page') == 'university':
        show_university_page(data, metadata)
    elif st.session_state.get('page') == 'comparison':
        show_comparison_page(data, metadata)

def setup_sidebar(data: dict, metadata: dict):
    """サイドバーの設定"""
    st.sidebar.title("📊 ナビゲーション")
    
    # ページ選択
    page = st.sidebar.radio(
        "ページを選択",
        ["overview", "university", "comparison"],
        format_func=lambda x: {
            "overview": "🏠 概要ダッシュボード",
            "university": "🏫 大学別詳細",
            "comparison": "⚖️ 比較分析"
        }[x]
    )
    st.session_state.page = page
    
    st.sidebar.markdown("---")
    
    # フィルター設定
    st.sidebar.subheader("🔍 フィルター")
    
    # 大学選択
    universities = get_university_list(data)
    selected_universities = st.sidebar.multiselect(
        "大学・学部を選択",
        universities,
        default=universities
    )
    st.session_state.selected_universities = selected_universities
    
    # 単語帳選択
    vocabularies = get_vocabulary_list(data)
    selected_vocabularies = st.sidebar.multiselect(
        "単語帳を選択",
        vocabularies,
        default=vocabularies
    )
    st.session_state.selected_vocabularies = selected_vocabularies
    
    # カバレッジ率閾値
    min_coverage = st.sidebar.slider(
        "最小カバレッジ率 (%)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=1.0
    )
    st.session_state.min_coverage = min_coverage
    
    st.sidebar.markdown("---")
    
    # データ情報
    st.sidebar.subheader("📋 データ情報")
    overall_summary = data.get('overall_summary', {})
    st.sidebar.write(f"**分析日時**: {overall_summary.get('analysis_timestamp', 'N/A')[:10]}")
    st.sidebar.write(f"**大学数**: {len(universities)}")
    st.sidebar.write(f"**単語帳数**: {len(vocabularies)}")
    st.sidebar.write(f"**総単語数**: {overall_summary.get('total_words_extracted', 0):,}")

def show_overview_page(data: dict, metadata: dict):
    """概要ダッシュボードページ"""
    st.markdown('<div class="sub-header">🏠 概要ダッシュボード</div>', unsafe_allow_html=True)
    
    # サマリー統計
    summary_stats = calculate_summary_stats(data)
    overall_summary = data.get('overall_summary', {})
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="総単語数",
            value=f"{overall_summary.get('total_words_extracted', 0):,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="平均OCR信頼度",
            value=f"{summary_stats.get('average_ocr_confidence', 0):.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            label="最適単語帳",
            value=summary_stats.get('best_vocabulary', 'N/A'),
            delta=f"{summary_stats.get('best_coverage_rate', 0):.1f}%"
        )
    
    with col4:
        st.metric(
            label="処理ページ数",
            value=f"{summary_stats.get('total_pages_processed', 0)}",
            delta=None
        )
    
    st.markdown("---")
    
    # チャート表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 単語帳別カバレッジ率・抽出精度")
        fig_vocab = create_vocabulary_comparison_bar(data)
        st.plotly_chart(fig_vocab, use_container_width=True)
    
    with col2:
        st.subheader("🎯 カバレッジ率 vs 抽出精度")
        fig_scatter = create_scatter_coverage_precision(data)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # ヒートマップ
    st.subheader("🔥 大学×単語帳 カバレッジ率ヒートマップ")
    fig_heatmap = create_university_heatmap(data)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 頻出単語
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 最頻出単語")
        word_freq_data = data.get('top_frequent_words', {})
        fig_words = create_word_frequency_chart(word_freq_data)
        st.plotly_chart(fig_words, use_container_width=True)
    
    with col2:
        st.subheader("⚡ OCR処理品質")
        avg_confidence = summary_stats.get('average_ocr_confidence', 0)
        fig_gauge = create_ocr_confidence_gauge(avg_confidence)
        st.plotly_chart(fig_gauge, use_container_width=True)

def show_university_page(data: dict, metadata: dict):
    """大学別詳細ページ"""
    st.markdown('<div class="sub-header">🏫 大学別詳細分析</div>', unsafe_allow_html=True)
    
    # 大学選択
    universities = get_university_list(data)
    selected_university = st.selectbox("詳細を表示する大学・学部を選択", universities)
    
    if not selected_university:
        st.warning("大学を選択してください。")
        return
    
    university_data = data.get('university_analysis', {}).get(selected_university, {})
    university_meta = metadata.get('universities', {}).get(selected_university, {})
    
    # 大学情報カード
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **🏫 {university_meta.get('full_name', selected_university)}**
        - 分類: {university_meta.get('category', 'N/A')}
        - 地域: {university_meta.get('region', 'N/A')}
        """)
    
    with col2:
        st.info(f"""
        **📊 処理統計**
        - 総単語数: {university_data.get('total_words', 0):,}
        - ユニーク語数: {university_data.get('unique_words', 0):,}
        - 処理ページ: {university_data.get('pages_processed', 0)}
        """)
    
    with col3:
        ocr_confidence = university_data.get('ocr_confidence', 0)
        confidence_color = "🟢" if ocr_confidence >= 95 else "🟡" if ocr_confidence >= 90 else "🔴"
        st.info(f"""
        **⚡ OCR品質**
        - 信頼度: {confidence_color} {ocr_confidence:.1f}%
        - ファイル: {university_data.get('source_file', 'N/A').split('/')[-1]}
        """)
    
    st.markdown("---")
    
    # 単語帳別詳細
    st.subheader("📚 単語帳別パフォーマンス")
    
    vocab_coverage = university_data.get('vocabulary_coverage', {})
    vocab_df_data = []
    
    for vocab_name, vocab_stats in vocab_coverage.items():
        vocab_df_data.append({
            '単語帳': vocab_name,
            '一致語数': vocab_stats.get('matched_words_count', 0),
            'カバレッジ率(%)': round(vocab_stats.get('target_coverage_rate', 0), 1),
            '抽出精度(%)': round(vocab_stats.get('extraction_precision', 0), 1)
        })
    
    vocab_df = pd.DataFrame(vocab_df_data)
    
    # スタイル付きテーブル
    try:
        st.dataframe(
            vocab_df.style.format({
                'カバレッジ率(%)': '{:.1f}',
                '抽出精度(%)': '{:.1f}'
            }).background_gradient(subset=['カバレッジ率(%)', '抽出精度(%)'], cmap='RdYlGn'),
            use_container_width=True
        )
    except ImportError:
        # matplotlibが利用できない場合のフォールバック
        st.dataframe(
            vocab_df.style.format({
                'カバレッジ率(%)': '{:.1f}',
                '抽出精度(%)': '{:.1f}'
            }),
            use_container_width=True
        )
    
    # 単語帳比較チャート
    if len(vocab_df_data) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_coverage = px.bar(
                vocab_df, 
                x='単語帳', 
                y='カバレッジ率(%)',
                title='単語帳別カバレッジ率',
                color='カバレッジ率(%)',
                color_continuous_scale='RdYlGn'
            )
            fig_coverage.update_layout(height=400)
            st.plotly_chart(fig_coverage, use_container_width=True)
        
        with col2:
            fig_precision = px.bar(
                vocab_df, 
                x='単語帳', 
                y='抽出精度(%)',
                title='単語帳別抽出精度',
                color='抽出精度(%)',
                color_continuous_scale='RdYlBu'
            )
            fig_precision.update_layout(height=400)
            st.plotly_chart(fig_precision, use_container_width=True)

def show_comparison_page(data: dict, metadata: dict):
    """比較分析ページ"""
    st.markdown('<div class="sub-header">⚖️ 比較分析</div>', unsafe_allow_html=True)
    
    # 比較対象選択
    universities = get_university_list(data)
    selected_universities = st.multiselect(
        "比較する大学・学部を選択（2つ以上）",
        universities,
        default=universities[:3] if len(universities) >= 3 else universities
    )
    
    if len(selected_universities) < 2:
        st.warning("比較には2つ以上の大学を選択してください。")
        return
    
    # 比較分析タブ
    tab1, tab2, tab3 = st.tabs(["📊 レーダーチャート", "📋 詳細テーブル", "🎯 ランキング"])
    
    with tab1:
        st.subheader("🕸️ 大学別単語帳カバレッジ率レーダーチャート")
        fig_radar = create_coverage_radar_chart(data, selected_universities)
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.info("""
        **📖 読み方**: 
        - 外側に向かうほど高いカバレッジ率
        - 各軸は単語帳を表す
        - 色分けで大学を区別
        """)
    
    with tab2:
        st.subheader("📊 大学別パフォーマンス詳細テーブル")
        performance_df = create_performance_metrics_table(data, selected_universities)
        
        try:
            st.dataframe(
                performance_df.style.format({
                    'OCR信頼度(%)': '{:.1f}',
                    '最高カバレッジ率(%)': '{:.1f}'
                }).background_gradient(
                    subset=['OCR信頼度(%)', '最高カバレッジ率(%)'], 
                    cmap='RdYlGn'
                ),
                use_container_width=True
            )
        except ImportError:
            # matplotlibが利用できない場合のフォールバック
            st.dataframe(
                performance_df.style.format({
                    'OCR信頼度(%)': '{:.1f}',
                    '最高カバレッジ率(%)': '{:.1f}'
                }),
                use_container_width=True
            )
    
    with tab3:
        st.subheader("🏆 大学ランキング")
        
        # ランキング基準選択
        ranking_criteria = st.selectbox(
            "ランキング基準を選択",
            ["最高カバレッジ率", "OCR信頼度", "総単語数", "ユニーク単語数"]
        )
        
        performance_df = create_performance_metrics_table(data, selected_universities)
        
        # デバッグ情報（本番では削除可能）
        # st.write("DEBUG - DataFrame columns:", performance_df.columns.tolist())
        
        try:
            if ranking_criteria == "最高カバレッジ率":
                sorted_df = performance_df.sort_values('最高カバレッジ率(%)', ascending=False)
            elif ranking_criteria == "OCR信頼度":
                sorted_df = performance_df.sort_values('OCR信頼度(%)', ascending=False)
            elif ranking_criteria == "総単語数":
                sorted_df = performance_df.sort_values('総単語数', ascending=False)
            else:  # ユニーク単語数
                sorted_df = performance_df.sort_values('ユニーク単語数', ascending=False)
        except KeyError as e:
            st.error(f"ソートエラー: 列 '{e}' が見つかりません。利用可能な列: {performance_df.columns.tolist()}")
            sorted_df = performance_df
        
        # ランキング表示
        for i, (_, row) in enumerate(sorted_df.iterrows(), 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}位"
            
            # 列名のマッピング
            column_mapping = {
                "最高カバレッジ率": "最高カバレッジ率(%)",
                "OCR信頼度": "OCR信頼度(%)",
                "総単語数": "総単語数",
                "ユニーク単語数": "ユニーク単語数"
            }
            
            actual_column = column_mapping.get(ranking_criteria, ranking_criteria)
            
            try:
                criteria_value = row[actual_column]
                
                # 値の表示形式を調整
                if "%" in actual_column:
                    criteria_display = f"{criteria_value}%"
                else:
                    criteria_display = f"{criteria_value:,}"
                
                with st.container():
                    st.markdown(f"""
                    ### {medal} {row['大学・学部']}
                    - **{ranking_criteria}**: {criteria_display}
                    - **最適単語帳**: {row['最適単語帳']}
                    - **OCR信頼度**: {row['OCR信頼度(%)']}%
                    """)
            except KeyError as e:
                st.error(f"表示エラー: 列 '{e}' が見つかりません。")
                with st.container():
                    st.markdown(f"""
                    ### {medal} {row['大学・学部']}
                    - **最適単語帳**: {row.get('最適単語帳', 'N/A')}
                    - **OCR信頼度**: {row.get('OCR信頼度(%)', 0)}%
                    """)

if __name__ == "__main__":
    main()