# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このStreamlitダッシュボードは、`extraction_results_pure_english.json`ファイルから英語単語を読み込み、5つの単語帳（Target 1900/1400、システム英単語、LEAP、鉄壁）と比較分析するWebアプリケーションです。

**重要**: このダッシュボードはファイルアップロード機能により、OCR処理システムとは独立して動作します。アップロードされたJSONデータをリアルタイムで分析し、結果を表示します。

## 主要なコマンド

### ローカル開発
```bash
# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
streamlit run streamlit_app.py

# デバッグモードで起動
streamlit run streamlit_app.py --logger.level=debug
```

### データ更新ワークフロー
```bash
# 1. 親ディレクトリで分析実行（重い処理）
cd ../
python incremental_processor.py  # 新PDFファイル自動検出・処理
# または手動実行:
python pdf_text_extractor.py && python vocabulary_analyzer_multi.py

# 2. Streamlit用データ生成
cd streamlit-vocab-analyzer
python utils/data_processor.py

# 3. GitHubにプッシュ（自動デプロイ）
git add data/analysis_data.json
git commit -m "Update analysis data"
git push origin main
```

### 新規大学・学部追加時の重要手順
```bash
# 1. utils/data_processor.py の extract_university_name() 関数を更新
# 2. 新大学の学部認識パターンを追加
# 3. データ再生成とプッシュ
python utils/data_processor.py
git add utils/data_processor.py data/analysis_data.json
git commit -m "Add new university support"
git push origin main
```

### テストとデバッグ用コマンド
```bash
# カバレッジ率計算のデバッグ
python debug_coverage_calculation.py

# 最適単語帳機能テスト
python test_optimal_vocabulary.py

# データの整合性確認
python final_data_test.py

# キャッシュクリア付きでアプリ起動
streamlit run streamlit_app.py --server.enableCORS=false --server.enableXsrfProtection=false
```

### Streamlit Cloud デプロイ
- リポジトリ: https://github.com/GrookeyAS252C0/streamlit-vocab-analyzer.git
- メインファイル: `streamlit_app.py`
- ブランチ: `main`
- 自動デプロイ: GitHubプッシュで自動更新

## アーキテクチャ

### コアコンポーネント

1. **streamlit_app.py** - メインアプリケーション
   - 3つのページ構成：概要ダッシュボード、大学別詳細、比較分析
   - サイドバーでのフィルタリング機能
   - セッション状態によるページ管理

2. **utils/data_loader.py** - データ読み込みユーティリティ
   - `@st.cache_data` でのパフォーマンス最適化
   - 大学・単語帳リスト取得関数
   - DataFrame変換とサマリー統計計算

3. **utils/visualizations.py** - 可視化ユーティリティ
   - Plotlyベースのインタラクティブチャート
   - レーダーチャート、ヒートマップ、散布図、ゲージチャート
   - 大学比較用の複合可視化

4. **utils/data_processor.py** - データ前処理システム
   - 親ディレクトリの分析結果をStreamlit用に軽量化
   - `estimate_department_vocabulary_coverage()` - 学部レベル推定機能
   - `create_university_consolidated_data()` - 大学統合データ生成
   - `extract_university_name()` - ファイル名からの大学・学部抽出

### データ構造

#### data/analysis_data.json（重要）
```json
{
  "metadata": { "生成時刻、バージョン情報" },
  "overall_summary": { "全体統計（21大学・学部 + 2統合）" },
  "vocabulary_summary": { "5単語帳の総合カバレッジ率" },
  "university_analysis": { 
    "早稲田大学_法学部": { "個別学部データ" },
    "慶應義塾大学_医学部": { "個別学部データ" },
    "東京大学": { "単一大学データ" },
    "早稲田大学（全学部）": { "統合データ" },
    "慶應義塾大学（全学部）": { "統合データ" },
    // ... 全23エントリ（21学部別 + 2統合）
  },
  "top_frequent_words": { "頻出単語ランキング" }
}
```

**現在サポート大学**: 早稲田大学（10学部）、慶應義塾大学（10学部）、東京大学（1エントリ）

#### data/university_metadata.json
- 大学・単語帳の追加情報（色設定、カテゴリ分類など）
- 現在は基本的な構造のみ

### ページ構成

1. **概要ダッシュボード** (`show_overview_page`)
   - 全体サマリーメトリクス
   - 単語帳別比較棒グラフ
   - カバレッジ率 vs 抽出精度散布図
   - 大学×単語帳ヒートマップ
   - 最頻出単語・OCR信頼度ゲージ

