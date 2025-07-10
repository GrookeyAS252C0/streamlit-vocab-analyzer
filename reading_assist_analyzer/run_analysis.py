#!/usr/bin/env python3
"""
ReadingAssist Analyzer メインエントリーポイント
コマンドライン実行とStreamlitアプリ起動の統合スクリプト
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.text_analyzer import TextAnalyzer
from utils.report_generator import ReportGenerator, ReportConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> dict:
    """設定ファイルの読み込み"""
    config_path = project_root / "config" / "settings.json"
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("設定ファイルが見つかりません。デフォルト設定を使用します。")
            return {}
    except Exception as e:
        logger.error(f"設定ファイル読み込みエラー: {e}")
        return {}

def run_cli_analysis(
    input_text: str, 
    output_path: Optional[str] = None,
    report_format: str = "json",
    vocab_data_path: Optional[str] = None
) -> bool:
    """
    CLIモードでの分析実行
    
    Args:
        input_text: 分析対象テキスト
        output_path: 出力パス
        report_format: レポート形式
        vocab_data_path: 単語帳データパス
        
    Returns:
        実行成功フラグ
    """
    try:
        logger.info("ReadingAssist Analyzer CLI分析を開始します")
        
        # 設定読み込み
        config = load_config()
        
        # 分析エンジン初期化
        analyzer = TextAnalyzer(config.get('analysis', {}))
        
        # 単語帳データパス設定
        if vocab_data_path is None:
            vocab_data_path = str(project_root / "data" / "vocabulary_books")
        
        # 分析実行
        logger.info("分析を実行中...")
        result = analyzer.analyze_text_comprehensive(input_text, vocab_data_path)
        
        # 出力パス設定
        if output_path is None:
            output_path = f"analysis_result_{result['metadata']['analysis_timestamp'].replace(':', '-')}"
        
        # レポート生成
        report_config = ReportConfig(format=report_format)
        report_generator = ReportGenerator(report_config)
        
        success = report_generator.generate_comprehensive_report(result, output_path)
        
        if success:
            logger.info(f"分析完了。結果を '{output_path}' に保存しました。")
            
            # 簡易サマリーの表示
            assessment = result.get('comprehensive_assessment', {})
            print("\\n" + "="*60)
            print("📊 ReadingAssist Analyzer 分析結果サマリー")
            print("="*60)
            print(f"総合難易度: {assessment.get('difficulty_level', '不明')}")
            print(f"読解レベル: {assessment.get('reading_level', '不明')}")
            print(f"推定読解時間: {assessment.get('estimated_reading_time_minutes', 0)}分")
            print(f"総合スコア: {assessment.get('overall_difficulty_score', 0):.1f}")
            
            # 主要な課題表示
            report = result.get('integrated_report', {})
            challenges = report.get('executive_summary', {}).get('key_challenges', [])
            if challenges:
                print("\\n⚠️  主要な学習課題:")
                for i, challenge in enumerate(challenges, 1):
                    print(f"  {i}. {challenge}")
            
            print("="*60)
            
            return True
        else:
            logger.error("レポート生成に失敗しました")
            return False
            
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        return False

def run_streamlit_app():
    """Streamlitアプリの起動"""
    try:
        import subprocess
        import sys
        
        app_path = project_root / "web_app" / "streamlit_app.py"
        
        logger.info("Streamlitアプリを起動します...")
        print("\\n🚀 ReadingAssist Analyzer Web Interface")
        print("ブラウザで http://localhost:8501 にアクセスしてください")
        print("終了する場合は Ctrl+C を押してください\\n")
        
        # Streamlitアプリの起動
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.address", "localhost",
            "--server.port", "8501"
        ])
        
    except KeyboardInterrupt:
        print("\\n\\nアプリを終了しました。")
    except ImportError:
        logger.error("Streamlitがインストールされていません。'pip install streamlit' を実行してください。")
    except Exception as e:
        logger.error(f"Streamlitアプリ起動エラー: {e}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="ReadingAssist Analyzer - 英文読解分析ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # Streamlit Webアプリを起動
  python run_analysis.py

  # CLIモードでテキストファイルを分析
  python run_analysis.py --cli --input sample.txt --output result

  # CLIモードで直接テキストを分析
  python run_analysis.py --cli --text "Your English text here"

  # HTMLレポートを生成
  python run_analysis.py --cli --input sample.txt --format html
        """
    )
    
    parser.add_argument(
        '--cli', 
        action='store_true',
        help='CLIモードで実行'
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='入力ファイルパス'
    )
    
    parser.add_argument(
        '--text', '-t',
        type=str,
        help='直接入力するテキスト'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='出力ファイルパス（拡張子なし）'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['json', 'html', 'csv', 'txt'],
        default='json',
        help='レポート形式 (デフォルト: json)'
    )
    
    parser.add_argument(
        '--vocab-path',
        type=str,
        help='単語帳データディレクトリパス'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='ReadingAssist Analyzer v1.0.0'
    )
    
    args = parser.parse_args()
    
    # CLIモードの場合
    if args.cli:
        # 入力テキストの取得
        input_text = ""
        
        if args.text:
            input_text = args.text
        elif args.input:
            try:
                input_path = Path(args.input)
                if not input_path.exists():
                    print(f"エラー: ファイル '{args.input}' が見つかりません")
                    return 1
                
                with open(input_path, 'r', encoding='utf-8') as f:
                    input_text = f.read()
                    
            except Exception as e:
                print(f"ファイル読み込みエラー: {e}")
                return 1
        else:
            print("エラー: --input または --text オプションが必要です")
            parser.print_help()
            return 1
        
        # テキスト検証
        if not input_text.strip():
            print("エラー: 入力テキストが空です")
            return 1
        
        if len(input_text.strip()) < 50:
            print("警告: 入力テキストが短すぎる可能性があります（50文字未満）")
        
        # 分析実行
        success = run_cli_analysis(
            input_text=input_text,
            output_path=args.output,
            report_format=args.format,
            vocab_data_path=args.vocab_path
        )
        
        return 0 if success else 1
    
    else:
        # Streamlitアプリモード（デフォルト）
        run_streamlit_app()
        return 0

if __name__ == "__main__":
    sys.exit(main())