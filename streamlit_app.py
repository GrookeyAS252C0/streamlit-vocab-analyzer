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
    
    # カバレッジ率閾値（先に設定）
    min_coverage = st.sidebar.slider(
        "最小カバレッジ率 (%)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=1.0,
        help="この値より低いカバレッジ率の大学は表示されません"
    )
    st.session_state.min_coverage = min_coverage
    
    # 階層フィルター設定
    st.sidebar.subheader("📊 表示レベル")
    display_mode = st.sidebar.radio(
        "選択モード",
        ["大学レベル（統合）", "学部レベル（詳細）", "混合選択"],
        help="大学レベル：統合データ+単一大学、学部レベル：学部別データ、混合：全て自由選択"
    )
    
    # 大学選択
    all_universities = get_university_list(data)
    if not all_universities:
        st.sidebar.error("大学データが見つかりません")
        st.sidebar.write("デバッグ情報:", list(data.keys()))
        return
    
    # 選択モードに応じて選択肢をフィルタリング
    if display_mode == "大学レベル（統合）":
        # 統合データ + 単一大学データ（学部が複数ない大学）を表示
        universities = []
        for univ in all_universities:
            if "（全学部）" in univ:
                # 統合データは含める
                universities.append(univ)
            elif "_" not in univ:
                # 学部が分かれていない単一大学（東京大学など）も含める
                universities.append(univ)
        help_text = "大学レベルでの比較（統合データ + 単一大学）"
    elif display_mode == "学部レベル（詳細）":
        # 学部別データのみ表示（統合データは除外）
        universities = [univ for univ in all_universities if "（全学部）" not in univ]
        help_text = "学部別の詳細データで比較"
    else:  # 混合選択
        # 全てのデータを表示
        universities = all_universities
        help_text = "大学統合データと学部別データを自由に組み合わせて比較"
    
    # カバレッジ率フィルタリングを適用
    if min_coverage > 0:
        from utils.data_loader import filter_universities_by_criteria
        universities = [univ for univ in universities if univ in filter_universities_by_criteria(data, min_coverage)]
    
    # デバッグ情報表示
    mode_label = {"大学レベル（統合）": "大学", "学部レベル（詳細）": "学部", "混合選択": "全て"}[display_mode]
    st.sidebar.write(f"{mode_label}: {len(universities)} | 全体: {len(all_universities)}")
    if min_coverage > 0:
        st.sidebar.write(f"フィルター条件: カバレッジ率 ≥ {min_coverage}%")
    
    selected_universities = st.sidebar.multiselect(
        "🏫 大学・学部を選択",
        universities,
        default=[],
        help=help_text
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
    
    st.sidebar.markdown("---")
    
    # 簡潔な指標説明
    st.sidebar.subheader("💡 指標の意味")
    st.sidebar.markdown("""
    **カバレッジ率**: 単語帳の何%が入試に出現
    
    **抽出精度**: 学習語彙の何%が入試に出現
    
    **一致語数**: 実際に一致した語数
    """)
    
    # 低カバレッジ率の説明
    if min_coverage == 0:
        st.sidebar.info("""
        📌 **注意**: カバレッジ率は大学・学部により9.6-16.9%の範囲で変動します。
        これは出題傾向や問題形式の違いによるものです。
        """)
    
    # フィルタリングされた大学への説明
    if len(universities) < len(all_universities):
        hidden_count = len(all_universities) - len(universities)
        st.sidebar.warning(f"""
        ⚠️ {hidden_count}大学がフィルターで非表示です。
        すべての大学を表示するには、カバレッジ率を0%に設定してください。
        """)
    
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
    
    # 簡潔な定義（常時表示）
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **📈 カバレッジ率とは？**  
        単語帳の何%の語彙が実際の入試問題に出現したかを示す指標。高いほど実用的。
        """)
    
    with col2:
        st.info("""
        **🎯 抽出精度とは？**  
        抽出した単語のうち、単語帳に含まれる割合。高いほど学習効率が良い。
        """)
    
    # 詳細な指標の説明
    with st.expander("📖 詳しい指標の意味を確認する", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📈 **カバレッジ率 (Coverage Rate)**
            **定義**: 単語帳の何%の語彙が実際の入試問題に出現したか
            
            **計算式**: `一致語数 ÷ 単語帳総語数 × 100`
            
            **例**: Target 1900の24.25% = 460語 ÷ 1,897語 × 100
            
            **意味**: その単語帳の**実用性・入試適合度**を表す
            - 高いほど入試で頻出する語彙を多く含む
            - 受験対策での効率性の指標
            """)
        
        with col2:
            st.markdown("""
            ### 🎯 **抽出精度 (Extraction Precision)**
            **定義**: 抽出した単語のうち、単語帳に含まれる割合
            
            **計算式**: `一致語数 ÷ 抽出ユニーク語数 × 100`
            
            **例**: Target 1900の26.96% = 460語 ÷ 1,706語 × 100
            
            **意味**: その単語帳で学習する**効率性**を表す
            - 高いほど学んだ単語が入試に出やすい
            - 学習投資対効果の指標
            """)
        
        st.info("""
        💡 **理想的な単語帳**: 高カバレッジ率 + 高抽出精度 = 効率的な受験対策
        """)
    
    st.markdown("---")
    
    # 大学選択状況を確認
    selected_universities = st.session_state.get('selected_universities', [])
    
    if not selected_universities:
        # 大学が選択されていない場合
        st.info("""
        👈 **左のサイドバーから大学・学部を選択してください**
        
        選択した大学・学部の語彙分析結果とチャートが表示されます。
        
        - 複数の大学・学部を選択して比較分析も可能です
        - カバレッジ率の閾値設定でフィルタリングもできます
        """)
        return
    
    # 選択された大学のデータに基づいてサマリー統計を計算
    filtered_data = {
        'university_analysis': {k: v for k, v in data.get('university_analysis', {}).items() if k in selected_universities},
        'vocabulary_summary': data.get('vocabulary_summary', {}),
        'overall_summary': data.get('overall_summary', {})
    }
    summary_stats = calculate_summary_stats(filtered_data)
    
    # 選択された大学の統計
    selected_total_words = sum([info.get('total_words', 0) for univ, info in data.get('university_analysis', {}).items() if univ in selected_universities])
    selected_total_pages = sum([info.get('pages_processed', 0) for univ, info in data.get('university_analysis', {}).items() if univ in selected_universities])
    selected_avg_confidence = sum([info.get('ocr_confidence', 0) for univ, info in data.get('university_analysis', {}).items() if univ in selected_universities]) / len(selected_universities) if selected_universities else 0
    
    # メトリクス表示（選択された大学のみ）
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="選択大学総単語数",
            value=f"{selected_total_words:,}",
            delta=f"{len(selected_universities)}大学・学部"
        )
    
    with col2:
        st.metric(
            label="平均OCR信頼度",
            value=f"{selected_avg_confidence:.1f}%",
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
            value=f"{selected_total_pages}",
            delta=None
        )
    
    st.markdown("---")
    
    # チャート表示（選択された大学のデータのみ）
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 選択大学の単語帳別カバレッジ率・抽出精度")
        fig_vocab = create_vocabulary_comparison_bar(filtered_data)
        st.plotly_chart(fig_vocab, use_container_width=True)
        st.caption("💡 選択した大学のデータに基づく統計。カバレッジ率が高いほど実用的、抽出精度が高いほど学習効率が良い")
    
    with col2:
        st.subheader("🎯 選択大学のカバレッジ率 vs 抽出精度")
        fig_scatter = create_scatter_coverage_precision(filtered_data)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("💡 選択した大学での結果。右上にある単語帳ほど理想的（高実用性×高効率性）")
    
    # ヒートマップ（選択された大学のみ）
    if len(selected_universities) > 1:
        st.subheader("🔥 選択大学×単語帳 カバレッジ率ヒートマップ")
        fig_heatmap = create_university_heatmap(filtered_data)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.caption("💡 色が濃い（赤い）ほど高いカバレッジ率。選択した大学間での単語帳適合度を比較")
    else:
        st.subheader("📋 選択大学の詳細データ")
        st.info("複数の大学を選択すると、大学間比較のヒートマップが表示されます。")
    
    # 文章統計（選択された大学のみ）
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 選択大学の文章統計")
        
        # 選択された大学の文章統計テーブル作成
        university_data = {k: v for k, v in data.get('university_analysis', {}).items() if k in selected_universities}
        sentence_table_data = []
        
        for univ, info in university_data.items():
            sentence_table_data.append({
                '大学・学部': univ.replace('早稲田大学_', '早大_'),
                '文の数': info.get('total_sentences', 0),
                '平均語数/文': info.get('avg_words_per_sentence', 0.0)
            })
        
        # DataFrameに変換してソート（文の数の降順）
        import pandas as pd
        sentence_df = pd.DataFrame(sentence_table_data)
        sentence_df = sentence_df.sort_values('文の数', ascending=False)
        
        # スタイル付きテーブル表示
        try:
            st.dataframe(
                sentence_df.style.format({
                    '文の数': '{:,}',
                    '平均語数/文': '{:.1f}'
                }).background_gradient(subset=['文の数', '平均語数/文'], cmap='RdYlGn'),
                use_container_width=True,
                height=400
            )
        except ImportError:
            # matplotlibが利用できない場合のフォールバック
            st.dataframe(
                sentence_df.style.format({
                    '文の数': '{:,}',
                    '平均語数/文': '{:.1f}'
                }),
                use_container_width=True,
                height=400
            )
        
        st.caption("💡 文の数が多いほど豊富なコンテンツ、平均語数/文が高いほど複雑な文章構造")
    
    with col2:
        st.subheader("⚡ OCR処理品質")
        avg_confidence = summary_stats.get('average_ocr_confidence', 0)
        fig_gauge = create_ocr_confidence_gauge(avg_confidence)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # 選択大学の文章統計サマリー
        if university_data:
            selected_total_sentences = sum([info.get('total_sentences', 0) for info in university_data.values()])
            selected_total_words_in_sentences = sum([info.get('avg_words_per_sentence', 0) * info.get('total_sentences', 0) for info in university_data.values()])
            selected_overall_avg = selected_total_words_in_sentences / selected_total_sentences if selected_total_sentences > 0 else 0
            
            st.markdown("### 📊 選択大学文章統計")
            st.metric("総文数", f"{selected_total_sentences:,}")
            st.metric("平均語数/文", f"{selected_overall_avg:.1f}語")

