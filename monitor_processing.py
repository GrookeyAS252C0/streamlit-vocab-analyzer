#!/usr/bin/env python3
"""
PDF処理の進行状況を監視するスクリプト
"""

import time
import os
import json
from datetime import datetime
import sys

def monitor_processing():
    """PDF処理進行状況をリアルタイム監視"""
    
    print("🔄 PDF処理監視開始")
    print("=" * 60)
    
    last_progress = 0
    start_time = datetime.now()
    
    try:
        while True:
            # 進捗確認
            if os.path.exists("extraction_results_pure_english.json"):
                with open("extraction_results_pure_english.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                current_progress = len(data.get('extracted_data', []))
                total_files = 11  # 全体のファイル数
                
                # 進捗が更新された場合
                if current_progress > last_progress:
                    elapsed = datetime.now() - start_time
                    eta = elapsed / current_progress * (total_files - current_progress) if current_progress > 0 else None
                    
                    print(f"\n🎯 [{datetime.now().strftime('%H:%M:%S')}] 進捗更新:")
                    print(f"   処理完了: {current_progress}/{total_files} ({current_progress/total_files*100:.1f}%)")
                    print(f"   経過時間: {elapsed}")
                    if eta:
                        print(f"   推定残り時間: {eta}")
                    
                    last_progress = current_progress
                
                # 完了チェック
                if current_progress >= total_files:
                    print("\n🎉 全ファイル処理完了!")
                    break
            
            # ログファイルの最新内容表示
            if os.path.exists("processing_incremental.log"):
                with open("processing_incremental.log", 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if "処理中" in last_line or "HTTP Request" in last_line:
                            print(f"📋 {last_line}", end='\r')
            
            time.sleep(10)  # 10秒ごとに更新
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 監視を停止しました")
    except Exception as e:
        print(f"\n❌ エラー: {e}")

if __name__ == "__main__":
    monitor_processing()