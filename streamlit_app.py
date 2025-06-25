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
                        st.session_state.analysis_data = analysis_data
                        st.success("✅ 語彙分析が完了しました！")
                        st.rerun()
                
                # 分析結果の表示
                if 'analysis_data' in st.session_state:
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
    """単語帳データを読み込み"""
    try:
        vocab_data = {}
        vocab_files = {
            'Target 1900': '/Users/takashikemmoku/Desktop/analysisdashboard/target1900.csv',
            'Target 1400': '/Users/takashikemmoku/Desktop/analysisdashboard/target1400.csv',
            'システム英単語': '/Users/takashikemmoku/Desktop/analysisdashboard/システム英単語.csv',
            'LEAP': '/Users/takashikemmoku/Desktop/analysisdashboard/LEAP.csv',
            '鉄壁': '/Users/takashikemmoku/Desktop/analysisdashboard/鉄壁.csv'
        }
        
        for name, filepath in vocab_files.items():
            try:
                if name == 'Target 1900':
                    df = pd.read_csv(filepath, encoding='utf-8-sig')
                    vocab_data[name] = set(df['word'].str.lower().dropna())
                elif name == 'Target 1400':
                    df = pd.read_csv(filepath, encoding='utf-8-sig')
                    vocab_data[name] = set(df['単語'].str.lower().dropna())
                else:
                    df = pd.read_csv(filepath, encoding='utf-8-sig')
                    vocab_data[name] = set(df['英語'].str.lower().dropna())
            except Exception as e:
                st.warning(f"単語帳 '{name}' の読み込みに失敗: {str(e)}")
                vocab_data[name] = set()
        
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
        # NLTK データダウンロード
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except:
            pass
        
        # 単語帳データ読み込み
        vocab_books = load_vocabulary_books()
        if not vocab_books:
            st.error("単語帳データの読み込みに失敗しました")
            return None
        
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
        for entry in extraction_data.get('extracted_data', []):
            source_file = entry.get('source_file', '')
            university_name = extract_university_name_from_filename(source_file)
            
            # 抽出された単語を正規化
            extracted_words = entry.get('extracted_words', [])
            normalized_words = [word.lower().strip() for word in extracted_words if word and len(word) > 1]
            unique_words = list(set(normalized_words))
            
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
            analysis_result['university_analysis'][university_name] = {
                'source_file': source_file,
                'total_words': len(extracted_words),
                'unique_words': len(unique_words),
                'vocabulary_coverage': vocab_coverage,
                'pages_processed': entry.get('pages_processed', 0)
            }
        
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
        
        return analysis_result
        
    except Exception as e:
        st.error(f"語彙分析中にエラーが発生しました: {str(e)}")
        return None

def extract_university_name_from_filename(filename):
    """ファイル名から大学・学部名を抽出"""
    if not filename:
        return "不明な大学"
    
    # PDFファイル名の例: "慶應義塾大学_2024年度_英語_薬学部.pdf"
    parts = filename.replace('.pdf', '').split('_')
    if len(parts) >= 4:
        university = parts[0]
        department = parts[3]
        return f"{university}_{department}"
    elif len(parts) >= 1:
        return parts[0]
    
    return filename.replace('.pdf', '')

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
        # 選択された大学に基づく最適単語帳を計算
        optimal_vocab_info = get_optimal_vocabulary_for_selection(data, selected_universities)
        
        if optimal_vocab_info and 'optimal_vocabulary' in optimal_vocab_info:
            optimal_name = optimal_vocab_info['optimal_vocabulary']
            optimal_score = optimal_vocab_info['optimal_score']
            optimal_coverage = optimal_vocab_info['optimal_coverage']
            
            st.metric(
                label="選択大学の最適単語帳",
                value=optimal_name,
                delta=f"総合スコア: {optimal_score:.1f}",
                help=f"カバレッジ率: {optimal_coverage:.1f}%"
            )
        else:
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
    
    # 選択大学の最適単語帳詳細情報
    if len(selected_universities) >= 1:
        st.markdown("---")
        st.subheader("🎯 選択大学の最適単語帳分析")
        
        optimal_vocab_info = get_optimal_vocabulary_for_selection(data, selected_universities)
        
        if optimal_vocab_info and 'optimal_vocabulary' in optimal_vocab_info:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 最適単語帳の詳細情報
                optimal_name = optimal_vocab_info['optimal_vocabulary']
                optimal_score = optimal_vocab_info['optimal_score']
                optimal_coverage = optimal_vocab_info['optimal_coverage']
                optimal_precision = optimal_vocab_info['optimal_precision']
                total_matched = optimal_vocab_info['selection_summary']['total_matched']
                
                st.success(f"""
                **🏆 最適単語帳: {optimal_name}**
                - 📈 総合スコア: {optimal_score:.1f}/100点
                - 📊 カバレッジ率: {optimal_coverage:.1f}%
                - 🎯 抽出精度: {optimal_precision:.1f}%
                - ✅ 一致語数: {total_matched:,}語
                """)
                
                # 単語帳別パフォーマンス比較
                st.markdown("##### 📚 全単語帳パフォーマンス比較")
                
                performance_data = []
                for vocab_name, perf in optimal_vocab_info['all_performance'].items():
                    is_optimal = vocab_name == optimal_name
                    performance_data.append({
                        '単語帳': f"🏆 {vocab_name}" if is_optimal else vocab_name,
                        '総合スコア': perf['composite_score'],
                        'カバレッジ率(%)': perf['coverage_rate'],
                        '抽出精度(%)': perf['extraction_precision'],
                        '一致語数': perf['matched_words_count']
                    })
                
                # DataFrameで表示
                perf_df = pd.DataFrame(performance_data)
                perf_df = perf_df.sort_values('総合スコア', ascending=False)
                
                try:
                    st.dataframe(
                        perf_df.style.format({
                            '総合スコア': '{:.1f}',
                            'カバレッジ率(%)': '{:.1f}',
                            '抽出精度(%)': '{:.1f}',
                            '一致語数': '{:,}'
                        }).background_gradient(subset=['総合スコア'], cmap='RdYlGn'),
                        use_container_width=True
                    )
                except ImportError:
                    st.dataframe(
                        perf_df.style.format({
                            '総合スコア': '{:.1f}',
                            'カバレッジ率(%)': '{:.1f}',
                            '抽出精度(%)': '{:.1f}',
                            '一致語数': '{:,}'
                        }),
                        use_container_width=True
                    )
                
                st.caption("💡 総合スコア = カバレッジ率×70% + 抽出精度×30%")
            
            with col2:
                # 選択情報サマリー
                st.info(f"""
                **📊 選択情報**
                - 選択大学数: {optimal_vocab_info['selected_universities_count']}
                - 総単語数: {optimal_vocab_info['selection_summary']['total_words']:,}語
                
                **🔍 算出方法**
                - 各大学の単語数で重み付け平均
                - カバレッジ率を重視した評価
                """)
                
                # 選択大学リスト
                st.markdown("**📝 選択大学一覧:**")
                for i, univ in enumerate(selected_universities, 1):
                    short_name = univ.replace('早稲田大学_', '早大_').replace('慶應義塾大学_', '慶大_')
                    st.write(f"{i}. {short_name}")
        else:
            st.warning("選択された大学の最適単語帳データを取得できませんでした。")

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
        st.warning(f"""
        **比較分析には2つ以上の大学が必要です**
        
        現在選択: {len(selected_universities)}大学（{', '.join(selected_universities)}）
        
        👈 左のサイドバーで追加の大学を選択してください。
        """)
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