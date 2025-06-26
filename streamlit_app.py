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
        "英語分析用JSONファイルを選択（複数選択可能）",
        type=["json"],
        accept_multiple_files=True,
        help="OCR処理済みの英語抽出結果JSONファイルをアップロードしてください。大学名_年度_英語_学部名.json形式のファイルに対応しています。"
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
        👆 **英語分析用JSONファイルをアップロードしてください**
        
        📋 対応しているファイル形式:
        - **新形式**: `大学名_年度_英語_学部名.json` (file_info + content構造)
        - **旧形式**: `extraction_results_pure_english.json` (extraction_summary + extracted_data構造)
        
        💡 複数ファイルをまとめて選択して一括分析が可能です
        """)

def merge_multiple_json_files(uploaded_files):
    """複数のJSONファイルを統合（実際のJSONフォーマットに対応）"""
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
            
            # 新しいフォーマット対応
            if 'file_info' in file_content and 'content' in file_content:
                # 新しいフォーマット: {"file_info": {...}, "content": {"extracted_words": [...]}}
                file_info = file_content.get('file_info', {})
                content = file_content.get('content', {})
                extraction_results = file_content.get('extraction_results', {})
                
                # サマリー情報を統合
                combined_data['extraction_summary']['total_source_files'] += 1
                combined_data['extraction_summary']['total_words_extracted'] += extraction_results.get('total_words', 0)
                
                # 抽出データを統合
                extracted_entry = {
                    'source_file': file_info.get('source_file', uploaded_file.name),
                    'pages_processed': file_info.get('processed_pages', 0),
                    'ocr_confidence': file_info.get('ocr_confidence', 0),
                    'extracted_words': content.get('extracted_words', []),
                    'english_passages': content.get('english_passages', [])
                }
                combined_data['extracted_data'].append(extracted_entry)
                
            else:
                # 旧フォーマット対応
                file_summary = file_content.get('extraction_summary', {})
                combined_data['extraction_summary']['total_source_files'] += file_summary.get('total_source_files', 0)
                combined_data['extraction_summary']['total_words_extracted'] += file_summary.get('total_words_extracted', 0)
                
                file_extracted_data = file_content.get('extracted_data', [])
                combined_data['extracted_data'].extend(file_extracted_data)
        
        return combined_data
        
    except Exception as e:
        st.error(f"ファイル統合中にエラーが発生しました: {str(e)}")
        st.error(f"詳細: {str(e)}")
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
    
    # 前回の選択状態を取得
    previous_selection = st.session_state.get('selected_universities', [])
    
    selected_universities = st.sidebar.multiselect(
        "大学・学部を選択",
        available_universities,
        default=available_universities[:3] if len(available_universities) >= 3 else available_universities,
        help="比較分析する大学・学部を選択してください",
        key="university_selector"
    )
    
    # 選択が変更された場合の検出
    if selected_universities != previous_selection:
        st.session_state.selected_universities = selected_universities
        st.session_state.selection_changed = True
        st.sidebar.success("🔄 選択を更新しました")
    else:
        st.session_state.selected_universities = selected_universities
        st.session_state.selection_changed = False
    
    st.sidebar.markdown("---")
    
    # 指標説明
    st.sidebar.subheader("💡 指標の意味")
    st.sidebar.markdown("""
    **カバレッジ率**: 単語帳の何%が入試に出現
    
    **抽出精度**: 学習語彙の何%が入試に出現
    
    **一致語数**: 実際に一致した語数
    """)
    
    # 分析オプション
    st.sidebar.subheader("🔧 分析オプション")
    
    exclude_basic = st.sidebar.checkbox(
        "基礎語彙を除外して分析",
        value=False,
        help="Target 1200の基礎語彙を除外して、より高度な語彙のみを分析します"
    )
    
    if exclude_basic:
        st.sidebar.info("📝 Target 1200の基礎語彙を除外した高度語彙分析を実行します")
    else:
        st.sidebar.info("📝 全語彙を含む標準分析を実行します")
    
    # 除外設定をセッション状態に保存
    st.session_state.exclude_basic_vocab = exclude_basic
    
    st.sidebar.markdown("---")
    
    # データ情報
    st.sidebar.subheader("📋 データ情報")
    overall_summary = analysis_data.get('overall_summary', {})
    st.sidebar.write(f"**総大学数**: {len(available_universities)}")
    st.sidebar.write(f"**選択中**: {len(selected_universities)}大学・学部")
    st.sidebar.write(f"**単語帳数**: 5種類")
    st.sidebar.write(f"**総単語数**: {overall_summary.get('total_words_extracted', 0):,}")
    
    if exclude_basic:
        st.sidebar.write(f"**分析モード**: 高度語彙のみ")

def recalculate_vocabulary_analysis_with_basic_exclusion(analysis_data, exclude_basic_vocab=False):
    """基礎語彙除外オプションに基づいて語彙分析を再計算"""
    if not exclude_basic_vocab:
        return analysis_data
    
    # 基礎語彙データを取得
    from vocab_data import get_embedded_vocabulary_data
    vocab_books = get_embedded_vocabulary_data()
    basic_vocab = vocab_books.get('Target 1200', set())
    
    # 分析データをコピー
    recalculated_data = {
        'overall_summary': analysis_data.get('overall_summary', {}),
        'vocabulary_summary': {},
        'university_analysis': {}
    }
    
    # 各大学のデータを基礎語彙除外で再計算
    university_analysis = analysis_data.get('university_analysis', {})
    
    for univ_name, univ_data in university_analysis.items():
        # 元の抽出語彙から基礎語彙を除外
        original_vocab_coverage = univ_data.get('vocabulary_coverage', {})
        
        # 各単語帳に対して再計算
        new_vocab_coverage = {}
        
        # 元の全抽出語彙を取得（新しいフィールドから）
        all_extracted_words = univ_data.get('all_extracted_words', [])
        
        # もしall_extracted_wordsがない場合は、旧方式で復元を試みる
        if not all_extracted_words:
            all_extracted_words = set()
            for vocab_name, coverage in original_vocab_coverage.items():
                all_extracted_words.update(coverage.get('matched_words', []))
            if 'Target 1900' in original_vocab_coverage:
                all_extracted_words.update(original_vocab_coverage['Target 1900'].get('unmatched_words', []))
            all_extracted_words = list(all_extracted_words)
        
        # 基礎語彙を除外（元の語彙数と除外後の数を記録）
        original_count = len(all_extracted_words)
        filtered_words = [word for word in all_extracted_words if word not in basic_vocab]
        excluded_count = original_count - len(filtered_words)
        
        # デバッグ情報を表示
        if original_count > 0:
            st.caption(f"🔍 {univ_name}: 元の語彙{original_count}語 → 基礎語彙{excluded_count}語除外 → 高度語彙{len(filtered_words)}語")
        
        # 各単語帳との再比較
        for vocab_name, vocab_set in vocab_books.items():
            matched_words = [word for word in filtered_words if word in vocab_set]
            matched_count = len(matched_words)
            
            target_coverage_rate = (matched_count / len(vocab_set)) * 100 if vocab_set else 0
            extraction_precision = (matched_count / len(filtered_words)) * 100 if filtered_words else 0
            
            unmatched_words = [word for word in filtered_words if word not in vocab_set]
            
            new_vocab_coverage[vocab_name] = {
                'matched_words_count': matched_count,
                'target_coverage_rate': target_coverage_rate,
                'extraction_precision': extraction_precision,
                'matched_words': matched_words[:20],  # 表示用に20語のみ保存
                'unmatched_words': unmatched_words,
                'unmatched_count': len(unmatched_words)
            }
        
        # 大学データを更新
        recalculated_data['university_analysis'][univ_name] = {
            'source_file': univ_data.get('source_file', ''),
            'total_words': univ_data.get('total_words', 0),
            'unique_words': len(filtered_words),  # 基礎語彙除外後の語彙数
            'original_unique_words': original_count,  # 元の語彙数
            'excluded_basic_words': excluded_count,  # 除外された基礎語彙数
            'vocabulary_coverage': new_vocab_coverage,
            'pages_processed': univ_data.get('pages_processed', 0),
            'basic_vocab_excluded': True  # 除外フラグ
        }
    
    # 全体サマリーを再計算
    if recalculated_data['university_analysis']:
        vocab_summary = {}
        
        for vocab_name in vocab_books.keys():
            coverage_rates = []
            precisions = []
            total_matched = 0
            
            for univ_data in recalculated_data['university_analysis'].values():
                vocab_coverage = univ_data.get('vocabulary_coverage', {}).get(vocab_name, {})
                if vocab_coverage:
                    coverage_rates.append(vocab_coverage.get('target_coverage_rate', 0))
                    precisions.append(vocab_coverage.get('extraction_precision', 0))
                    total_matched += vocab_coverage.get('matched_words_count', 0)
            
            if coverage_rates:
                vocab_summary[vocab_name] = {
                    'average_coverage_rate': sum(coverage_rates) / len(coverage_rates),
                    'average_extraction_precision': sum(precisions) / len(precisions),
                    'total_matched_words': total_matched
                }
        
        recalculated_data['vocabulary_summary'] = vocab_summary
    
    return recalculated_data

def filter_analysis_data_by_selection(analysis_data, selected_universities):
    """選択された大学のデータのみでフィルタリングした分析結果を作成"""
    if not selected_universities:
        return analysis_data
    
    # 元の分析データから選択された大学のみを抽出
    filtered_data = {
        'overall_summary': analysis_data.get('overall_summary', {}),
        'vocabulary_summary': {},
        'university_analysis': {}
    }
    
    # 選択された大学のデータを抽出
    university_analysis = analysis_data.get('university_analysis', {})
    for univ_name in selected_universities:
        if univ_name in university_analysis:
            filtered_data['university_analysis'][univ_name] = university_analysis[univ_name]
    
    # 選択された大学のデータから語彙サマリーを再計算
    if filtered_data['university_analysis']:
        vocab_books = load_vocabulary_books()
        vocab_summary = {}
        
        for vocab_name in vocab_books.keys():
            coverage_rates = []
            precisions = []
            total_matched = 0
            
            for univ_data in filtered_data['university_analysis'].values():
                vocab_coverage = univ_data.get('vocabulary_coverage', {}).get(vocab_name, {})
                if vocab_coverage:
                    coverage_rates.append(vocab_coverage.get('target_coverage_rate', 0))
                    precisions.append(vocab_coverage.get('extraction_precision', 0))
                    total_matched += vocab_coverage.get('matched_words_count', 0)
            
            if coverage_rates:
                vocab_summary[vocab_name] = {
                    'average_coverage_rate': sum(coverage_rates) / len(coverage_rates),
                    'average_extraction_precision': sum(precisions) / len(precisions),
                    'total_matched_words': total_matched
                }
        
        filtered_data['vocabulary_summary'] = vocab_summary
    
    return filtered_data

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
        
        # extraction_summary の詳細確認
        summary = extraction_data.get('extraction_summary', {})
        st.write(f"extraction_summary: {summary}")
        
        # extracted_data の詳細確認
        extracted_data_list = extraction_data.get('extracted_data', [])
        st.write(f"extracted_data type: {type(extracted_data_list)}")
        st.write(f"extracted_data length: {len(extracted_data_list)}")
        
        if not extracted_data_list:
            st.error("❌ extracted_data リストが空です")
            st.write("**JSONファイル構造の確認:**")
            st.write("対応している形式:")
            st.code("""新形式:
{
  "file_info": {
    "source_file": "大学名_年度_英語_学部名.pdf",
    "processed_pages": 7,
    "ocr_confidence": 0.95
  },
  "content": {
    "extracted_words": ["word1", "word2", ...]
  }
}

