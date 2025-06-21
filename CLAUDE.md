# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このプロジェクトは、PDF形式の大学入試問題から英語の単語を抽出し、Target 1900という単語帳との一致率を分析するシステムです。OCR、自然言語処理、機械学習を組み合わせて、大学別・学部別の語彙分析を提供します。

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
# 1. PDFフォルダ内のファイルから英語テキストを抽出
python pdf_text_extractor.py

# 2a. Target 1900単語帳のみの語彙分析
python vocabulary_analyzer.py

# 2b. 複数単語帳（Target 1900/1400, システム英単語, LEAP, 鉄壁）の語彙分析
python vocabulary_analyzer_multi.py

# 3. 新規PDFファイル追加時のワンライン実行
python pdf_text_extractor.py && python vocabulary_analyzer_multi.py

# デバッグ・検証用スクリプト
python debug_extraction.py          # OCR抽出結果の詳細確認
python debug_normalization.py       # 正規化処理のデバッグ
python check_lemmatization.py       # Lemmatization効果の検証
```

## アーキテクチャ

### コアコンポーネント

1. **PDFTextExtractor** (`pdf_text_extractor.py`)
   - PDF → 画像変換 → OCR → LLM校正 → 英語抽出の完全パイプライン
   - 6種類の画像前処理技術（アンシャープマスク、適応閾値処理など）
   - OpenAI GPT-4o-mini による OCR テキスト校正
   - 言語検出による日本語コンテンツの自動除外
   - **重要**: ストップワード除去により内容語のみを抽出（機能語は除外）

2. **VocabularyAnalyzer** (`vocabulary_analyzer.py`)
   - Target 1900 単語帳との一致率分析
   - NLTK WordNetLemmatizer による語形正規化（動詞形・名詞形両方向）
   - 大学・学部別の詳細分析（ファイル名から自動分類）
   - 頻度層別分析（高頻度・中頻度・低頻度）

3. **MultiVocabularyAnalyzer** (`vocabulary_analyzer_multi.py`)
   - 5つの単語帳同時分析（Target 1900/1400, システム英単語, LEAP, 鉄壁）
   - 各単語帳のカバレッジ率・抽出精度の比較分析
   - 大学・学部別の複数単語帳分析
   - 最適単語帳選択のための推奨事項生成

### データフロー
```
PDF files → Image conversion → OCR → LLM correction → 
Language detection → English extraction → Word normalization → 
Lemmatization → Vocabulary analysis → JSON report
```

### 重要なデータファイルと形式

#### 入力ファイル
- `PDF/`: 処理対象のPDFファイル（大学名_年度_英語_学部名.pdf 形式）
- `target1900.csv`: Target 1900 単語帳データ（BOM付きUTF-8、'word'列必須）
- `target1400.csv`: Target 1400 単語帳データ（BOM付きUTF-8、'単語'列必須）
- `システム英単語.csv`: システム英単語データ（BOM付きUTF-8、'英語'列必須）
- `LEAP.csv`: LEAP単語帳データ（BOM付きUTF-8、'英語'列必須）
- `鉄壁.csv`: 鉄壁単語帳データ（BOM付きUTF-8、'英語'列必須）

#### 出力ファイル
- `extraction_results_pure_english.json`: 抽出された英語テキスト（全文＋語彙）
- `vocabulary_analysis_report.json`: Target 1900分析レポート
- `multi_vocabulary_analysis_report.json`: 複数単語帳分析レポート
- `comprehensive_analysis_summary.md`: 総合分析サマリー（人間が読みやすい形式）

### 設定要件

- **OpenAI API Key**: `.env` ファイルに `OPENAI_API_KEY=your_key` として設定
- **Tesseract OCR**: システムにインストール済みが必要
- **Poppler**: PDF画像変換用ライブラリ
- **NLTK データ**: 初回実行時に自動ダウンロード（punkt, stopwords, wordnet, averaged_perceptron_tagger）

### 重要な技術仕様

#### OCR信頼度算出
```python
confidence = (英語文字比率×0.4) + (有効単語比率×0.3) + (文長スコア×0.2) + (句読点適正度×0.1)
```

#### カバレッジ率算出
```python
target_coverage_rate = (一致単語数 ÷ Target1900総単語数) × 100
extraction_precision = (一致単語数 ÷ 抽出ユニーク単語数) × 100
```

#### 大学名・学部抽出ロジック
`_extract_university_name()` メソッドはファイル名から大学・学部を自動識別。早稲田大学は学部別（法学部、政治経済学部など）に分離して分析。

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
- **カバレッジ率**: 単語帳の何%が入試に出現したか = 一致語数 ÷ 単語帳総語数 × 100
- **抽出精度**: 抽出語の何%が単語帳に含まれるか = 一致語数 ÷ 抽出ユニーク語数 × 100
- **一致語数**: 抽出語と単語帳の重複語数

#### 分析結果の3つのカテゴリ

1. **matched_words**: Target 1900にあり、かつPDFから抽出された単語
   - 学習効果が確認できる重要語彙
   - カバレッジ率の分子となる

2. **unmatched_from_target**: Target 1900にあるが、PDFから抽出されなかった単語
   - 入試問題で出現しなかった Target 1900 語彙
   - 追加学習が必要な可能性がある単語

3. **unmatched_from_extracted**: PDFから抽出されたが、Target 1900にない単語
   - Target 1900 では学習しない高度・専門語彙
   - 抽出精度の分母に含まれるが一致には寄与しない

#### 単語帳選択の目安
- **高カバレッジ率**: その単語帳は入試頻出語を多く含む（実用性高）
- **高抽出精度**: 学習した語彙が入試に出やすい（効率性高）
- **Target 1400**: 通常最高カバレッジ率（36%程度）
- **LEAP**: 通常最高抽出精度（33%程度）

### デバッグ時の確認ポイント

1. **OCR品質**: `ocr_confidence` が 0.95 以上が理想
2. **言語検出**: 日本語混在テキストの適切な除外
3. **Lemmatization**: 語形変化単語の原形化効果
4. **一致率**: Target 1900 カバレッジが 20-30% 程度が標準的

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

#### 新規PDFファイル追加ワークフロー
1. PDFファイルを `PDF/` フォルダに配置（命名規則: `大学名_年度_英語_学部名.pdf`）
2. 英語抽出実行: `python pdf_text_extractor.py`
3. 複数単語帳分析実行: `python vocabulary_analyzer_multi.py`
4. 結果確認: `comprehensive_analysis_summary.md`

### 重要な実装詳細

#### CSVファイルの列名対応
- `target1900.csv` → `'word'` 列
- `target1400.csv` → `'単語'` 列  
- `システム英単語.csv`, `LEAP.csv`, `鉄壁.csv` → `'英語'` 列

#### 大学名自動認識パターン
- 早稲田大学（学部別分析対応）: 法学部、政治経済学部、商学部、文学部、理工学部
- その他認識対象: 東京大学、慶應義塾大学、京都大学、一橋大学、大阪大学、明治大学、立教大学、上智大学、青山学院大学

#### エラー対処
- **BOM問題**: pandas.read_csv で `encoding='utf-8-sig'` 使用必須
- **OpenAI API**: 最新版 1.88.0 以上推奨、GPT-4o-mini モデル使用
- **依存関係エラー**: Poppler と Tesseract のシステムレベルインストール必須