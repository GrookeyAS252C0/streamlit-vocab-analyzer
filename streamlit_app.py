#!/usr/bin/env python3
"""
大学入試英単語分析 Streamlit アプリ
JSONファイルアップロード・語彙分析ダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import nltk

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
    
    # メインタイトル
    st.markdown('<div class="main-header">📚 大学入試英単語分析ダッシュボード</div>', unsafe_allow_html=True)
    st.markdown("**JSONファイルをアップロードして語彙分析を実行してください**")
    
    # ファイルアップロードエリア
    uploaded_files = st.file_uploader(
        "extraction_results_pure_english.json ファイルを選択（複数選択可能）",
        type=["json"],
        accept_multiple_files=True,
        help="OCR処理済みの英語抽出結果JSONファイルをアップロードしてください。複数ファイルを統合して分析します。"
    )
    
    if uploaded_files:
        try:
            # 複数ファイルの内容を統合
            combined_data = merge_multiple_json_files(uploaded_files)
            
            if combined_data:
                st.success(f"✅ {len(uploaded_files)}個のファイルを正常に読み込みました")
                
                # ファイル一覧表示
                with st.expander("📁 アップロードされたファイル", expanded=False):
                    for i, file in enumerate(uploaded_files, 1):
                        st.write(f"{i}. {file.name}")
                
                # 分析実行ボタン
                if st.button("📊 語彙分析を実行", type="primary"):
                    with st.spinner("語彙分析を実行中..."):
                        analysis_data = perform_vocabulary_analysis(combined_data)
                        if analysis_data:
                            st.session_state.analysis_data = analysis_data
                            st.session_state.analysis_completed = True
                            st.success("✅ 語彙分析が完了しました！")
                        else:
                            st.error("❌ 語彙分析に失敗しました")
                
                # 分析結果の表示
                if st.session_state.get('analysis_completed', False) and 'analysis_data' in st.session_state:
                    st.markdown("---")
                    show_analysis_dashboard(st.session_state.analysis_data)
            else:
                st.error("❌ ファイルの読み込みに失敗しました")
                
        except json.JSONDecodeError:
            st.error("❌ JSONファイルの形式が正しくありません")
        except Exception as e:
            st.error(f"❌ ファイル読み込みエラー: {str(e)}")
    else:
        st.info("""
        👆 **extraction_results_pure_english.json ファイルをアップロードしてください**
        
        📋 必要なファイル形式:
        - OCR処理済みの英語抽出結果
        - extracted_data セクションに各大学・学部のデータ
        - pure_english_text と extracted_words を含む
        """)

def merge_multiple_json_files(uploaded_files):
    """複数のJSONファイルを統合"""
    try:
        combined_data = {
            'extraction_summary': {
                'total_source_files': 0,
                'total_words_extracted': 0
            },
            'extracted_data': []
        }
        
        for uploaded_file in uploaded_files:
            # ファイルポインタを先頭に戻す
            uploaded_file.seek(0)
            file_content = json.load(uploaded_file)
            
            # サマリー情報を統合
            file_summary = file_content.get('extraction_summary', {})
            combined_data['extraction_summary']['total_source_files'] += file_summary.get('total_source_files', 0)
            combined_data['extraction_summary']['total_words_extracted'] += file_summary.get('total_words_extracted', 0)
            
            # 抽出データを統合
            file_extracted_data = file_content.get('extracted_data', [])
            combined_data['extracted_data'].extend(file_extracted_data)
        
        return combined_data
        
    except Exception as e:
        st.error(f"ファイル統合中にエラーが発生しました: {str(e)}")
        return None

@st.cache_data
def load_vocabulary_books():
    """単語帳データを読み込み（組み込みデータを使用）"""
    try:
        from vocab_data import get_embedded_vocabulary_data
        
        # 組み込みデータを取得
        embedded_data = get_embedded_vocabulary_data()
        
        # 小文字化して正規化
        vocab_data = {}
        for name, word_set in embedded_data.items():
            vocab_data[name] = {word.lower().strip() for word in word_set if word and len(word) > 1}
        
        return vocab_data
    except Exception as e:
        st.error(f"単語帳データの読み込みに失敗: {str(e)}")
        return {}

def setup_analysis_sidebar(analysis_data):
    """分析用サイドバーの設定"""
    st.sidebar.title("📊 分析設定")
    
    # 分析対象選択
    st.sidebar.subheader("🏫 分析対象")
    available_universities = list(analysis_data.get('university_analysis', {}).keys())
    
    # デバッグ情報を表示
    if len(available_universities) == 0:
        st.sidebar.error("❌ 大学データが見つかりません")
        st.sidebar.write("**デバッグ情報:**")
        st.sidebar.write(f"analysis_data keys: {list(analysis_data.keys())}")
        st.sidebar.write(f"university_analysis keys: {list(analysis_data.get('university_analysis', {}).keys())}")
    else:
        st.sidebar.success(f"✅ {len(available_universities)}大学・学部を検出")
    
    selected_universities = st.sidebar.multiselect(
        "大学・学部を選択",
        available_universities,
        default=available_universities[:3] if len(available_universities) >= 3 else available_universities,
        help="比較分析する大学・学部を選択してください"
    )
    
    st.session_state.selected_universities = selected_universities
    
    st.sidebar.markdown("---")
    
    # 指標説明
    st.sidebar.subheader("💡 指標の意味")
    st.sidebar.markdown("""
    **カバレッジ率**: 単語帳の何%が入試に出現
    
    **抽出精度**: 学習語彙の何%が入試に出現
    
    **一致語数**: 実際に一致した語数
    """)
    
    # データ情報
    st.sidebar.subheader("📋 データ情報")
    overall_summary = analysis_data.get('overall_summary', {})
    st.sidebar.write(f"**総大学数**: {len(available_universities)}")
    st.sidebar.write(f"**単語帳数**: 5種類")
    st.sidebar.write(f"**総単語数**: {overall_summary.get('total_words_extracted', 0):,}")

def perform_vocabulary_analysis(extraction_data):
    """JSONデータから語彙分析を実行"""
    try:
        st.write("🔄 分析開始...")
        
        # NLTK データダウンロード
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            st.warning(f"NLTK データダウンロード警告: {str(e)}")
        
        # 単語帳データ読み込み
        st.write("📚 単語帳データ読み込み中...")
        vocab_books = load_vocabulary_books()
        if not vocab_books:
            st.error("単語帳データの読み込みに失敗しました")
            return None
        st.success(f"✅ {len(vocab_books)}個の単語帳を読み込み完了")
        
        # 入力データの検証
        st.write("📋 入力データの検証中...")
        if not extraction_data:
            st.error("❌ extraction_data が空です")
            return None
        
        st.write(f"extraction_data keys: {list(extraction_data.keys())}")
        extracted_data_list = extraction_data.get('extracted_data', [])
        if not extracted_data_list:
            st.error("❌ extracted_data リストが空です")
            return None
        
        st.success(f"✅ {len(extracted_data_list)}件のデータエントリを確認")
        
        # 分析結果の初期化
        analysis_result = {
            'overall_summary': {
                'total_source_files': extraction_data.get('extraction_summary', {}).get('total_source_files', 0),
                'total_words_extracted': extraction_data.get('extraction_summary', {}).get('total_words_extracted', 0),
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'vocabulary_summary': {},
            'university_analysis': {}
        }
        
        # 各大学・学部のデータを分析
        st.write("🏫 大学・学部データの分析開始...")
        
        for i, entry in enumerate(extracted_data_list):
            try:
                st.write(f"--- エントリ {i+1}/{len(extracted_data_list)} の処理 ---")
                
                source_file = entry.get('source_file', '')
                if not source_file:
                    st.warning(f"⚠️ エントリ {i+1}: source_file が空です")
                    continue
                
                university_name = extract_university_name_from_filename(source_file)
                if not university_name or university_name == "不明な大学":
                    st.warning(f"⚠️ エントリ {i+1}: 大学名抽出に失敗 - '{source_file}'")
                    continue
                
                # 抽出された単語を正規化
                extracted_words = entry.get('extracted_words', [])
                if not extracted_words:
                    st.warning(f"⚠️ エントリ {i+1}: extracted_words が空です")
                    continue
                
                normalized_words = [word.lower().strip() for word in extracted_words if word and len(word) > 1]
                unique_words = list(set(normalized_words))
                
                st.write(f"✅ {university_name}: {len(extracted_words)}語 → {len(unique_words)}ユニーク語")
                
                # 各単語帳との比較分析
                vocab_coverage = {}
                for vocab_name, vocab_set in vocab_books.items():
                matched_words = [word for word in unique_words if word in vocab_set]
                matched_count = len(matched_words)
                
                target_coverage_rate = (matched_count / len(vocab_set)) * 100 if vocab_set else 0
                extraction_precision = (matched_count / len(unique_words)) * 100 if unique_words else 0
                
                vocab_coverage[vocab_name] = {
                    'matched_words_count': matched_count,
                    'target_coverage_rate': target_coverage_rate,
                    'extraction_precision': extraction_precision,
                    'matched_words': matched_words[:20]  # 最初の20語のみ保存
                }
            
                # 大学データを保存
                try:
                    analysis_result['university_analysis'][university_name] = {
                        'source_file': source_file,
                        'total_words': len(extracted_words),
                        'unique_words': len(unique_words),
                        'vocabulary_coverage': vocab_coverage,
                        'pages_processed': entry.get('pages_processed', 0)
                    }
                    st.success(f"✅ {university_name} のデータを保存完了")
                    st.write(f"現在の大学数: {len(analysis_result['university_analysis'])}")
                except Exception as save_error:
                    st.error(f"❌ {university_name} の保存中にエラー: {str(save_error)}")
                    continue
                    
            except Exception as entry_error:
                st.error(f"❌ エントリ {i+1} の処理中にエラー: {str(entry_error)}")
                continue
        
        # 全体サマリーの計算
        all_coverage_data = {vocab_name: [] for vocab_name in vocab_books.keys()}
        for univ_data in analysis_result['university_analysis'].values():
            for vocab_name in vocab_books.keys():
                coverage = univ_data['vocabulary_coverage'][vocab_name]
                all_coverage_data[vocab_name].append({
                    'coverage_rate': coverage['target_coverage_rate'],
                    'precision': coverage['extraction_precision'],
                    'matched_count': coverage['matched_words_count']
                })
        
        # 語彙サマリーの計算
        for vocab_name, coverage_list in all_coverage_data.items():
            if coverage_list:
                avg_coverage = sum(item['coverage_rate'] for item in coverage_list) / len(coverage_list)
                avg_precision = sum(item['precision'] for item in coverage_list) / len(coverage_list)
                total_matched = sum(item['matched_count'] for item in coverage_list)
                
                analysis_result['vocabulary_summary'][vocab_name] = {
                    'average_coverage_rate': avg_coverage,
                    'average_extraction_precision': avg_precision,
                    'total_matched_words': total_matched
                }
        
        # 最終結果の確認
        st.success(f"✅ 分析完了: {len(analysis_result['university_analysis'])}大学・学部")
        st.write("**最終結果:**")
        st.write(f"  - university_analysis keys: {list(analysis_result['university_analysis'].keys())}")
        
        return analysis_result
        
    except Exception as e:
        st.error(f"語彙分析中にエラーが発生しました: {str(e)}")
        return None

def extract_university_name_from_filename(filename):
    """ファイル名から大学・学部名を抽出"""
    if not filename:
        return "不明な大学"
    
    # PDFファイル名の例: "慶應義塾大学_2024年度_英語_薬学部.pdf"
    # ファイル名からパス部分を取り除く
    basename = filename.split('/')[-1] if '/' in filename else filename
    parts = basename.replace('.pdf', '').split('_')
    
    if len(parts) >= 4:
        university = parts[0]
        department = parts[3]
        return f"{university}_{department}"
    elif len(parts) >= 1:
        return parts[0]
    
    return basename.replace('.pdf', '')

def show_analysis_dashboard(analysis_data):
    """分析結果ダッシュボードの表示"""
    if not analysis_data:
        st.error("分析データがありません")
        return
    
    # サイドバー設定
    setup_analysis_sidebar(analysis_data)
    
    # メインタブの作成
    tab1, tab2, tab3 = st.tabs(["🏠 概要分析", "🏫 大学別詳細", "📊 比較分析"])
    
    with tab1:
        show_overview_analysis(analysis_data)
    
    with tab2:
        show_university_analysis(analysis_data)
    
    with tab3:
        show_comparison_analysis(analysis_data)

def show_overview_analysis(analysis_data: dict):
    """概要分析タブのコンテンツ"""
    
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
    
    # 選択された大学のデータを取得
    university_analysis = analysis_data.get('university_analysis', {})
    vocabulary_summary = analysis_data.get('vocabulary_summary', {})
    
    # 選択された大学の統計
    selected_total_words = sum([info.get('total_words', 0) for univ, info in university_analysis.items() if univ in selected_universities])
    selected_total_pages = sum([info.get('pages_processed', 0) for univ, info in university_analysis.items() if univ in selected_universities])
    
    # メトリクス表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="選択大学総単語数",
            value=f"{selected_total_words:,}",
            delta=f"{len(selected_universities)}大学・学部"
        )
    
    with col2:
        # 最高カバレッジ率を計算
        best_coverage = 0
        best_vocab = "N/A"
        for vocab_name, summary in vocabulary_summary.items():
            if summary.get('average_coverage_rate', 0) > best_coverage:
                best_coverage = summary.get('average_coverage_rate', 0)
                best_vocab = vocab_name
        
        st.metric(
            label="最適単語帳",
            value=best_vocab,
            delta=f"{best_coverage:.1f}%"
        )
    
    with col3:
        st.metric(
            label="処理ページ数",
            value=f"{selected_total_pages}",
            delta=None
        )
    
    st.markdown("---")
    
    # 単語帳別パフォーマンスチャート
    if vocabulary_summary:
        st.subheader("📚 単語帳別パフォーマンス")
        
        # データ準備
        vocab_data = []
        for vocab_name, summary in vocabulary_summary.items():
            vocab_data.append({
                '単語帳': vocab_name,
                'カバレッジ率(%)': summary.get('average_coverage_rate', 0),
                '抽出精度(%)': summary.get('average_extraction_precision', 0),
                '一致語数': summary.get('total_matched_words', 0)
            })
        
        vocab_df = pd.DataFrame(vocab_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # カバレッジ率棒グラフ
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
            # 抽出精度棒グラフ
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
        
        # パフォーマンステーブル
        st.subheader("📊 単語帳パフォーマンステーブル")
        try:
            st.dataframe(
                vocab_df.style.format({
                    'カバレッジ率(%)': '{:.1f}',
                    '抽出精度(%)': '{:.1f}',
                    '一致語数': '{:,}'
                }).background_gradient(subset=['カバレッジ率(%)', '抽出精度(%)'], cmap='RdYlGn'),
                use_container_width=True
            )
        except ImportError:
            st.dataframe(
                vocab_df.style.format({
                    'カバレッジ率(%)': '{:.1f}',
                    '抽出精度(%)': '{:.1f}',
                    '一致語数': '{:,}'
                }),
                use_container_width=True
            )

def show_university_analysis(analysis_data: dict):
    """大学別詳細タブのコンテンツ"""
    
    # 簡潔な指標説明
    st.info("""
    💡 **カバレッジ率**: 単語帳の何%が入試に出現 | **抽出精度**: 学習した語彙の何%が入試に出現 | 詳細は概要タブで確認
    """)
    
    # サイドバーで選択された大学を取得
    selected_universities = st.session_state.get('selected_universities', [])
    
    if not selected_universities:
        st.info("""
        👈 **左のサイドバーから大学・学部を選択してください**
        
        選択した大学・学部の詳細分析が表示されます。
        
        - 1つの大学を選択すると、その大学の詳細情報を表示
        - 複数選択時は最初の大学の詳細を表示
        """)
        return
    
    # 最初に選択された大学の詳細を表示
    selected_university = selected_universities[0]
    if len(selected_universities) > 1:
        st.info(f"複数選択されています。{selected_university} の詳細を表示中（他 {len(selected_universities)-1} 大学）")
    
    university_data = analysis_data.get('university_analysis', {}).get(selected_university, {})
    university_meta = {}  # メタデータは現在利用不可
    
    # 大学情報カード
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **🏫 {selected_university}**
        - ファイル: {university_data.get('source_file', 'N/A').split('/')[-1] if university_data.get('source_file') else 'N/A'}
        """)
    
    with col2:
        st.info(f"""
        **📊 処理統計**
        - 総単語数: {university_data.get('total_words', 0):,}
        - ユニーク語数: {university_data.get('unique_words', 0):,}
        - 処理ページ: {university_data.get('pages_processed', 0)}
        """)
    
    with col3:
        st.info(f"""
        **📚 語彙分析**
        - 単語帳数: {len(university_data.get('vocabulary_coverage', {}))}
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

def show_comparison_analysis(analysis_data: dict):
    """比較分析タブのコンテンツ"""
    
    # 簡潔な指標説明
    st.info("""
    📊 **カバレッジ率**: 単語帳の実用性（高いほど入試頻出語を多く含む） | **抽出精度**: 学習効率性（高いほど学習効果大）
    """)
    
    # サイドバーで選択された大学を取得
    selected_universities = st.session_state.get('selected_universities', [])
    
    if not selected_universities:
        st.info("""
        👈 **左のサイドバーから大学・学部を選択してください**
        
        選択した大学・学部の比較分析が表示されます。
        
        - 2つ以上の大学を選択すると比較チャートが表示されます
        - 1つの場合は個別分析を表示
        """)
        return
    
    if len(selected_universities) < 2:
        st.warning("比較分析には2つ以上の大学が必要です")
        return
    
    # 大学間比較テーブル
    st.subheader("📊 大学間比較")
    
    comparison_data = []
    university_analysis = analysis_data.get('university_analysis', {})
    
    for univ in selected_universities:
        univ_data = university_analysis.get(univ, {})
        vocab_coverage = univ_data.get('vocabulary_coverage', {})
        
        # 最高カバレッジ率と最適単語帳を探す
        best_coverage = 0
        best_vocab = "N/A"
        
        for vocab_name, stats in vocab_coverage.items():
            coverage = stats.get('target_coverage_rate', 0)
            if coverage > best_coverage:
                best_coverage = coverage
                best_vocab = vocab_name
        
        comparison_data.append({
            '大学・学部': univ,
            '総単語数': univ_data.get('total_words', 0),
            'ユニーク単語数': univ_data.get('unique_words', 0),
            '最適単語帳': best_vocab,
            '最高カバレッジ率(%)': round(best_coverage, 1),
            '処理ページ': univ_data.get('pages_processed', 0)
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # スタイル付きテーブル表示
    try:
        st.dataframe(
            comparison_df.style.format({
                '総単語数': '{:,}',
                'ユニーク単語数': '{:,}',
                '最高カバレッジ率(%)': '{:.1f}'
            }).background_gradient(subset=['最高カバレッジ率(%)'], cmap='RdYlGn'),
            use_container_width=True
        )
    except ImportError:
        st.dataframe(
            comparison_df.style.format({
                '総単語数': '{:,}',
                'ユニーク単語数': '{:,}',
                '最高カバレッジ率(%)': '{:.1f}'
            }),
            use_container_width=True
        )
    
    # ランキング表示
    st.subheader("🏆 ランキング")
    
    ranking_criteria = st.selectbox(
        "ランキング基準",
        ["最高カバレッジ率(%)", "総単語数", "ユニーク単語数"]
    )
    
    sorted_df = comparison_df.sort_values(ranking_criteria, ascending=False)
    
    for i, (_, row) in enumerate(sorted_df.iterrows(), 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}位"
        
        criteria_value = row[ranking_criteria]
        if "(%" in ranking_criteria:
            criteria_display = f"{criteria_value}%"
        else:
            criteria_display = f"{criteria_value:,}"
        
        with st.container():
            st.markdown(f"""
            ### {medal} {row['大学・学部']}
            - **{ranking_criteria}**: {criteria_display}
            - **最適単語帳**: {row['最適単語帳']}
            - **処理ページ**: {row['処理ページ']}
            """)

if __name__ == "__main__":
    main()