旧形式:
{
  "extraction_summary": {...},
  "extracted_data": [
    {
      "source_file": "大学名_年度_英語_学部名.pdf",
      "extracted_words": ["word1", "word2", ...]
    }
  ]
}""")
            st.write("**現在のJSONファイル内容（一部）:**")
            import json
            st.code(json.dumps(extraction_data, indent=2, ensure_ascii=False)[:1000] + "...")
            return None
        
        st.success(f"✅ {len(extracted_data_list)}件のデータエントリを確認")
        
        # 最初のエントリの詳細確認
        if len(extracted_data_list) > 0:
            first_entry = extracted_data_list[0]
            st.write("**最初のエントリの確認:**")
            st.write(f"  - Keys: {list(first_entry.keys()) if isinstance(first_entry, dict) else 'Not a dict'}")
            if isinstance(first_entry, dict):
                st.write(f"  - source_file: '{first_entry.get('source_file', 'Missing')}'")
                words = first_entry.get('extracted_words', [])
                st.write(f"  - extracted_words count: {len(words) if isinstance(words, list) else 'Not a list'}")
                if isinstance(words, list) and len(words) > 0:
                    st.write(f"  - Sample words: {words[:5]}")
                else:
                    st.write(f"  - extracted_words content: {words}")
        
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
                
                # 抽出された単語を正規化（Lemmatization含む）
                extracted_words = entry.get('extracted_words', [])
                if not extracted_words:
                    st.warning(f"⚠️ エントリ {i+1}: extracted_words が空です")
                    continue
                
                # 基本的な正規化
                cleaned_words = [word.lower().strip() for word in extracted_words if word and len(word) > 1]
                
                # 基礎語彙除外オプションの確認
                exclude_basic = st.session_state.get('exclude_basic_vocab', False)
                if exclude_basic:
                    # Target 1200の基礎語彙を除外
                    basic_vocab = vocab_books.get('Target 1200', set())
                    cleaned_words = [word for word in cleaned_words if word not in basic_vocab]
                    st.write(f"  🔧 基礎語彙除外: Target 1200の{len(basic_vocab)}語を除外")
                
                # Lemmatization処理
                try:
                    from nltk.stem import WordNetLemmatizer
                    
                    lemmatizer = WordNetLemmatizer()
                    normalized_words = []
                    
                    for word in cleaned_words:
                        # 複数品詞でlemmatizeを試行
                        lemma_verb = lemmatizer.lemmatize(word, pos='v')  # 動詞
                        lemma_noun = lemmatizer.lemmatize(lemma_verb, pos='n')  # 名詞
                        
                        # より効果的な正規化を選択
                        if len(lemma_noun) < len(word):
                            normalized_words.append(lemma_noun)
                        elif len(lemma_verb) < len(word):
                            normalized_words.append(lemma_verb)
                        else:
                            normalized_words.append(word)
                    
                    unique_words = list(set(normalized_words))
                    
                    # Lemmatization効果を表示
                    original_unique = len(set(cleaned_words))
                    lemmatized_unique = len(unique_words)
                    if original_unique != lemmatized_unique:
                        st.write(f"  📝 Lemmatization効果: {original_unique}語 → {lemmatized_unique}語")
                    
                except Exception as lemma_error:
                    st.warning(f"⚠️ Lemmatization処理でエラー、基本正規化を使用: {str(lemma_error)}")
                    normalized_words = cleaned_words
                    unique_words = list(set(normalized_words))
                
                # 基礎語彙除外の効果を表示
                exclude_basic = st.session_state.get('exclude_basic_vocab', False)
                if exclude_basic:
                    basic_vocab = vocab_books.get('Target 1200', set())
                    original_unique = len(set([word.lower().strip() for word in extracted_words if word and len(word) > 1]))
                    excluded_count = original_unique - len(unique_words)
                    st.write(f"✅ {university_name}: {len(extracted_words)}語 → {original_unique}ユニーク語 → {len(unique_words)}高度語彙 (基礎語彙{excluded_count}語除外)")
                else:
                    st.write(f"✅ {university_name}: {len(extracted_words)}語 → {len(unique_words)}ユニーク語")
                
                # 各単語帳との比較分析
                vocab_coverage = {}
                for vocab_name, vocab_set in vocab_books.items():
                    matched_words = [word for word in unique_words if word in vocab_set]
                    matched_count = len(matched_words)
                    
                    target_coverage_rate = (matched_count / len(vocab_set)) * 100 if vocab_set else 0
                    extraction_precision = (matched_count / len(unique_words)) * 100 if unique_words else 0
                    
                    # カバーされていない単語（単語帳にない単語）
                    unmatched_words = [word for word in unique_words if word not in vocab_set]
                    
                    vocab_coverage[vocab_name] = {
                        'matched_words_count': matched_count,
                        'target_coverage_rate': target_coverage_rate,
                        'extraction_precision': extraction_precision,
                        'matched_words': matched_words[:20],  # 表示用に20語のみ保存
                        'unmatched_words': unmatched_words,  # 全てのカバーされていない単語を保存
                        'unmatched_count': len(unmatched_words)
                    }
            
                # 大学データを保存
                try:
                    analysis_result['university_analysis'][university_name] = {
                        'source_file': source_file,
                        'total_words': len(extracted_words),
                        'unique_words': len(unique_words),
                        'all_extracted_words': unique_words,  # 全抽出語彙を保存（基礎語彙除外用）
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
    
    # 基礎語彙除外オプションの確認
    exclude_basic = st.session_state.get('exclude_basic_vocab', False)
    
    # 基礎語彙除外が有効な場合、データを再計算
    if exclude_basic:
        with st.spinner("基礎語彙除外モードで再計算中..."):
            analysis_data = recalculate_vocabulary_analysis_with_basic_exclusion(analysis_data, exclude_basic_vocab=True)
    
    # 選択された大学に基づいてデータをフィルタリング
    selected_universities = st.session_state.get('selected_universities', [])
    filtered_data = filter_analysis_data_by_selection(analysis_data, selected_universities)
    
    # 選択変更時の通知
    if st.session_state.get('selection_changed', False):
        mode_text = "（高度語彙のみ）" if exclude_basic else "（全語彙）"
        st.info(f"🔄 {len(selected_universities)}大学・学部の分析結果を表示中... {mode_text}")
    
    # 分析モードの表示
    if exclude_basic:
        st.success("🎯 **高度語彙分析モード**: Target 1200の基礎語彙を除外した分析結果を表示しています")
        st.caption("💡 カバレッジ率と抽出精度は、Target 1200の1,400語を除外した高度語彙で再計算されています")
        
        # 基礎語彙除外統計の表示
        show_basic_exclusion_stats(filtered_data)
        
    else:
        st.info("📊 **標準分析モード**: 全語彙を含む分析結果を表示しています")
    
    # メインタブの作成
    tab1, tab2, tab3 = st.tabs(["🏠 概要分析", "🏫 大学別詳細", "📊 比較分析"])
    
    with tab1:
        show_overview_analysis(filtered_data)
    
    with tab2:
        show_university_analysis(filtered_data)
    
    with tab3:
        show_comparison_analysis(filtered_data)

def show_basic_exclusion_stats(analysis_data: dict):
    """基礎語彙除外の統計情報を表示"""
    university_analysis = analysis_data.get('university_analysis', {})
    
    if not university_analysis:
        return
    
    # 統計情報を集計
    total_original = 0
    total_excluded = 0
    total_remaining = 0
    
    for univ_data in university_analysis.values():
        if univ_data.get('basic_vocab_excluded', False):
            total_original += univ_data.get('original_unique_words', 0)
            total_excluded += univ_data.get('excluded_basic_words', 0)
            total_remaining += univ_data.get('unique_words', 0)
    
    if total_original > 0:
        exclusion_rate = (total_excluded / total_original) * 100
        
        st.markdown("### 🔧 基礎語彙除外統計")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 元の語彙数",
                f"{total_original:,}語",
                help="基礎語彙除外前の総ユニーク語彙数"
            )
        
        with col2:
            st.metric(
                "❌ 除外された語彙",
                f"{total_excluded:,}語",
                delta=f"-{exclusion_rate:.1f}%",
                help="Target 1200に含まれる基礎語彙数"
            )
        
        with col3:
            st.metric(
                "✅ 高度語彙数",
                f"{total_remaining:,}語",
                help="基礎語彙除外後の高度語彙数"
            )
        
        with col4:
            st.metric(
                "🎯 高度語彙率",
                f"{100-exclusion_rate:.1f}%",
                help="全語彙に占める高度語彙の割合"
            )
        
        st.markdown("---")

def show_overview_analysis(analysis_data: dict):
    """概要分析タブのコンテンツ"""
    
    # 簡潔な定義（常時表示）
    exclude_basic = st.session_state.get('exclude_basic_vocab', False)
    
    col1, col2, col3 = st.columns(3)
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
    
    with col3:
        if exclude_basic:
            st.warning("""
            **🎯 高度語彙分析モード**  
            Target 1200の基礎語彙（1,400語）を除外し、高度語彙のみでカバレッジ率と抽出精度を再計算。
            """)
        else:
            st.info("""
            **📊 標準分析モード**  
            全語彙を含む標準的な分析。
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
        
        # カバーされていない単語の統計
        st.markdown("---")
        st.subheader("📝 カバー外語彙の統計")
        st.info("""
        各単語帳でカバーされていない語彙の統計情報です。これらは追加学習対象となる可能性があります。
        """)
        
        # 選択された大学のカバー外語彙統計を計算
        selected_universities = st.session_state.get('selected_universities', [])
        university_analysis = analysis_data.get('university_analysis', {})
        
        if selected_universities and university_analysis:
            uncovered_stats = []
            
            for vocab_name in vocabulary_summary.keys():
                total_unmatched = 0
                total_words = 0
                
                for univ_name in selected_universities:
                    univ_data = university_analysis.get(univ_name, {})
                    vocab_coverage = univ_data.get('vocabulary_coverage', {}).get(vocab_name, {})
                    
                    total_unmatched += vocab_coverage.get('unmatched_count', 0)
                    total_words += univ_data.get('unique_words', 0)
                
                if total_words > 0:
                    uncovered_rate = (total_unmatched / len(selected_universities) / total_words * len(selected_universities)) * 100
                    uncovered_stats.append({
                        '単語帳': vocab_name,
                        'カバー外語数': total_unmatched // len(selected_universities),
                        'カバー外率(%)': round(uncovered_rate, 1)
                    })
            
            if uncovered_stats:
                uncovered_df = pd.DataFrame(uncovered_stats)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # カバー外語数の棒グラフ
                    fig_uncovered = px.bar(
                        uncovered_df,
                        x='単語帳',
                        y='カバー外語数',
                        title='単語帳別カバー外語数',
                        color='カバー外語数',
                        color_continuous_scale='Reds'
                    )
                    fig_uncovered.update_layout(height=400)
                    st.plotly_chart(fig_uncovered, use_container_width=True)
                
                with col2:
                    # カバー外率の棒グラフ
                    fig_uncovered_rate = px.bar(
                        uncovered_df,
                        x='単語帳',
                        y='カバー外率(%)',
                        title='単語帳別カバー外率',
                        color='カバー外率(%)',
                        color_continuous_scale='OrRd'
                    )
                    fig_uncovered_rate.update_layout(height=400)
                    st.plotly_chart(fig_uncovered_rate, use_container_width=True)
                
                # 統計テーブル
                st.dataframe(uncovered_df, use_container_width=True)

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
    
    # カバーされていない単語の表示
    st.markdown("---")
    st.subheader("📝 単語帳でカバーされていない語彙")
    st.info("""
    以下は入試問題から抽出されたが、各単語帳には含まれていない語彙です。  
    これらの語彙は追加学習が必要な可能性があります。
    """)
    
    # 単語帳選択
    vocab_tabs = st.tabs([f"📖 {vocab_name}" for vocab_name in vocab_coverage.keys()])
    
    for i, (vocab_name, vocab_stats) in enumerate(vocab_coverage.items()):
        with vocab_tabs[i]:
            unmatched_words = vocab_stats.get('unmatched_words', [])
            unmatched_count = vocab_stats.get('unmatched_count', 0)
            matched_count = vocab_stats.get('matched_words_count', 0)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric(
                    label="カバー外語数",
                    value=f"{unmatched_count:,}語",
                    delta=f"一致: {matched_count}語"
                )
                
                if unmatched_count > 0:
                    coverage_ratio = (matched_count / (matched_count + unmatched_count)) * 100
                    st.write(f"**語彙カバー率**: {coverage_ratio:.1f}%")
            
            with col2:
                if unmatched_words:
                    # 表示方法の選択
                    display_mode = st.radio(
                        "表示形式を選択:",
                        ["プレビュー表示", "全語彙表示", "ダウンロード用"],
                        key=f"display_mode_{vocab_name}_{selected_university}",
                        horizontal=True
                    )
                    
                    if display_mode == "プレビュー表示":
                        st.write("**カバーされていない主な語彙（最初の30語）:**")
                        displayed_words = unmatched_words[:30]
                        for j in range(0, len(displayed_words), 5):
                            word_group = displayed_words[j:j+5]
                            st.write("• " + " • ".join(word_group))
                        
                        if len(unmatched_words) > 30:
                            st.write(f"... 他 {len(unmatched_words) - 30}語")
                    
                    elif display_mode == "全語彙表示":
                        st.write(f"**カバーされていない全語彙（{len(unmatched_words)}語）:**")
                        
                        # ページネーション
                        words_per_page = 100
                        total_pages = (len(unmatched_words) + words_per_page - 1) // words_per_page
                        
                        if total_pages > 1:
                            page = st.selectbox(
                                f"ページを選択 (1-{total_pages})",
                                range(1, total_pages + 1),
                                key=f"page_{vocab_name}_{selected_university}"
                            )
                            start_idx = (page - 1) * words_per_page
                            end_idx = min(start_idx + words_per_page, len(unmatched_words))
                            page_words = unmatched_words[start_idx:end_idx]
                            
                            st.write(f"**ページ {page}/{total_pages} ({start_idx + 1}-{end_idx}語):**")
                        else:
                            page_words = unmatched_words
                        
                        # 10語ずつの行で表示
                        for j in range(0, len(page_words), 10):
                            word_group = page_words[j:j+10]
                            st.write("• " + " • ".join(word_group))
                    
                    elif display_mode == "ダウンロード用":
                        st.write("**ダウンロード・コピー用フォーマット:**")
                        
                        format_option = st.selectbox(
                            "フォーマットを選択:",
                            ["CSV形式", "リスト形式", "改行区切り"],
                            key=f"format_{vocab_name}_{selected_university}"
                        )
                        
                        if format_option == "CSV形式":
                            formatted_text = ", ".join(unmatched_words)
                        elif format_option == "リスト形式":
                            formatted_text = " • ".join(unmatched_words)
                        else:  # 改行区切り
                            formatted_text = "\n".join(unmatched_words)
                        
                        st.text_area(
                            f"カバーされていない全語彙 ({len(unmatched_words)}語)",
                            value=formatted_text,
                            height=300,
                            key=f"download_{vocab_name}_{selected_university}",
                            help="このテキストエリアから全ての単語をコピーできます"
                        )
                        
                        # 統計情報
                        st.write(f"**統計:** 総語数 {len(unmatched_words)}語")
                else:
                    st.success("🎉 すべての語彙がカバーされています！")

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