2. **大学別詳細** (`show_university_page`)
   - 個別大学の詳細統計
   - 単語帳別パフォーマンステーブル
   - 学部内での単語帳比較チャート

3. **比較分析** (`show_comparison_page`)
   - 複数大学のレーダーチャート比較
   - 詳細パフォーマンステーブル
   - カスタムランキング（カバレッジ率、OCR信頼度等）

### 重要な実装詳細

#### キャッシング戦略
- `@st.cache_data` でデータ読み込みをキャッシュ
- セッション状態でページ選択とフィルター設定を保持
- 大きなデータセットは事前に軽量化してから配信

#### 大学名の一貫性とフィルタリング
- `university_analysis` キーは「大学名_学部名」形式または「大学名（全学部）」
- 例：`早稲田大学_法学部`、`慶應義塾大学_医学部`、`早稲田大学（全学部）`、`東京大学`
- 階層フィルター: 「大学レベル」「学部レベル」「混合選択」の3モード
- `utils/data_processor.py` の `extract_university_name()` 関数で新大学を追加可能

#### 動的最適単語帳選択システム
- `get_optimal_vocabulary_for_selection()` 関数で選択大学に応じた最適単語帳を動的計算
- 重み付きスコア: カバレッジ率70% + 抽出精度30%
- 単語数による重み付け平均で複数大学の統合計算
- 学部レベル推定: `estimate_department_vocabulary_coverage()` で大学データから学部データを推定

#### データ重複とカバレッジ率計算の問題解決
- 複数の慶應学部選択時に同一データによる重複を防ぐため比例配分システムを実装
- 学部固有の語彙特性を反映する調整係数（カバレッジ70-100%、精度80-120%）
- 重み付き平均計算で適切なカバレッジ率を維持

#### エラーハンドリング
- データファイル不在時の適切なエラーメッセージ
- matplotlib依存のスタイリングでのフォールバック対応
- KeyError対策でのcolumn名マッピング

### データの流れ

```
親ディレクトリでの重い処理:
PDF files → OCR extraction → Vocabulary analysis → multi_vocabulary_analysis_report.json

Streamlit用軽量化:
multi_vocabulary_analysis_report.json → utils/data_processor.py → data/analysis_data.json

ダッシュボード表示:
data/analysis_data.json → utils/data_loader.py → streamlit_app.py → 可視化
```

### カスタマイズポイント

#### 新しい大学・学部の追加
1. 親ディレクトリでPDF処理・分析実行
2. `utils/data_processor.py` が自動的に新しいエントリを検出
3. `data/analysis_data.json` が更新される
4. GitHubプッシュで自動反映

#### 新しい単語帳の追加
1. 親ディレクトリの分析スクリプトで単語帳追加
2. `vocabulary_summary` と各大学の `vocabulary_coverage` が自動更新
3. 可視化コードは動的に対応（色設定のみ要調整）

#### 色とスタイル
- `utils/visualizations.py` のcolor配列で各チャートの色設定
- `streamlit_app.py` のカスタムCSSでUI調整
- university_metadata.jsonで大学・単語帳固有の色設定可能

### トラブルシューティング

#### よくある問題
1. **大学データが表示されない**: `data/analysis_data.json` の `university_analysis` キーを確認
2. **チャートエラー**: matplotlib依存部分のフォールバック確認
3. **データ更新されない**: Streamlit Cloudのキャッシュクリア、または `@st.cache_data` のttl設定
4. **複数大学選択時のカバレッジ率異常**: 学部レベル推定機能が正常動作しているか確認
5. **最適単語帳が更新されない**: `get_optimal_vocabulary_for_selection()` 関数の動作確認

#### デバッグ手法
- `st.write(data.keys())` でデータ構造確認
- `st.json(data['university_analysis'])` で大学データ詳細表示
- `streamlit run streamlit_app.py --logger.level=debug` でログ出力

### パフォーマンス最適化

- 大きなデータは親ディレクトリで事前処理し、軽量化したJSONを配信
- `@st.cache_data` で読み込み処理をキャッシュ（デフォルト1時間）
- 複雑な計算は事前に実行し、結果のみをJSONに保存
- Plotlyチャートは必要最小限のデータ点で描画

### デプロイメント

- **本番環境**: Streamlit Cloud（https://github.com/GrookeyAS252C0/streamlit-vocab-analyzer.git）
- **更新頻度**: 新しい分析結果があるときのみ手動プッシュ
- **ダウンタイム**: GitHubプッシュ後1-2分の自動デプロイ時間
- **モニタリング**: Streamlit Cloud管理画面でアプリ状態確認可能