# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このプロジェクトは、PDF形式の大学入試問題から英語の単語を抽出し、複数の単語帳（Target 1900/1400、システム英単語、LEAP、鉄壁、Target 1200）との一致率を分析するシステムです。OCR、自然言語処理、機械学習、そしてStreamlitダッシュボードを組み合わせて、大学別・学部別の語彙分析を提供します。

## 主要なコマンド

### 環境セットアップ
```bash
# 仮想環境を有効化
source env/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# Poppler（PDFイメージ変換）をインストール（macOS）
brew install poppler

# Tesseract OCR をインストール（macOS）
brew install tesseract
```

### 基本的な実行コマンド
```bash
# 1. 複数単語帳（Target 1900/1400, システム英単語, LEAP, 鉄壁、Target 1200）の語彙分析
python vocabulary_analyzer_multi.py

# 2. Streamlitダッシュボード起動
cd streamlit-vocab-analyzer
streamlit run streamlit_app.py

# 3. Streamlit用データ抽出（ダッシュボード用軽量化）
python utils/data_processor.py
```

## アーキテクチャ

### コアコンポーネント

1. **MultiVocabularyAnalyzer** (`vocabulary_analyzer_multi.py`)
   - 6つの単語帳同時分析（Target 1900/1400/1200, システム英単語, LEAP, 鉄壁）
   - 各単語帳のカバレッジ率・抽出精度の比較分析
   - 大学・学部別の複数単語帳分析
   - NLTK WordNetLemmatizer による語形正規化（動詞形・名詞形両方向）
   - 最適単語帳選択のための推奨事項生成

2. **Streamlitダッシュボード** (`streamlit-vocab-analyzer/`)
   - **streamlit_app.py**: メインアプリケーション（概要・大学別詳細・比較分析）
   - **utils/data_processor.py**: 分析結果をStreamlit用に軽量化
   - **vocab_data.py**: 組み込み単語帳データ（6つの単語帳をハードコード）
   - JSONファイルアップロード機能で語彙分析を実行

### データフロー
```
JSON files (extracted_data) → MultiVocabularyAnalyzer → 
Word normalization → Lemmatization → 
Multi-vocabulary analysis → multi_vocabulary_analysis_report.json

↓ (Streamlit用データ変換)

multi_vocabulary_analysis_report.json → utils/data_processor.py → 
streamlit-vocab-analyzer/data/analysis_data.json → Streamlit Dashboard
```

### 重要なデータファイルと形式

#### 入力ファイル
- `extraction_results_pure_english.json`: 抽出された英語テキスト（全文＋語彙）
- `target1900.csv`: Target 1900 単語帳データ（BOM付きUTF-8、'word'列必須）
- `target1400.csv`: Target 1400 単語帳データ（BOM付きUTF-8、'単語'列必須）
- `target1200.csv`: Target 1200 単語帳データ（BOM付きUTF-8、'単語'列必須）
- `システム英単語.csv`: システム英単語データ（BOM付きUTF-8、'英語'列必須）
- `LEAP.csv`: LEAP単語帳データ（BOM付きUTF-8、'英語'列必須）
- `鉄壁.csv`: 鉄壁単語帳データ（BOM付きUTF-8、'英語'列必須）

#### 出力ファイル
- `multi_vocabulary_analysis_report.json`: 複数単語帳分析レポート
- `streamlit-vocab-analyzer/data/analysis_data.json`: Streamlit用軽量化データ
- `function_words.json`: 機能語データ（ストップワード除去用）

### 設定要件

- **NLTK データ**: 初回実行時に自動ダウンロード（punkt, stopwords, wordnet, averaged_perceptron_tagger）
- **Streamlit**: ダッシュボード表示用 (`pip install streamlit`)
- **Plotly**: インタラクティブチャート用 (`pip install plotly`)

### 重要な技術仕様

#### 語彙分析指標算出
```python
vocabulary_utilization_rate = (一致単語数 ÷ 単語帳総単語数) × 100  # 単語帳使用率
vocabulary_coverage_rate = (一致単語数 ÷ 抽出ユニーク単語数) × 100  # 語彙カバレッジ率
```

#### 大学名・学部抽出ロジック
`_extract_university_name()` メソッドはファイル名から大学・学部を自動識別。早稲田大学・慶應義塾大学は学部別に分離して分析。

#### Streamlitダッシュボードの機能
- **JSONファイルアップロード**: 複数ファイル対応、新旧形式の自動判別
- **インタラクティブ分析**: 大学・学部選択による動的フィルタリング
- **可視化チャート**: Plotlyによる棒グラフ、ヒートマップ、散布図
- **基礎語彙除外**: Target 1200除外による高度語彙のみの分析
- **比較分析**: 複数大学の同時比較とランキング表示

