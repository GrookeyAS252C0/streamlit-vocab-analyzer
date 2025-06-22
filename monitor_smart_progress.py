#!/usr/bin/env python3
"""
スマートOCR処理進捗監視
改良版進捗表示とリアルタイム監視
"""

import os
import json
import time
from datetime import datetime, timedelta
import sys

def clear_screen():
    """画面クリア"""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_duration(seconds):
    """秒数を時分秒形式に変換"""
    return str(timedelta(seconds=int(seconds)))

def read_smart_progress():
    """スマート進捗情報読み取り"""
    try:
        if os.path.exists("smart_progress.json"):
            with open("smart_progress.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception:
        return None

def read_log_tail(log_file="smart_processing.log", lines=8):
    """ログファイルの末尾読み取り"""
    try:
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if all_lines else []
        return []
    except Exception:
        return []

def display_progress_bar(percentage, width=50):
    """プログレスバー表示"""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage}%"

def check_completion_status():
    """完了状況確認"""
    completion_files = [
        "processing_completion_summary.json",
        "extraction_results_pure_english.json",
        "multi_vocabulary_analysis_report.json"
    ]
    
    completed = all(os.path.exists(f) for f in completion_files)
    
    if completed and os.path.exists("processing_completion_summary.json"):
        try:
            with open("processing_completion_summary.json", "r", encoding="utf-8") as f:
                summary = json.load(f)
            return True, summary
        except:
            return False, None
    
    return False, None

def display_main_monitor():
    """メイン監視画面"""
    print("🔍 スマートOCR処理監視")
    print("=" * 70)
    print("Ctrl+C で監視終了")
    print("=" * 70)
    
    try:
        while True:
            clear_screen()
            
            # ヘッダー
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"🔍 スマートOCR処理監視 - {current_time}")
            print("=" * 70)
            
            # 完了状況確認
            is_completed, completion_summary = check_completion_status()
            
            if is_completed:
                print("🎉 処理完了!")
                print("-" * 70)
                print(f"📅 完了時刻: {completion_summary['completion_time'][:19]}")
                print(f"⏱️  処理時間: {completion_summary['duration']}")
                print(f"📁 PDFファイル数: {completion_summary['pdf_count']}")
                print(f"🔧 処理モード: {completion_summary['mode']}")
                print()
                
                # 生成ファイル確認
                print("📊 生成ファイル:")
                for file_name, info in completion_summary.get('generated_files', {}).items():
                    if info.get('exists', False):
                        size_mb = info.get('size_mb', 0)
                        print(f"   ✅ {file_name} ({size_mb}MB)")
                    else:
                        print(f"   ❌ {file_name} (未生成)")
                
                print("\n🎊 すべての処理が完了しました!")
                break
            
            # 進捗情報読み取り
            progress = read_smart_progress()
            
            if progress:
                # 開始時刻と経過時間
                start_time = datetime.fromisoformat(progress["start_time"])
                elapsed = datetime.now() - start_time
                
                print(f"📅 開始時刻: {start_time.strftime('%H:%M:%S')}")
                print(f"⏱️  経過時間: {format_duration(elapsed.total_seconds())}")
                print(f"🔧 処理モード: {'クリーン' if progress.get('force_clean', False) else 'スマート'}")
                print()
                
                # 進捗バー
                percentage = progress["percentage"]
                print(f"📊 進捗: {progress['current_step']}/{progress['total_steps']}")
                print(f"     {display_progress_bar(percentage)}")
                print()
                
                # 現在のタスク
                current_task = progress.get("current_task", "")
                details = progress.get("details", "")
                
                if current_task:
                    print(f"🔄 現在のタスク: {current_task}")
                    if details:
                        print(f"📋 詳細: {details}")
                    print()
                
                # 予想残り時間
                if percentage > 5:  # 5%以上進捗があれば予想時間表示
                    estimated_total = elapsed.total_seconds() * 100 / percentage
                    remaining = estimated_total - elapsed.total_seconds()
                    if remaining > 0:
                        print(f"⏳ 予想残り時間: {format_duration(remaining)}")
                        estimated_completion = datetime.now() + timedelta(seconds=remaining)
                        print(f"🏁 予想完了時刻: {estimated_completion.strftime('%H:%M:%S')}")
                        print()
            
            else:
                print("❓ 進捗情報が見つかりません")
                
                # バックグラウンドプロセス確認
                import subprocess
                try:
                    result = subprocess.run(
                        ["ps", "aux"], 
                        capture_output=True, 
                        text=True
                    )
                    if "smart_ocr_processor" in result.stdout:
                        print("🔄 バックグラウンドプロセス実行中...")
                    else:
                        print("❌ バックグラウンドプロセスが見つかりません")
                except:
                    pass
                
                print()
            
            # 最新ログ
            print("📋 最新ログ:")
            print("-" * 70)
            log_lines = read_log_tail()
            if log_lines:
                for line in log_lines[-6:]:  # 最新6行
                    # ログレベルに応じて色分け（簡易版）
                    line = line.strip()
                    if "ERROR" in line:
                        print(f"❌ {line}")
                    elif "WARNING" in line:
                        print(f"⚠️  {line}")
                    elif "✅" in line or "🎉" in line:
                        print(f"✅ {line}")
                    else:
                        print(f"   {line}")
            else:
                print("   ログなし")
            
            print("-" * 70)
            print("Ctrl+C で監視終了 | 2秒ごと自動更新")
            
            time.sleep(2)  # 2秒ごとに更新
            
    except KeyboardInterrupt:
        print("\n\n👋 監視を終了しました")
    except Exception as e:
        print(f"\n❌ 監視エラー: {e}")

def main():
    """メイン関数"""
    display_main_monitor()

if __name__ == "__main__":
    main()