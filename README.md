# 📚 大学入試英単語分析ダッシュボード

OCR処理・LLM校正で抽出した大学入試問題の英単語を、複数の単語帳と比較分析するStreamlitダッシュボードです。

## 🎯 機能

### 📊 概要ダッシュボード
- 全体サマリー統計（総単語数、OCR信頼度、最適単語帳）
- 単語帳別カバレッジ率・抽出精度比較
- 大学×単語帳ヒートマップ
- 最頻出単語ランキング
- OCR信頼度ゲージ

### 🏫 大学別詳細分析
- 個別大学・学部の詳細データ
- 単語帳別パフォーマンス比較
- スタイル付きデータテーブル
- 棒グラフによる可視化

### ⚖️ 比較分析
- 複数大学のレーダーチャート比較
- 詳細パフォーマンステーブル
- カスタムランキング表示

## 🚀 ローカル実行

### 環境セットアップ
```bash
cd streamlit-vocab-analyzer
pip install -r requirements.txt
```

### アプリ起動
```bash
streamlit run streamlit_app.py
```

ブラウザで `http://localhost:8501` にアクセス

## ☁️ Streamlit Cloud デプロイ

### 1. GitHub リポジトリ作成
```bash
# 新しいGitHubリポジトリを作成し、このフォルダをpush
git init
git add .
git commit -m "Initial commit: Streamlit vocab analyzer"
git remote add origin https://github.com/yourusername/streamlit-vocab-analyzer.git
git push -u origin main
```

### 2. Streamlit Cloud デプロイ
1. [share.streamlit.io](https://share.streamlit.io) にアクセス
2. GitHubアカウントでログイン
3. "New app" をクリック
4. リポジトリ、ブランチ、メインファイル（`streamlit_app.py`）を指定
5. "Deploy!" をクリック

### 3. 自動デプロイ設定
- GitHubにpushするたびに自動的にStreamlit Cloudが更新されます
- 新しい分析結果は `data/analysis_data.json` を更新してpushするだけで反映

## 📂 ファイル構造

```
streamlit-vocab-analyzer/
├── streamlit_app.py           # メインアプリケーション
├── requirements.txt           # 依存関係
├── README.md                  # このファイル
├── data/
│   ├── analysis_data.json     # 分析結果データ（軽量化済み）
│   └── university_metadata.json # 大学・単語帳メタデータ
└── utils/
    ├── data_loader.py         # データ読み込みユーティリティ
    └── visualizations.py     # 可視化関数
```

## 🔄 データ更新ワークフロー

### ローカル処理（重い処理）
```bash
# 新しいPDFファイルを追加後
cd /path/to/wordsearch
python pdf_text_extractor.py
python vocabulary_analyzer_multi.py

# Streamlit用データ生成
python utils/data_processor.py
```

### クラウド更新（軽い処理）
```bash
# 生成されたデータをStreamlitリポジトリにコピー
cp streamlit-vocab-analyzer/data/*.json /path/to/streamlit-repo/data/

# GitHubにpush
cd /path/to/streamlit-repo
git add data/
git commit -m "Update analysis data"
git push origin main
```

→ Streamlit Cloudが自動的に更新

## 📊 データ形式

### analysis_data.json
```json
{
  "metadata": { "生成情報" },
  "overall_summary": { "全体統計" },
  "vocabulary_summary": { "単語帳別データ" },
  "university_analysis": { "大学別データ" },
  "top_frequent_words": { "頻出単語" }
}
```

### university_metadata.json
```json
{
  "universities": { "大学情報" },
  "vocabulary_books": { "単語帳情報" }
}
```

## 🎨 カスタマイズ

### 色設定
- `utils/visualizations.py` で各チャートの色を変更可能
- `university_metadata.json` で大学・単語帳の色を設定

### 新しい指標追加
- `utils/data_loader.py` でデータ処理関数を追加
- `streamlit_app.py` で表示ロジックを実装

## 🔧 トラブルシューティング

### よくある問題
1. **データファイルが見つからない**: `data/` フォルダの存在確認
2. **チャートが表示されない**: Plotlyのバージョン確認
3. **パフォーマンス低下**: データキャッシュの確認

### ログ確認
```bash
streamlit run streamlit_app.py --logger.level=debug
```

## 📈 パフォーマンス最適化

- データ読み込みに `@st.cache_data` を使用
- 大きなデータセットは事前に軽量化
- 不要な再計算を避けるためセッション状態を活用

## 🤝 貢献

1. Fork this repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 ライセンス

MIT License - 詳細は LICENSE ファイルを参照

---

**🔗 関連リンク**
- [Streamlit Documentation](https://docs.streamlit.io)
- [Plotly Documentation](https://plotly.com/python/)
- [元の分析システム](../README.md)