#### 語彙正規化プロセス
1. 基本クリーニング（記号除去、小文字化）
2. 長さフィルタ（2文字以上）
3. 数字除外
4. Lemmatization（動詞形→名詞形の順で原形化）
5. ストップワード除去

### 単語カウントの重要な注意点

- **報告される単語数**: 内容語のみ（ストップワード除外後）
- **実際の英文単語数**: 内容語の約2.5-3倍（ストップワード含む）
- **機能語は除外**: the, and, or, but, in, on, at, to, of, for, with, by, from, is, was, are, were等は分析対象外
- **語彙分析**: Target 1900も内容語中心のため、現在の処理が適切

### 複数単語帳分析の指標

#### 各単語帳の評価指標
- **単語帳使用率**: 単語帳の何%が入試に出現したか = 一致語数 ÷ 単語帳総語数 × 100
- **語彙カバレッジ率**: 入試英単語の何%が単語帳に含まれるか = 一致語数 ÷ 抽出ユニーク語数 × 100
- **一致語数**: 抽出語と単語帳の重複語数

#### 分析結果の3つのカテゴリ

1. **matched_words**: 単語帳にあり、かつ入試問題から抽出された単語
   - 学習効果が確認できる重要語彙
   - 単語帳使用率の分子となる

2. **unmatched_from_target**: 単語帳にあるが、入試問題から抽出されなかった単語
   - 入試問題で出現しなかった単語帳語彙
   - 追加学習が必要な可能性がある単語

3. **unmatched_from_extracted**: 入試問題から抽出されたが、単語帳にない単語
   - 単語帳では学習しない高度・専門語彙
   - 語彙カバレッジ率の分母に含まれるが一致には寄与しない

#### 6つの単語帳の特徴
- **Target 1200**: 基礎語彙中心（ダッシュボードで除外可能）
- **Target 1400**: 中級語彙、通常最高語彙カバレッジ率
- **Target 1900**: 上級語彙、総合バランス重視
- **システム英単語**: システマティックな構成
- **LEAP**: 4技能対応、実用性重視
- **鉄壁**: 難関大学対策、高語彙カバレッジ率傾向

### デバッグ時の確認ポイント

1. **語彙分析品質**: `vocabulary_analyzer_multi.py` の出力ファイル確認
2. **Lemmatization**: 語形変化単語の原形化効果
3. **単語帳使用率**: 各単語帳で 10-30% 程度が標準的
4. **語彙カバレッジ率**: 各単語帳で 30-50% 程度が標準的
5. **Streamlitダッシュボード**: JSONアップロード機能とチャート表示

### バックアップとリストア

#### バックアップ作成
```bash
# タイムスタンプ付きバックアップディレクトリ作成
backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# 全ファイルをバックアップ
cp -r *.py *.csv *.json *.md *.txt requirements.txt CLAUDE.md "$backup_dir"/
cp -r PDF/ "$backup_dir"/
```

#### 新規JSONファイル処理ワークフロー
1. 語彙分析実行: `python vocabulary_analyzer_multi.py`
2. Streamlit用データ生成: `python utils/data_processor.py`
3. ダッシュボード確認: `cd streamlit-vocab-analyzer && streamlit run streamlit_app.py`

### 重要な実装詳細

#### CSVファイルの列名対応
- `target1900.csv` → `'word'` 列
- `target1400.csv`, `target1200.csv` → `'単語'` 列  
- `システム英単語.csv`, `LEAP.csv`, `鉄壁.csv` → `'英語'` 列

#### 大学名自動認識パターン
- 早稲田大学（学部別分析対応）: 10学部を個別認識
- 慶應義塾大学（学部別分析対応）: 10学部を個別認識  
- その他認識対象: 東京大学（単一エントリ）

#### Streamlitダッシュボードの実装詳細
- **ファイル構造**: `streamlit-vocab-analyzer/` サブディレクトリ
- **データ読み込み**: JSONファイルアップロード機能
- **組み込み単語帳**: `vocab_data.py` に6つの単語帳をハードコード
- **可視化**: Plotlyによるインタラクティブチャート
- **フィルタリング**: 大学・学部選択、基礎語彙除外オプション

#### エラー対処
- **BOM問題**: pandas.read_csv で `encoding='utf-8-sig'` 使用必須
- **NLTK データ**: 初回実行時の自動ダウンロード確認
- **Streamlit起動**: ポート8501でのローカル実行