# 🚀 GitHub & Streamlit Cloud デプロイ手順

## ✅ 現在の状態
- ✅ ローカルGitリポジトリ初期化済み
- ✅ 全ファイル追加・コミット完了
- ✅ ブランチ名を `main` に設定済み
- ✅ Streamlitアプリ動作確認済み

## 📋 次の手順

### 1️⃣ GitHubリポジトリ作成

1. **GitHub にアクセス**: https://github.com
2. **新しいリポジトリ作成**:
   - 右上の「+」→「New repository」
   - **Repository name**: `streamlit-vocab-analyzer`
   - **Description**: `大学入試英単語分析ダッシュボード - University entrance exam vocabulary analyzer`
   - **Visibility**: `Public` に設定
   - **Initialize**: チェックボックスは全て**空のまま**
   - 「Create repository」をクリック

### 2️⃣ リモートリポジトリ接続

GitHubリポジトリ作成後、以下のコマンドを実行：

```bash
# 現在のディレクトリ確認
pwd
# /Users/takashikemmoku/Desktop/wordsearch/streamlit-vocab-analyzer

# リモートリポジトリ追加（[あなたのユーザー名]を実際のユーザー名に変更）
git remote add origin https://github.com/[あなたのユーザー名]/streamlit-vocab-analyzer.git

# プッシュ
git push -u origin main
```

### 3️⃣ Streamlit Cloud デプロイ

1. **Streamlit Cloud アクセス**: https://share.streamlit.io
2. **ログイン**: GitHubアカウントでログイン
3. **新しいアプリ作成**:
   - 「New app」をクリック
   - **Repository**: `[あなたのユーザー名]/streamlit-vocab-analyzer`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - 「Deploy!」をクリック

### 4️⃣ 自動デプロイ確認

- GitHubにpushするたびに自動的にStreamlit Cloudが更新されます
- 数分でデプロイが完了し、公開URLが発行されます

## 🎯 完成後の機能

### 📊 ダッシュボード機能
- 全体サマリー統計
- 単語帳別比較チャート
- 大学×単語帳ヒートマップ
- OCR信頼度ゲージ
- 最頻出単語ランキング

### 🏫 大学別分析
- 個別大学の詳細データ
- 単語帳別パフォーマンス
- インタラクティブな比較

### ⚖️ 比較分析
- 複数大学レーダーチャート
- ランキング表示
- カスタムフィルタリング

## 📊 現在のデータセット
- **大学数**: 3校
- **単語帳数**: 5種
- **総単語数**: 2,353語
- **OCR信頼度**: 96.0%

## 🔄 データ更新ワークフロー

新しい過去問追加時：
1. ローカルでOCR処理実行
2. `data/analysis_data.json` 更新
3. GitHubにpush
4. Streamlit Cloud自動更新

---

**🎉 準備完了！上記の手順に従ってデプロイしてください。**