def show_university_page(data: dict, metadata: dict):
    """大学別詳細ページ"""
    st.markdown('<div class="sub-header">🏫 大学別詳細分析</div>', unsafe_allow_html=True)
    
    # 簡潔な指標説明
    st.info("""
    💡 **カバレッジ率**: 単語帳の何%が入試に出現 | **抽出精度**: 学習した語彙の何%が入試に出現 | 詳細は概要ページで確認
    """)
    
    # 大学選択
    universities = get_university_list(data)
    
    # デバッグ情報表示
    st.write(f"デバッグ: 利用可能な大学数 = {len(universities)}")
    if universities:
        st.write("利用可能な大学例:", universities[:3])
    
    if not universities:
        st.error("大学データが見つかりません。データファイルを確認してください。")
        return
    
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
        - 文の数: {university_data.get('total_sentences', 0):,}
        - 平均語数/文: {university_data.get('avg_words_per_sentence', 0):.1f}語
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
    
    # 簡潔な指標説明
    st.info("""
    📊 **カバレッジ率**: 単語帳の実用性（高いほど入試頻出語を多く含む） | **抽出精度**: 学習効率性（高いほど学習効果大）
    """)
    
    # 比較対象選択
    universities = get_university_list(data)
    
    # デバッグ情報
    st.write(f"デバッグ: 利用可能な大学数 = {len(universities)}")
    if universities:
        st.write("利用可能な大学:", universities[:5])  # 最初の5つを表示
    
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
        - 外側に向かうほど高いカバレッジ率（その単語帳が入試により適している）
        - 各軸は単語帳を表す（5種類の単語帳を比較）
        - 色分けで大学を区別（複数大学の特徴を一目で比較）
        - 大きく外に広がった形ほど、多くの単語帳で高いカバレッジ率を示す
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