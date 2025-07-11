# 大学入試英単語分析ダッシュボード

このStreamlitアプリケーションは、`extraction_results_pure_english.json`ファイルから英語語彙を読み込み、複数の単語帳と比較分析するWebダッシュボードです。

## 主な機能

- **JSONファイルアップロード**: `extraction_results_pure_english.json`形式のファイルをアップロード（複数ファイル対応）
- **自動ファイル統合**: 複数のJSONファイルを自動的に統合して一括分析
- **語彙分析**: 5つの単語帳（Target 1900/1400、システム英単語、LEAP、鉄壁）との比較
- **可視化**: カバレッジ率、抽出精度のインタラクティブチャート
- **大学比較**: 複数大学・学部間のパフォーマンス比較

## セットアップ

```bash
# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
streamlit run streamlit_app.py
```

## 使用方法

1. ブラウザでアプリにアクセス
2. `extraction_results_pure_english.json`ファイルをアップロード（複数ファイル選択可能）
3. アップロードされたファイル一覧を確認
4. 「語彙分析を実行」ボタンをクリック
5. 左サイドバーで分析対象大学・学部を選択
6. 各タブ（概要分析、大学別詳細、比較分析）で結果を確認

### 複数ファイルアップロード
- ファイル選択時にCtrl+クリック（Windowsの場合）またはCmd+クリック（Macの場合）で複数ファイルを選択
- アップロードされたファイルは自動的に統合され、一括で分析されます

## 必要なデータ形式

アップロードするJSONファイルは以下の構造が必要です：

```json
{
  "extraction_summary": {
    "total_source_files": 2,
    "total_words_extracted": 1000
  },
  "extracted_data": [
    {
      "source_file": "大学名_年度_英語_学部名.pdf",
      "pages_processed": 3,
      "extracted_words": ["word1", "word2", "word3", ...]
    }
  ]
}
```

## 単語帳データ

アプリは以下の5つの単語帳データを内蔵しています：
- **Target 1900**: 大学受験用の重要単語集
- **Target 1400**: 基礎レベルの単語集
- **システム英単語**: システマティックな語彙学習用
- **LEAP**: 大学受験・TOEIC対応
- **鉄壁**: 難関大学受験用

単語帳データは `vocab_data.py` に組み込まれており、外部ファイルは不要です。

## 指標の説明

- **カバレッジ率**: 単語帳の何%の語彙が入試問題に出現したか
- **抽出精度**: 抽出した語彙の何%が単語帳に含まれるか
- **一致語数**: 実際に一致した語彙の数

## 技術スタック

- **Streamlit**: Webアプリケーションフレームワーク
- **Plotly**: インタラクティブ可視化
- **Pandas**: データ処理・分析
- **NLTK**: 自然言語処理

## ライセンス

MIT License