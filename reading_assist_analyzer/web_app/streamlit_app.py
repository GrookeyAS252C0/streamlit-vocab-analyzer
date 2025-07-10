#!/usr/bin/env python3
"""
ReadingAssist Analyzer - Streamlit Web Application
英文読解における単語帳有効性と文章構造の総合分析ダッシュボード
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
import sys
import os
from pathlib import Path
import logging

# パスの設定
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from core.text_analyzer import TextAnalyzer
from core.vocab_analyzer import VocabularyAnalyzer
from core.grammar_analyzer import GrammarAnalyzer
from core.sentence_analyzer import SentenceAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    .analysis-section {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .recommendation-box {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .challenge-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ReadingAssistApp:
    def __init__(self):
        """アプリケーション初期化"""
        self.initialize_session_state()
        self.load_config()
        self.initialize_analyzers()
    
    def initialize_session_state(self):
        """セッション状態の初期化"""
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = None
        if 'input_text' not in st.session_state:
            st.session_state.input_text = ""
        if 'analysis_in_progress' not in st.session_state:
            st.session_state.analysis_in_progress = False
    
    def load_config(self):
        """設定ファイルの読み込み"""
        config_path = project_root / "config" / "settings.json"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            self.config = {}
    
    def initialize_analyzers(self):
        """分析エンジンの初期化"""
        try:
            self.text_analyzer = TextAnalyzer(self.config.get('analysis', {}))
            logger.info("分析エンジンを初期化しました")
        except Exception as e:
            logger.error(f"分析エンジン初期化エラー: {e}")
            st.error("分析エンジンの初期化に失敗しました")
    
    def run(self):
        """メインアプリケーション実行"""
        self.render_header()
        self.render_sidebar()
        self.render_main_content()
    
    def render_header(self):
        """ヘッダーの描画"""
        st.markdown("""
        <div class="main-header">
            <h1>📚 ReadingAssist Analyzer</h1>
            <p>英文読解における単語帳有効性と文章構造の総合分析</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """サイドバーの描画"""
        with st.sidebar:
            st.header("📋 分析設定")
            
            # テキスト入力方法の選択
            input_method = st.radio(
                "入力方法を選択",
                ["テキスト直接入力", "ファイルアップロード", "サンプルテキスト"]
            )
            
            if input_method == "テキスト直接入力":
                self.handle_text_input()
            elif input_method == "ファイルアップロード":
                self.handle_file_upload()
            else:
                self.handle_sample_text()
            
            # 分析オプション
            st.subheader("🔧 分析オプション")
            
            enable_vocab = st.checkbox("語彙分析", value=True)
            enable_grammar = st.checkbox("文法分析", value=True)
            enable_sentence = st.checkbox("文構造分析", value=True)
            
            # 分析実行ボタン
            if st.button("🚀 分析実行", type="primary", use_container_width=True):
                self.run_analysis(enable_vocab, enable_grammar, enable_sentence)
            
            # 分析結果のクリア
            if st.button("🗑️ 結果クリア"):
                st.session_state.analysis_result = None
                st.session_state.input_text = ""
                st.rerun()
    
    def handle_text_input(self):
        """テキスト直接入力の処理"""
        text_input = st.text_area(
            "分析したい英文を入力してください",
            height=200,
            placeholder="Enter English text here..."
        )
        
        if text_input:
            st.session_state.input_text = text_input
            
            # テキスト統計の表示
            word_count = len(text_input.split())
            char_count = len(text_input)
            
            st.metric("文字数", f"{char_count:,}")
            st.metric("単語数", f"{word_count:,}")
    
    def handle_file_upload(self):
        """ファイルアップロードの処理"""
        uploaded_file = st.file_uploader(
            "テキストファイルをアップロード",
            type=['txt', 'csv', 'json'],
            help="対応形式: .txt, .csv, .json"
        )
        
        if uploaded_file is not None:
            try:
                # ファイル内容の読み込み
                if uploaded_file.type == "text/plain":
                    content = str(uploaded_file.read(), "utf-8")
                else:
                    content = uploaded_file.read().decode("utf-8")
                
                st.session_state.input_text = content
                
                # ファイル情報表示
                st.success(f"ファイル '{uploaded_file.name}' を読み込みました")
                st.info(f"ファイルサイズ: {len(content)} 文字")
                
            except Exception as e:
                st.error(f"ファイル読み込みエラー: {e}")
    
    def handle_sample_text(self):
        """サンプルテキストの処理"""
        sample_files = {
            "学術文章サンプル": "data/sample_texts/sample_academic.txt",
            "ニュース記事サンプル": "data/sample_texts/sample_news.txt",
            "小説サンプル": "data/sample_texts/sample_fiction.txt"
        }
        
        selected_sample = st.selectbox(
            "サンプルテキストを選択",
            list(sample_files.keys())
        )
        
        if st.button("サンプル読み込み"):
            sample_path = project_root / sample_files[selected_sample]
            
            try:
                if sample_path.exists():
                    with open(sample_path, 'r', encoding='utf-8') as f:
                        sample_content = f.read()
                    
                    st.session_state.input_text = sample_content
                    st.success(f"'{selected_sample}' を読み込みました")
                else:
                    # サンプルファイルが存在しない場合のデフォルトテキスト
                    default_text = """
                    The advancement of artificial intelligence has revolutionized numerous industries. 
                    Machine learning algorithms can now process vast amounts of data to identify patterns 
                    and make predictions with remarkable accuracy. However, the implementation of these 
                    technologies requires careful consideration of ethical implications and potential 
                    societal impacts.
                    """
                    st.session_state.input_text = default_text.strip()
                    st.info("デフォルトサンプルテキストを使用します")
                    
            except Exception as e:
                st.error(f"サンプル読み込みエラー: {e}")
    
    def run_analysis(self, enable_vocab, enable_grammar, enable_sentence):
        """分析の実行"""
        if not st.session_state.input_text.strip():
            st.warning("分析するテキストを入力してください")
            return
        
        if not any([enable_vocab, enable_grammar, enable_sentence]):
            st.warning("少なくとも1つの分析オプションを選択してください")
            return
        
        # 分析実行
        with st.spinner("分析を実行中..."):
            try:
                st.session_state.analysis_in_progress = True
                
                # 統合分析の実行
                result = self.text_analyzer.analyze_text_comprehensive(
                    st.session_state.input_text,
                    str(project_root / "data" / "vocabulary_books")
                )
                
                # 必要な分析結果のみ抽出
                filtered_result = {}
                
                if enable_vocab:
                    filtered_result['vocabulary_analysis'] = result.get('vocabulary_analysis', {})
                
                if enable_grammar:
                    filtered_result['grammar_analysis'] = result.get('grammar_analysis', {})
                
                if enable_sentence:
                    filtered_result['sentence_analysis'] = result.get('sentence_analysis', {})
                
                # 統合結果は常に含める
                filtered_result['comprehensive_assessment'] = result.get('comprehensive_assessment', {})
                filtered_result['integrated_report'] = result.get('integrated_report', {})
                filtered_result['basic_statistics'] = result.get('basic_statistics', {})
                filtered_result['metadata'] = result.get('metadata', {})
                
                st.session_state.analysis_result = filtered_result
                st.success("分析が完了しました！")
                
            except Exception as e:
                st.error(f"分析エラー: {e}")
                logger.error(f"Analysis error: {e}")
            
            finally:
                st.session_state.analysis_in_progress = False
    
    def render_main_content(self):
        """メインコンテンツの描画"""
        if st.session_state.analysis_result is None:
            self.render_welcome_page()
        else:
            self.render_analysis_results()
    
    def render_welcome_page(self):
        """ウェルカムページの描画"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="analysis-section" style="text-align: center;">
                <h2>🎯 ReadingAssist Analyzer へようこそ</h2>
                <p>このアプリは英文読解における単語帳の有効性と文章の構造的特徴を総合的に分析します。</p>
                
                <h3>📊 分析機能</h3>
                <ul style="text-align: left; display: inline-block;">
                    <li><strong>語彙分析</strong>: Target 1900/1400、システム英単語等の単語帳カバレッジ</li>
                    <li><strong>文法分析</strong>: 関係代名詞、仮定法、完了形等の出現頻度と難易度</li>
                    <li><strong>文構造分析</strong>: 文長、複雑さ、読みやすさ指標</li>
                    <li><strong>総合評価</strong>: 読解難易度と学習推奨事項</li>
                </ul>
                
                <h3>🚀 使い方</h3>
                <p>左のサイドバーから分析したい英文を入力し、「分析実行」ボタンをクリックしてください。</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_analysis_results(self):
        """分析結果の描画"""
        result = st.session_state.analysis_result
        
        # タブの作成
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 総合評価", "📚 語彙分析", "📝 文法分析", "🔗 文構造分析", "📋 詳細レポート"
        ])
        
        with tab1:
            self.render_comprehensive_assessment(result)
        
        with tab2:
            if 'vocabulary_analysis' in result:
                self.render_vocabulary_analysis(result['vocabulary_analysis'])
            else:
                st.info("語彙分析が無効化されています")
        
        with tab3:
            if 'grammar_analysis' in result:
                self.render_grammar_analysis(result['grammar_analysis'])
            else:
                st.info("文法分析が無効化されています")
        
        with tab4:
            if 'sentence_analysis' in result:
                self.render_sentence_analysis(result['sentence_analysis'])
            else:
                st.info("文構造分析が無効化されています")
        
        with tab5:
            self.render_detailed_report(result)
    
    def render_comprehensive_assessment(self, result):
        """総合評価の描画"""
        assessment = result.get('comprehensive_assessment', {})
        report = result.get('integrated_report', {})
        
        if not assessment:
            st.warning("総合評価データがありません")
            return
        
        # 総合評価メトリクス
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "総合難易度",
                assessment.get('difficulty_level', '不明'),
                help="テキスト全体の読解難易度"
            )
        
        with col2:
            st.metric(
                "読解レベル",
                assessment.get('reading_level', '不明'),
                help="推奨される学習レベル"
            )
        
        with col3:
            st.metric(
                "推定読解時間",
                f"{assessment.get('estimated_reading_time_minutes', 0)}分",
                help="平均的な読解にかかる時間"
            )
        
        with col4:
            st.metric(
                "総合スコア",
                f"{assessment.get('overall_difficulty_score', 0):.1f}",
                help="難易度を数値化したスコア"
            )
        
        # スコア内訳の可視化
        st.subheader("📈 難易度スコア内訳")
        
        scores = assessment.get('component_scores', {})
        if scores:
            score_df = pd.DataFrame([
                {'分析項目': '語彙', 'スコア': scores.get('vocabulary_score', 0)},
                {'分析項目': '文法', 'スコア': scores.get('grammar_score', 0)},
                {'分析項目': '文構造', 'スコア': scores.get('sentence_score', 0)}
            ])
            
            fig = px.bar(
                score_df, 
                x='分析項目', 
                y='スコア',
                title="各分析項目の難易度スコア",
                color='スコア',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # 主要な課題
        executive_summary = report.get('executive_summary', {})
        key_challenges = executive_summary.get('key_challenges', [])
        
        if key_challenges:
            st.subheader("⚠️ 主要な学習課題")
            for i, challenge in enumerate(key_challenges, 1):
                st.markdown(f"""
                <div class="challenge-box">
                    <strong>{i}.</strong> {challenge}
                </div>
                """, unsafe_allow_html=True)
        
        # 学習推奨事項
        study_recommendations = report.get('study_recommendations', {})
        if study_recommendations:
            st.subheader("💡 学習推奨事項")
            
            priority_areas = study_recommendations.get('priority_areas', [])
            if priority_areas:
                st.markdown(f"""
                <div class="recommendation-box">
                    <strong>優先学習分野:</strong> {', '.join(priority_areas)}
                </div>
                """, unsafe_allow_html=True)
            
            # 推奨事項の詳細表示
            for area, recommendations in study_recommendations.items():
                if area != 'priority_areas' and recommendations:
                    with st.expander(f"📋 {area}"):
                        for rec in recommendations:
                            st.write(f"• {rec}")
    
    def render_vocabulary_analysis(self, vocab_analysis):
        """語彙分析結果の描画"""
        st.subheader("📚 語彙分析結果")
        
        summary = vocab_analysis.get('summary', {})
        coverage = vocab_analysis.get('vocabulary_coverage', {})
        
        if not coverage:
            st.warning("語彙分析データがありません")
            return
        
        # 基本統計
        text_stats = vocab_analysis.get('text_statistics', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("抽出総単語数", f"{text_stats.get('total_words', 0):,}")
        with col2:
            st.metric("ユニーク単語数", f"{text_stats.get('unique_words', 0):,}")
        with col3:
            best_book = summary.get('best_coverage_book', {})
            if best_book:
                st.metric("最適単語帳", best_book.get('name', '不明'))
        
        # 単語帳カバレッジ比較
        st.subheader("📊 単語帳別カバレッジ比較")
        
        coverage_data = []
        for book_name, data in coverage.items():
            coverage_data.append({
                '単語帳': book_name,
                '語彙カバレッジ率(%)': data.get('vocabulary_coverage_rate', 0),
                '単語帳使用率(%)': data.get('vocabulary_utilization_rate', 0),
                '一致語数': data.get('matched_words_count', 0)
            })
        
        if coverage_data:
            df = pd.DataFrame(coverage_data)
            
            # カバレッジ率の棒グラフ
            fig = px.bar(
                df, 
                x='単語帳', 
                y='語彙カバレッジ率(%)',
                title="語彙カバレッジ率（入試語彙の何%が単語帳に含まれるか）",
                color='語彙カバレッジ率(%)',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 詳細データテーブル
            st.subheader("📋 詳細データ")
            st.dataframe(df, use_container_width=True)
        
        # 頻出単語
        word_frequencies = vocab_analysis.get('text_statistics', {}).get('word_frequencies', {})
        if word_frequencies:
            st.subheader("🔥 頻出単語 Top 20")
            
            freq_df = pd.DataFrame([
                {'単語': word, '出現回数': freq}
                for word, freq in list(word_frequencies.items())[:20]
            ])
            
            fig = px.bar(
                freq_df, 
                x='出現回数', 
                y='単語',
                orientation='h',
                title="頻出単語ランキング"
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_grammar_analysis(self, grammar_analysis):
        """文法分析結果の描画"""
        st.subheader("📝 文法分析結果")
        
        summary = grammar_analysis.get('summary', {})
        grammar_items = grammar_analysis.get('grammar_items', {})
        difficulty_analysis = grammar_analysis.get('difficulty_analysis', {})
        
        if not grammar_items:
            st.warning("文法分析データがありません")
            return
        
        # 基本統計
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("文法項目数", summary.get('total_grammar_items', 0))
        with col2:
            st.metric("文法密度", f"{summary.get('grammar_density', 0):.2f}%")
        with col3:
            st.metric("複雑度レベル", summary.get('complexity_level', '不明'))
        with col4:
            st.metric("平均難易度", f"{summary.get('average_difficulty_score', 0):.2f}")
        
        # 文法項目出現頻度
        st.subheader("📊 文法項目出現頻度")
        
        grammar_data = []
        for name, data in grammar_items.items():
            if data.get('count', 0) > 0:
                grammar_data.append({
                    '文法項目': name,
                    '出現回数': data.get('count', 0),
                    '頻度(/100語)': data.get('frequency_per_100_words', 0),
                    '難易度レベル': data.get('difficulty_level', 'basic'),
                    '重要度': data.get('importance', 'medium')
                })
        
        if grammar_data:
            df = pd.DataFrame(grammar_data)
            df = df.sort_values('出現回数', ascending=False)
            
            # 出現頻度の棒グラフ
            fig = px.bar(
                df.head(10), 
                x='文法項目', 
                y='出現回数',
                title="文法項目別出現回数 Top 10",
                color='難易度レベル',
                color_discrete_map={
                    'basic': '#90EE90',
                    'intermediate': '#FFD700', 
                    'advanced': '#FF6B6B'
                }
            )
            fig.update_layout(height=400)
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # 詳細データテーブル
            st.subheader("📋 文法項目詳細")
            st.dataframe(df, use_container_width=True)
        
        # 難易度分布
        if difficulty_analysis:
            st.subheader("📈 難易度別分布")
            
            dist_data = []
            for level, data in difficulty_analysis.items():
                if data.get('count', 0) > 0:
                    dist_data.append({
                        'レベル': level,
                        '出現回数': data.get('count', 0),
                        '割合(%)': data.get('percentage', 0)
                    })
            
            if dist_data:
                df_dist = pd.DataFrame(dist_data)
                
                fig = px.pie(
                    df_dist, 
                    values='出現回数', 
                    names='レベル',
                    title="文法項目難易度分布"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_sentence_analysis(self, sentence_analysis):
        """文構造分析結果の描画"""
        st.subheader("🔗 文構造分析結果")
        
        basic_stats = sentence_analysis.get('basic_statistics', {})
        length_analysis = sentence_analysis.get('sentence_length_analysis', {})
        complexity = sentence_analysis.get('complexity_analysis', {})
        readability = sentence_analysis.get('readability_scores', {})
        
        # 基本統計
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総文数", basic_stats.get('total_sentences', 0))
        with col2:
            st.metric("平均文長", f"{basic_stats.get('avg_words_per_sentence', 0):.1f}語")
        with col3:
            st.metric("複雑度レベル", complexity.get('complexity_level', '不明'))
        with col4:
            st.metric("読みやすさ", readability.get('reading_level', '不明'))
        
        # 文長分布
        if length_analysis:
            st.subheader("📊 文長分布")
            
            distribution = length_analysis.get('length_distribution', {})
            if distribution:
                dist_data = []
                for category, data in distribution.items():
                    category_name = {
                        'short_sentences': '短文(1-10語)',
                        'medium_sentences': '中文(11-20語)',
                        'long_sentences': '長文(21-30語)',
                        'very_long_sentences': '超長文(31語以上)'
                    }.get(category, category)
                    
                    dist_data.append({
                        'カテゴリ': category_name,
                        '文数': data.get('count', 0),
                        '割合(%)': data.get('percentage', 0)
                    })
                
                df_dist = pd.DataFrame(dist_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_bar = px.bar(
                        df_dist, 
                        x='カテゴリ', 
                        y='文数',
                        title="文長別文数"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    fig_pie = px.pie(
                        df_dist, 
                        values='文数', 
                        names='カテゴリ',
                        title="文長分布"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
        
        # 読みやすさ指標
        if readability:
            st.subheader("📈 読みやすさ指標")
            
            readability_data = [
                {'指標': 'Flesch Reading Ease', '値': readability.get('flesch_reading_ease', 0)},
                {'指標': 'Flesch-Kincaid Grade', '値': readability.get('flesch_kincaid_grade', 0)},
                {'指標': 'Automated Readability', '値': readability.get('automated_readability_index', 0)},
                {'指標': 'Coleman-Liau Index', '値': readability.get('coleman_liau_index', 0)},
                {'指標': 'Gunning Fog', '値': readability.get('gunning_fog', 0)}
            ]
            
            df_read = pd.DataFrame(readability_data)
            
            fig = px.bar(
                df_read, 
                x='指標', 
                y='値',
                title="各種読みやすさ指標"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        # 複雑さ分析
        if complexity:
            st.subheader("🔍 文構造複雑さ分析")
            
            indicators = complexity.get('complexity_indicators', {})
            if indicators:
                complexity_df = pd.DataFrame([
                    {'項目': '複文・重文', '数': indicators.get('complex_sentences', 0)},
                    {'項目': '単文', '数': indicators.get('simple_sentences', 0)},
                    {'項目': '等位接続', '数': indicators.get('coordination_count', 0)},
                    {'項目': '従属接続', '数': indicators.get('subordination_count', 0)},
                    {'項目': '関係節', '数': indicators.get('relative_clauses', 0)}
                ])
                
                fig = px.bar(
                    complexity_df, 
                    x='項目', 
                    y='数',
                    title="文構造要素の出現回数"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_detailed_report(self, result):
        """詳細レポートの描画"""
        st.subheader("📋 詳細分析レポート")
        
        report = result.get('integrated_report', {})
        
        if not report:
            st.warning("詳細レポートデータがありません")
            return
        
        # エグゼクティブサマリー
        executive_summary = report.get('executive_summary', {})
        if executive_summary:
            st.markdown("### 📊 エグゼクティブサマリー")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("総合評価", executive_summary.get('overall_assessment', '不明'))
                st.metric("読解レベル", executive_summary.get('reading_level', '不明'))
            with col2:
                st.metric("推定読解時間", f"{executive_summary.get('estimated_reading_time', 0)}分")
        
        # 詳細所見
        detailed_findings = report.get('detailed_findings', {})
        if detailed_findings:
            st.markdown("### 🔍 詳細所見")
            
            for category, findings in detailed_findings.items():
                category_name = {
                    'vocabulary_insights': '語彙分析所見',
                    'grammar_insights': '文法分析所見',
                    'structure_insights': '文構造分析所見'
                }.get(category, category)
                
                with st.expander(f"📋 {category_name}"):
                    if isinstance(findings, dict):
                        for key, value in findings.items():
                            if isinstance(value, list):
                                st.write(f"**{key}:**")
                                for item in value:
                                    st.write(f"• {item}")
                            else:
                                st.write(f"**{key}:** {value}")
        
        # アクションプラン
        action_plan = report.get('action_plan', {})
        if action_plan:
            st.markdown("### 🎯 アクションプラン")
            
            schedule = action_plan.get('study_schedule', {})
            if schedule:
                st.markdown("#### 📅 学習スケジュール")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("推奨学習期間", schedule.get('recommended_study_period', '不明'))
                with col2:
                    st.metric("1日の学習時間", schedule.get('daily_study_time', '不明'))
                
                weekly_goals = schedule.get('weekly_goals', [])
                if weekly_goals:
                    st.markdown("#### 📋 週次目標")
                    for goal in weekly_goals:
                        st.write(f"• {goal}")
            
            immediate_actions = action_plan.get('immediate_actions', [])
            if immediate_actions:
                st.markdown("#### ⚡ 即座に取り組むべき項目")
                for action in immediate_actions:
                    st.write(f"• {action}")
        
        # 生データの表示（オプション）
        with st.expander("🔧 生データ（デバッグ用）"):
            st.json(result)

def main():
    """メイン関数"""
    app = ReadingAssistApp()
    app.run()

if __name__ == "__main__":
    main()