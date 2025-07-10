# ReadingAssist Analyzer デプロイメントガイド

## 📋 目次

1. [ローカル環境セットアップ](#ローカル環境セットアップ)
2. [依存関係のインストール](#依存関係のインストール)
3. [設定ファイルの準備](#設定ファイルの準備)
4. [単語帳データの配置](#単語帳データの配置)
5. [アプリケーションの起動](#アプリケーションの起動)
6. [Streamlit Cloudデプロイ](#streamlit-cloudデプロイ)
7. [Dockerデプロイ](#dockerデプロイ)
8. [トラブルシューティング](#トラブルシューティング)

## 🚀 ローカル環境セットアップ

### 前提条件
- Python 3.8 以上
- pip (Python パッケージマネージャー)
- 4GB 以上のRAM

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd reading_assist_analyzer
```

### 2. 仮想環境の作成（推奨）

```bash
# 仮想環境作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\\Scripts\\activate

# macOS/Linux
source venv/bin/activate
```

## 📦 依存関係のインストール

### 基本依存関係のインストール

```bash
pip install -r requirements.txt
```

### NLTKデータのダウンロード

初回実行時に自動でダウンロードされますが、手動で実行することも可能です：

```bash
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
"
```

### オプション: spaCyモデルのインストール

より高度な自然言語処理機能を使用する場合：

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

## ⚙️ 設定ファイルの準備

### 基本設定の確認

`config/settings.json` ファイルが存在することを確認してください。存在しない場合、アプリケーションは基本設定で動作します。

### カスタム設定例

```json
{
  "analysis": {
    "vocabulary": {
      "lemmatization": true,
      "remove_stopwords": true,
      "min_word_length": 2
    },
    "grammar": {
      "enable_pos_tagging": true,
      "min_sentence_length": 3
    }
  },
  "ui": {
    "max_file_size_mb": 10,
    "supported_formats": [".txt", ".json", ".csv"]
  }
}
```

## 📚 単語帳データの配置

### 必要な単語帳ファイル

`data/vocabulary_books/` ディレクトリに以下のCSVファイルを配置してください：

```
data/vocabulary_books/
├── target1900.csv      (必須: 'word' 列)
├── target1400.csv      (必須: '単語' 列)
├── target1200.csv      (必須: '単語' 列)
├── システム英単語.csv   (必須: '英語' 列)
├── LEAP.csv           (必須: '英語' 列)
└── 鉄壁.csv           (必須: '英語' 列)
```

### CSVファイル形式

- エンコーディング: UTF-8 with BOM (`utf-8-sig`)
- ヘッダー行必須
- 各ファイルに対応する列名が必要

### サンプルデータファイル

単語帳データがない場合でも、サンプルテキストで動作確認が可能です：

```
data/sample_texts/
├── sample_academic.txt
├── sample_news.txt
└── sample_fiction.txt
```

## 🚀 アプリケーションの起動

### 方法1: Streamlit Webアプリ（推奨）

```bash
# メインスクリプトから起動
python run_analysis.py

# または直接Streamlitアプリを起動
cd web_app
streamlit run streamlit_app.py
```

ブラウザで `http://localhost:8501` にアクセス

### 方法2: コマンドライン（CLI）

```bash
# テキストファイルの分析
python run_analysis.py --cli --input sample.txt --output result

# 直接テキスト入力
python run_analysis.py --cli --text "Your English text here"

# HTMLレポート生成
python run_analysis.py --cli --input sample.txt --format html
```

### 方法3: 個別モジュールのテスト

```bash
# 語彙分析のみ
python core/vocab_analyzer.py

# 文法分析のみ
python core/grammar_analyzer.py

# 統合分析
python core/text_analyzer.py
```

## ☁️ Streamlit Cloudデプロイ

### 1. GitHubリポジトリの準備

```bash
# プロジェクトをGitHubにプッシュ
git add .
git commit -m "Initial ReadingAssist Analyzer setup"
git push origin main
```

### 2. Streamlit Cloudでデプロイ

1. [share.streamlit.io](https://share.streamlit.io) にアクセス
2. GitHubアカウントでログイン
3. "New app" をクリック
4. リポジトリを選択
5. メインファイルパスを設定: `web_app/streamlit_app.py`
6. "Deploy" をクリック

### 3. 環境変数の設定（必要に応じて）

Streamlit Cloudの「Advanced settings」で環境変数を設定：

```
PYTHONPATH=/mount/src/reading_assist_analyzer
```

## 🐳 Dockerデプロイ

### Dockerfileの作成

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルのコピー
COPY . .

# NLTKデータのダウンロード
RUN python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
"

# ポート設定
EXPOSE 8501

# ヘルスチェック
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# アプリケーション起動
CMD ["streamlit", "run", "web_app/streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

### Docker Composeの設定

```yaml
version: '3.8'

services:
  reading-assist:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
```

### デプロイコマンド

```bash
# Dockerイメージのビルド
docker build -t reading-assist-analyzer .

# コンテナの起動
docker run -p 8501:8501 reading-assist-analyzer

# または Docker Composeを使用
docker-compose up -d
```

## 🛠️ トラブルシューティング

### 一般的な問題と解決方法

#### 1. NLTK データエラー

```bash
# エラー: [Errno 2] No such file or directory: 'punkt'
python -c "import nltk; nltk.download('punkt')"
```

#### 2. 単語帳ファイルが見つからない

```bash
# データディレクトリの確認
ls -la data/vocabulary_books/

# ファイル形式の確認
file data/vocabulary_books/target1900.csv
```

#### 3. Streamlitアプリが起動しない

```bash
# ポート競合の確認
netstat -tulpn | grep :8501

# 別ポートで起動
streamlit run web_app/streamlit_app.py --server.port 8502
```

#### 4. メモリ不足エラー

```bash
# 軽量版の設定を使用
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50
export STREAMLIT_SERVER_MAX_MESSAGE_SIZE=50
```

#### 5. 文字エンコーディングエラー

```bash
# ファイルエンコーディングの確認
file -bi data/vocabulary_books/target1900.csv

# UTF-8 with BOMに変換
iconv -f UTF-8 -t UTF-8-BOM input.csv > output.csv
```

### ログファイルの確認

```bash
# アプリケーションログ
tail -f ~/.streamlit/logs/streamlit.log

# Pythonログ
python run_analysis.py --cli --text "test" 2>&1 | tee analysis.log
```

### パフォーマンス最適化

#### メモリ使用量の削減

```python
# config/settings.json
{
  "performance": {
    "cache_enabled": true,
    "max_text_length": 10000,
    "parallel_processing": false
  }
}
```

#### 処理速度の向上

```bash
# 並列処理の有効化（十分なメモリがある場合）
export NUMBA_NUM_THREADS=4
```

## 📊 監視とメンテナンス

### ヘルスチェック

```bash
# アプリケーションの状態確認
curl http://localhost:8501/_stcore/health
```

### ログ監視

```bash
# リアルタイムログ監視
tail -f logs/application.log | grep ERROR
```

### バックアップ

```bash
# 設定とデータのバックアップ
tar -czf backup_$(date +%Y%m%d).tar.gz config/ data/
```

## 🔄 アップデート手順

### 1. コードの更新

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### 2. 設定の確認

```bash
# 設定ファイルの差分確認
diff config/settings.json config/settings.json.new
```

### 3. アプリケーションの再起動

```bash
# Streamlitアプリの再起動
pkill -f streamlit
python run_analysis.py
```

---

## 📞 サポート

問題が解決しない場合：

1. [GitHub Issues](https://github.com/your-repo/issues) で報告
2. ログファイルを添付
3. 環境情報（OS、Python版）を記載

**環境情報の取得:**

```bash
python --version
pip list | grep -E "(streamlit|nltk|pandas)"
uname -a  # Linux/macOS
```