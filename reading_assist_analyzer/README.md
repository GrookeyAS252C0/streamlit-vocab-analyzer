# ReadingAssist Analyzer

英文読解における単語帳有効性と文章構造を総合分析するアプリケーション

## 📋 主要機能

### 🎯 分析機能
1. **単語帳カバレッジ分析**: 複数単語帳との一致率・有効性測定
2. **文法項目分析**: 関係代名詞、仮定法、不定詞等の出現頻度
3. **文章構造分析**: 文長、複文比率、読みやすさ指標
4. **総合読解難易度判定**: 語彙・文法・構造の統合評価

### 📊 対応単語帳
- Target 1900/1400/1200
- システム英単語
- LEAP
- 鉄壁
- その他カスタム単語帳

### 🎨 UI機能
- Streamlit Web インターフェース
- インタラクティブ可視化
- レポート生成・ダウンロード
- リアルタイム分析

## 🚀 クイックスタート

```bash
# 依存関係インストール
pip install -r requirements.txt

# アプリ起動
cd web_app
streamlit run streamlit_app.py
```

## 📁 プロジェクト構造

```
reading_assist_analyzer/
├── core/                    # コア分析エンジン
│   ├── text_analyzer.py     # メイン分析クラス
│   ├── vocab_analyzer.py    # 単語帳分析
│   ├── grammar_analyzer.py  # 文法分析
│   └── sentence_analyzer.py # 文構造分析
├── data/                    # データファイル
│   ├── vocabulary_books/    # 単語帳データ
│   ├── grammar_patterns/    # 文法パターン
│   └── sample_texts/        # サンプル英文
├── utils/                   # ユーティリティ
│   ├── text_preprocessor.py # テキスト前処理
│   ├── nlp_utils.py        # NLP共通機能
│   └── report_generator.py # レポート生成
├── web_app/                # Web インターフェース
│   ├── streamlit_app.py    # メインアプリ
│   ├── components/         # UIコンポーネント
│   └── static/            # 静的ファイル
├── config/                 # 設定ファイル
│   ├── settings.json       # アプリ設定
│   └── grammar_rules.json  # 文法ルール
└── tests/                  # テストコード
```

## 📈 開発ロードマップ

### Phase 1: 基盤構築 (Day 1-2)
- [x] プロジェクト構造作成
- [ ] 既存コードから単語帳分析機能移植
- [ ] 基本設定ファイル作成
- [ ] テストフレームワーク設定

### Phase 2: 新機能実装 (Day 3-4)
- [ ] 文法項目分析エンジン
- [ ] 文章構造分析エンジン
- [ ] 統合分析クラス
- [ ] 評価指標計算

### Phase 3: UI実装 (Day 5-6)
- [ ] Streamlit基本レイアウト
- [ ] ファイルアップロード機能
- [ ] インタラクティブ可視化
- [ ] レポート出力機能

### Phase 4: 統合・テスト (Day 7-8)
- [ ] 全機能統合
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング
- [ ] ユニットテスト

### Phase 5: 仕上げ (Day 9-10)
- [ ] ドキュメント整備
- [ ] サンプルデータ準備
- [ ] デプロイ対応
- [ ] 最終テスト

## 🔧 技術スタック

- **分析エンジン**: Python, NLTK, spaCy
- **Web UI**: Streamlit, Plotly
- **データ処理**: pandas, numpy
- **テスト**: pytest
- **デプロイ**: Streamlit Cloud / Docker

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

Issue報告、機能提案、プルリクエストを歓迎します。

---

**開発状況**: 🚧 開発中（Phase 1）