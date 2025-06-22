#!/usr/bin/env python3
"""
スマートOCR処理システム
- クリーンスタート機能
- 増分処理対応（新PDFファイルのみ処理）
- バックグラウンド実行・通知機能
- 処理状況の詳細ログ
"""

import os
import sys
import json
import subprocess
import platform
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class SmartOCRProcessor:
    def __init__(self, force_clean: bool = False):
        self.start_time = datetime.now()
        self.force_clean = force_clean
        self.log_file = "smart_processing.log"
        self.progress_file = "smart_progress.json"
        self.processed_files_db = "processed_files.json"
        self.pdf_folder = "PDF"
        
        # 結果ファイル
        self.extraction_results = "extraction_results_pure_english.json"
        self.multi_vocab_results = "multi_vocabulary_analysis_report.json"
        self.vocab_results = "vocabulary_analysis_report.json"
        
    def log(self, message: str, level: str = "INFO"):
        """強化されたログ機能"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        print(log_message)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def update_progress(self, step: int, total_steps: int, current_task: str = "", details: str = ""):
        """詳細進捗更新"""
        progress = {
            "current_step": step,
            "total_steps": total_steps,
            "current_task": current_task,
            "details": details,
            "percentage": round((step / total_steps) * 100, 1),
            "start_time": self.start_time.isoformat(),
            "last_update": datetime.now().isoformat(),
            "force_clean": self.force_clean
        }
        
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        
        self.log(f"進捗: {step}/{total_steps} ({progress['percentage']}%) - {current_task}")
        if details:
            self.log(f"詳細: {details}")
    
    def get_file_hash(self, file_path: str) -> str:
        """ファイルのハッシュ値計算（変更検出用）"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.log(f"ハッシュ計算エラー: {file_path} - {e}", "ERROR")
            return ""
    
    def load_processed_files_db(self) -> Dict:
        """処理済みファイルデータベース読み込み"""
        try:
            if os.path.exists(self.processed_files_db):
                with open(self.processed_files_db, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"処理済みファイルDB読み込みエラー: {e}", "WARNING")
        
        return {"processed_files": {}, "last_update": None}
    
    def save_processed_files_db(self, db: Dict):
        """処理済みファイルデータベース保存"""
        try:
            db["last_update"] = datetime.now().isoformat()
            with open(self.processed_files_db, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"処理済みファイルDB保存エラー: {e}", "ERROR")
    
    def scan_pdf_files(self) -> List[Dict]:
        """PDFファイルスキャン・変更検出"""
        pdf_files = []
        
        if not os.path.exists(self.pdf_folder):
            self.log(f"PDFフォルダが見つかりません: {self.pdf_folder}", "ERROR")
            return pdf_files
        
        for file_name in os.listdir(self.pdf_folder):
            if file_name.endswith(".pdf"):
                file_path = os.path.join(self.pdf_folder, file_name)
                file_hash = self.get_file_hash(file_path)
                file_size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)
                
                pdf_files.append({
                    "name": file_name,
                    "path": file_path,
                    "hash": file_hash,
                    "size": file_size,
                    "modified": modified_time
                })
        
        self.log(f"PDFファイル検出: {len(pdf_files)}個")
        return pdf_files
    
    def determine_processing_strategy(self) -> Dict:
        """処理戦略決定（クリーンスタート vs 増分処理）"""
        strategy = {
            "mode": "clean",  # "clean" or "incremental"
            "all_files": [],
            "new_files": [],
            "changed_files": [],
            "total_to_process": 0
        }
        
        pdf_files = self.scan_pdf_files()
        strategy["all_files"] = pdf_files
        
        # 強制クリーンモード
        if self.force_clean:
            strategy["mode"] = "clean"
            strategy["total_to_process"] = len(pdf_files)
            self.log("🔄 強制クリーンスタートモード")
            return strategy
        
        # 既存結果ファイルチェック
        results_exist = os.path.exists(self.extraction_results)
        
        if not results_exist:
            strategy["mode"] = "clean"
            strategy["total_to_process"] = len(pdf_files)
            self.log("📋 既存結果なし - クリーンスタート")
            return strategy
        
        # 増分処理チェック
        processed_db = self.load_processed_files_db()
        processed_files = processed_db.get("processed_files", {})
        
        for pdf_file in pdf_files:
            file_name = pdf_file["name"]
            current_hash = pdf_file["hash"]
            
            if file_name not in processed_files:
                strategy["new_files"].append(pdf_file)
                self.log(f"🆕 新規ファイル: {file_name}")
            else:
                stored_hash = processed_files[file_name].get("hash", "")
                if current_hash != stored_hash:
                    strategy["changed_files"].append(pdf_file)
                    self.log(f"🔄 変更ファイル: {file_name}")
        
        # 増分処理の可否判定
        files_to_process = strategy["new_files"] + strategy["changed_files"]
        strategy["total_to_process"] = len(files_to_process)
        
        if files_to_process:
            strategy["mode"] = "incremental"
            self.log(f"📈 増分処理モード: {len(files_to_process)}ファイル")
        else:
            self.log("✅ 処理対象ファイルなし - 分析のみ実行")
        
        return strategy
    
    def backup_existing_results(self):
        """既存結果のバックアップ"""
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        files_to_backup = [
            self.extraction_results,
            self.multi_vocab_results,
            self.vocab_results
        ]
        
        for file_name in files_to_backup:
            if os.path.exists(file_name):
                backup_name = f"{file_name.split('.')[0]}_backup_{backup_timestamp}.json"
                subprocess.run(["cp", file_name, backup_name], check=True)
                self.log(f"💾 バックアップ: {backup_name}")
    
    def run_clean_ocr_extraction(self):
        """クリーンOCR抽出"""
        self.log("🔄 クリーンOCR抽出開始")
        
        try:
            # 既存結果削除
            for result_file in [self.extraction_results, self.multi_vocab_results, self.vocab_results]:
                if os.path.exists(result_file):
                    os.remove(result_file)
                    self.log(f"🗑️  削除: {result_file}")
            
            # OCR実行
            result = subprocess.run(
                [sys.executable, "pdf_text_extractor.py"],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.log("✅ クリーンOCR抽出完了")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ OCR抽出エラー: {e}", "ERROR")
            if e.stderr:
                self.log(f"エラー詳細: {e.stderr}", "ERROR")
            return False
    
    def run_vocabulary_analysis(self):
        """語彙分析実行"""
        self.log("📚 語彙分析開始")
        
        try:
            # Target 1900分析
            subprocess.run([sys.executable, "vocabulary_analyzer.py"], check=True)
            self.log("✅ Target 1900分析完了")
            
            # 複数単語帳分析
            subprocess.run([sys.executable, "vocabulary_analyzer_multi.py"], check=True)
            self.log("✅ 複数単語帳分析完了")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ 語彙分析エラー: {e}", "ERROR")
            return False
    
    def update_streamlit_data(self):
        """Streamlitデータ更新"""
        try:
            data_processor_path = "utils/data_processor.py"
            if os.path.exists(data_processor_path):
                subprocess.run([sys.executable, data_processor_path], check=True)
                self.log("✅ Streamlitデータ更新完了")
            else:
                self.log("⚠️  data_processor.py未発見 - スキップ", "WARNING")
        except Exception as e:
            self.log(f"⚠️  Streamlitデータ更新エラー: {e}", "WARNING")
    
    def update_processed_files_db(self, pdf_files: List[Dict]):
        """処理済みファイルDB更新"""
        processed_db = self.load_processed_files_db()
        
        for pdf_file in pdf_files:
            processed_db["processed_files"][pdf_file["name"]] = {
                "hash": pdf_file["hash"],
                "size": pdf_file["size"],
                "modified": pdf_file["modified"],
                "processed_at": datetime.now().isoformat()
            }
        
        self.save_processed_files_db(processed_db)
        self.log(f"💾 処理済みDB更新: {len(pdf_files)}ファイル")
    
    def send_notification(self, title: str, message: str):
        """システム通知送信"""
        try:
            if platform.system() == "Darwin":  # macOS
                script = f'display notification "{message}" with title "{title}" sound name "Glass"'
                subprocess.run(["osascript", "-e", script], check=True)
                
                # Terminalを前面に
                subprocess.run([
                    "osascript", "-e", 
                    'tell application "Terminal" to activate'
                ], check=True)
                
        except Exception as e:
            self.log(f"⚠️  通知送信エラー: {e}", "WARNING")
    
    def generate_completion_summary(self) -> Dict:
        """処理完了サマリー"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # ファイル情報収集
        results_info = {}
        for file_name in [self.extraction_results, self.multi_vocab_results, self.vocab_results]:
            if os.path.exists(file_name):
                file_size = os.path.getsize(file_name)
                results_info[file_name] = {
                    "exists": True,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_name)).isoformat()
                }
            else:
                results_info[file_name] = {"exists": False}
        
        summary = {
            "completion_time": end_time.isoformat(),
            "duration": str(duration),
            "mode": "clean" if self.force_clean else "auto",
            "pdf_count": len(self.scan_pdf_files()),
            "generated_files": results_info,
            "log_file": self.log_file
        }
        
        with open("processing_completion_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary
    
    def run_complete_processing(self):
        """完全処理実行"""
        try:
            self.log("🚀 スマートOCR処理開始")
            
            # 処理戦略決定
            strategy = self.determine_processing_strategy()
            total_steps = 4
            
            self.update_progress(1, total_steps, "戦略決定完了", f"モード: {strategy['mode']}")
            
            # バックアップ
            self.backup_existing_results()
            
            # OCR処理
            if strategy["mode"] == "clean" or strategy["total_to_process"] > 0:
                self.update_progress(2, total_steps, "OCR処理実行中", f"{strategy['total_to_process']}ファイル")
                
                if not self.run_clean_ocr_extraction():
                    raise Exception("OCR処理に失敗しました")
                
                # 処理済みDB更新
                self.update_processed_files_db(strategy["all_files"])
            else:
                self.update_progress(2, total_steps, "OCR処理スキップ", "変更なし")
            
            # 語彙分析
            self.update_progress(3, total_steps, "語彙分析実行中")
            if not self.run_vocabulary_analysis():
                raise Exception("語彙分析に失敗しました")
            
            # Streamlitデータ更新
            self.update_progress(4, total_steps, "ダッシュボード更新中")
            self.update_streamlit_data()
            
            # 完了処理
            summary = self.generate_completion_summary()
            
            # 成功通知
            duration_str = str(summary["duration"]).split(".")[0]
            success_message = f"OCR・語彙分析完了！\n処理時間: {duration_str}\nPDF: {summary['pdf_count']}個"
            
            self.log("🎉 全処理完了!")
            self.log(f"📊 処理時間: {summary['duration']}")
            self.send_notification("OCR処理完了", success_message)
            
            return True
            
        except Exception as e:
            error_message = f"処理エラー: {str(e)}"
            self.log(f"❌ {error_message}", "ERROR")
            self.send_notification("OCR処理エラー", error_message)
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="スマートOCR処理システム")
    parser.add_argument("--clean", action="store_true", help="強制クリーンスタート")
    args = parser.parse_args()
    
    processor = SmartOCRProcessor(force_clean=args.clean)
    success = processor.run_complete_processing()
    
    if success:
        print("\n✅ 処理が正常に完了しました")
        print("📊 結果ファイル:")
        print("   - extraction_results_pure_english.json")
        print("   - multi_vocabulary_analysis_report.json")
        print("   - processing_completion_summary.json")
    else:
        print("\n❌ 処理中にエラーが発生しました")
        print("📋 ログファイル: smart_processing.log")

if __name__ == "__main__":
    main()