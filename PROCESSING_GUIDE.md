# 📋 新規PDF処理ガイド

## 🎯 現在の状況（2025-06-21 20:21）

### 📊 処理進捗
- **処理対象**: 11ファイル（早稲田10学部 + 東京大学）
- **現在進捗**: 27.3%（3/11ファイル完了）
- **推定残り時間**: 約30分

### ✅ 処理完了ファイル
1. 早稲田大学_法学部（823語、96.7%信頼度）
2. 早稲田大学_政治経済学部（715語、95.2%信頼度）
3. 東京大学（815語、96.0%信頼度）

## 🔄 処理手順

### ステップ1: PDF英語抽出（実行中）
```bash
python pdf_text_extractor.py
```
**状況**: 現在実行中（バックグラウンド）

### ステップ2: 進捗確認
```bash
python check_progress.py
```

### ステップ3: 処理完了後の分析実行
```bash
# 全PDFの処理完了を確認後
python vocabulary_analyzer_multi.py
python utils/data_processor.py
```

### ステップ4: Streamlit Cloud更新
```bash
cd streamlit-vocab-analyzer
cp ../streamlit-vocab-analyzer/data/*.json data/
git add data/
git commit -m "Update analysis with 11 universities (Waseda 10 faculties + Tokyo Univ)"
git push origin main
```

## ⏱️ 処理時間の目安

### OCR + LLM校正
- **1ページあたり**: 約40秒
- **1ファイルあたり**: 約4-6分（6-8ページ）
- **全11ファイル**: 約50-60分

### 語彙分析
- **分析実行**: 約2-3分
- **データ変換**: 約30秒

## 📊 期待される最終結果

### データセット拡大
- **大学数**: 1校 → 2校
- **学部数**: 3学部 → 11学部
- **総単語数**: 2,353語 → 推定8,000-10,000語
- **分析精度**: 大幅向上

### 新たな洞察
- 早稲田大学学部別特徴分析
- 理系・文系学部の語彙傾向
- より正確な単語帳適合度評価

## 🚨 注意事項

### 処理中の注意
- OCR処理中はPCのリソース使用量が高い
- OpenAI API使用料金が発生（推定$5-10）
- ネットワーク接続必須

### エラー対処
- プロセス停止時: `python pdf_text_extractor.py` で再開
- API エラー: `.env` ファイルのAPIキー確認
- メモリ不足: 他のアプリケーション終了

## 🎉 完了後の確認項目

### データ品質
- OCR平均信頼度 95%以上
- 総単語数の妥当性
- 学部別データの存在

### Streamlit更新
- ダッシュボードの新学部表示
- 比較分析の精度向上
- レーダーチャートの詳細化

---

**📞 サポート**: 問題が発生した場合は `python check_progress.py` で状況確認