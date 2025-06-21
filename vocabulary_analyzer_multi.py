#!/usr/bin/env python3
"""
複数単語帳との一致率分析ツール
extraction_results_pure_english.jsonから抽出した単語と複数の単語帳の比較分析
対応単語帳: Target 1900, Target 1400, システム英単語, LEAP, 鉄壁
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
import logging

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import pandas as pd

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiVocabularyAnalyzer:
    def __init__(self):
        """
        複数単語帳との一致率分析を行うクラス
        """
        # NLTK データのダウンロード
        self._download_nltk_data()
        
        # Lemmatizer初期化
        self.lemmatizer = WordNetLemmatizer()
        
        # ストップワード
        self.stop_words = set(stopwords.words('english'))
        
        # サポートする単語帳の定義
        self.vocabulary_books = {
            'Target 1900': {
                'file': 'target1900.csv',
                'word_column': 'word'
            },
            'Target 1400': {
                'file': 'target1400.csv', 
                'word_column': '単語'
            },
            'システム英単語': {
                'file': 'システム英単語.csv',
                'word_column': '英語'
            },
            'LEAP': {
                'file': 'LEAP.csv',
                'word_column': '英語'
            },
            '鉄壁': {
                'file': '鉄壁.csv',
                'word_column': '英語'
            }
        }
        
    def _download_nltk_data(self):
        """必要なNLTKデータをダウンロード"""
        required_data = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        
        for data_name in required_data:
            try:
                nltk.data.find(f'tokenizers/{data_name}' if data_name == 'punkt' 
                              else f'corpora/{data_name}' if data_name in ['stopwords', 'wordnet'] 
                              else f'taggers/{data_name}')
            except LookupError:
                logger.info(f"Downloading NLTK data: {data_name}")
                nltk.download(data_name)
    
    def load_vocabulary_lists(self) -> Dict[str, Set[str]]:
        """
        すべての単語帳を読み込み
        
        Returns:
            {単語帳名: 正規化済み単語セット}の辞書
        """
        vocabulary_sets = {}
        
        for book_name, config in self.vocabulary_books.items():
            try:
                file_path = config['file']
                word_column = config['word_column']
                
                logger.info(f"{book_name} を読み込み中: {file_path}")
                
                # CSV読み込み（BOM対応）
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                if word_column not in df.columns:
                    logger.error(f"{book_name}: '{word_column}'列が見つかりません")
                    continue
                
                words = set()
                for word in df[word_column].dropna():
                    word = str(word).strip().lower()
                    if word:
                        # 基本的なクリーニング
                        cleaned_word = re.sub(r'[^\w]', '', word.lower())
                        if len(cleaned_word) >= 2 and not cleaned_word.isdigit():
                            # lemmatization（原形化）
                            lemmatized = self.lemmatizer.lemmatize(cleaned_word, pos='v')  # 動詞として
                            lemmatized = self.lemmatizer.lemmatize(lemmatized, pos='n')    # 名詞として
                            words.add(lemmatized)
                
                vocabulary_sets[book_name] = words
                logger.info(f"{book_name}: {len(words)}語読み込み完了")
                
            except FileNotFoundError:
                logger.error(f"{book_name}のファイルが見つかりません: {config['file']}")
                continue
            except Exception as e:
                logger.error(f"{book_name}読み込みエラー: {e}")
                continue
        
        return vocabulary_sets
    
    def load_extracted_data(self, file_path: str) -> Tuple[List[str], Dict]:
        """
        extraction_results_pure_english.jsonから抽出データを読み込み
        
        Args:
            file_path: 抽出結果JSONファイルのパス
            
        Returns:
            (正規化済み抽出単語リスト, 元データ)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 全ての抽出単語を収集
            all_extracted_words = []
            for item in data.get('extracted_data', []):
                words = item.get('extracted_words', [])
                all_extracted_words.extend(words)
            
            # 正規化（lemmatization付き）
            normalized_words = []
            for word in all_extracted_words:
                # 基本的なクリーニング
                cleaned_word = re.sub(r'[^\w]', '', word.lower())
                if len(cleaned_word) >= 2 and not cleaned_word.isdigit():
                    # lemmatization（原形化）
                    lemmatized = self.lemmatizer.lemmatize(cleaned_word, pos='v')  # 動詞として
                    lemmatized = self.lemmatizer.lemmatize(lemmatized, pos='n')    # 名詞として
                    normalized_words.append(lemmatized)
            
            logger.info(f"抽出された総単語数: {len(all_extracted_words)}")
            logger.info(f"正規化後ユニーク単語数: {len(set(normalized_words))}")
            
            return normalized_words, data
            
        except FileNotFoundError:
            logger.error(f"抽出結果ファイルが見つかりません: {file_path}")
            raise
        except Exception as e:
            logger.error(f"抽出結果読み込みエラー: {e}")
            raise
    
    def _normalize_word(self, word: str) -> str:
        """
        単語の正規化処理
        
        Args:
            word: 正規化する単語
            
        Returns:
            正規化済み単語（空文字列の場合は除外対象）
        """
        # 基本的なクリーニング
        word = re.sub(r'[^\w]', '', word.lower())
        
        # 短すぎる単語や数字のみの単語を除外
        if len(word) < 2 or word.isdigit():
            return ""
        
        # ストップワードを除外
        if word in self.stop_words:
            return ""
        
        # レンマ化（原形化）
        try:
            lemmatized = self.lemmatizer.lemmatize(word, pos='v')  # 動詞として
            lemmatized = self.lemmatizer.lemmatize(lemmatized, pos='n')  # 名詞として
            return lemmatized
        except:
            return word
    
    def calculate_multi_vocabulary_coverage(self, vocabulary_sets: Dict[str, Set[str]], extracted_words: List[str]) -> Dict:
        """
        複数単語帳での一致率統計の計算
        
        Args:
            vocabulary_sets: {単語帳名: 単語セット}の辞書
            extracted_words: 抽出単語リスト
            
        Returns:
            複数単語帳の統計情報辞書
        """
        # ユニーク抽出単語
        unique_extracted = set(extracted_words)
        word_frequencies = Counter(extracted_words)
        
        multi_stats = {
            'extracted_total_words': len(extracted_words),
            'extracted_unique_words': len(unique_extracted),
            'vocabulary_coverage': {},
            'word_frequencies': dict(word_frequencies.most_common(50))
        }
        
        # 各単語帳との比較分析
        for book_name, target_words in vocabulary_sets.items():
            # 一致単語
            matched_words = target_words.intersection(unique_extracted)
            
            # 統計計算
            target_coverage_rate = len(matched_words) / len(target_words) * 100 if target_words else 0
            extraction_precision = len(matched_words) / len(unique_extracted) * 100 if unique_extracted else 0
            
            # 頻度分析
            matched_frequencies = {word: word_frequencies[word] for word in matched_words}
            
            book_stats = {
                'target_total_words': len(target_words),
                'matched_words_count': len(matched_words),
                'target_coverage_rate': round(target_coverage_rate, 2),
                'extraction_precision': round(extraction_precision, 2),
                'matched_words': sorted(list(matched_words)),
                'unmatched_from_target': sorted(list(target_words - matched_words)),
                'unmatched_from_extracted': sorted(list(unique_extracted - target_words)),
                'matched_word_frequencies': dict(sorted(matched_frequencies.items(), 
                                                       key=lambda x: x[1], reverse=True)[:30])
            }
            
            multi_stats['vocabulary_coverage'][book_name] = book_stats
            logger.info(f"{book_name}: カバレッジ率 {target_coverage_rate:.2f}%, 抽出精度 {extraction_precision:.2f}%")
        
        return multi_stats
    
    def analyze_by_frequency_tiers(self, target_words: Set[str], extracted_words: List[str]) -> Dict:
        """
        頻度層別の分析
        
        Args:
            target_words: Target 1900単語セット
            extracted_words: 抽出単語リスト
            
        Returns:
            頻度層別統計
        """
        word_frequencies = Counter(extracted_words)
        unique_extracted = set(extracted_words)
        matched_words = target_words.intersection(unique_extracted)
        
        # 頻度による層分け
        frequency_tiers = {
            'high_frequency': [],    # 10回以上
            'medium_frequency': [],  # 3-9回
            'low_frequency': []      # 1-2回
        }
        
        for word in unique_extracted:
            freq = word_frequencies[word]
            if freq >= 10:
                frequency_tiers['high_frequency'].append(word)
            elif freq >= 3:
                frequency_tiers['medium_frequency'].append(word)
            else:
                frequency_tiers['low_frequency'].append(word)
        
        # 各層での一致率計算
        tier_analysis = {}
        for tier_name, tier_words in frequency_tiers.items():
            tier_set = set(tier_words)
            tier_matched = target_words.intersection(tier_set)
            
            tier_analysis[tier_name] = {
                'total_words': len(tier_words),
                'matched_words': len(tier_matched),
                'coverage_rate': round(len(tier_matched) / len(tier_words) * 100, 2) if tier_words else 0,
                'matched_word_list': sorted(list(tier_matched))
            }
        
        return tier_analysis
    
    def analyze_by_university_multi(self, vocabulary_sets: Dict[str, Set[str]], original_data: Dict) -> Dict:
        """
        大学別の複数単語帳語彙分析
        
        Args:
            vocabulary_sets: {単語帳名: 単語セット}の辞書
            original_data: 抽出結果の元データ
            
        Returns:
            大学別複数単語帳分析結果
        """
        university_analysis = {}
        
        for item in original_data.get('extracted_data', []):
            source_file = item.get('source_file', '')
            words = item.get('extracted_words', [])
            
            # 大学名を抽出（ファイル名から）
            university_name = self._extract_university_name(source_file)
            
            # 単語を正規化（lemmatization付き）
            normalized_words = []
            for word in words:
                cleaned_word = re.sub(r'[^\w]', '', word.lower())
                if len(cleaned_word) >= 2 and not cleaned_word.isdigit():
                    # lemmatization（原形化）
                    lemmatized = self.lemmatizer.lemmatize(cleaned_word, pos='v')  # 動詞として
                    lemmatized = self.lemmatizer.lemmatize(lemmatized, pos='n')    # 名詞として
                    normalized_words.append(lemmatized)
            
            unique_words = set(normalized_words)
            word_frequencies = Counter(normalized_words)
            
            # 各単語帳との一致分析
            vocabulary_coverage = {}
            for book_name, target_words in vocabulary_sets.items():
                matched_words = target_words.intersection(unique_words)
                
                # 統計計算
                word_count = len(normalized_words)
                unique_count = len(unique_words)
                matched_count = len(matched_words)
                coverage_rate = (matched_count / len(target_words) * 100) if target_words else 0
                precision = (matched_count / unique_count * 100) if unique_count else 0
                
                # 頻度分析
                matched_frequencies = {word: word_frequencies[word] for word in matched_words}
                
                vocabulary_coverage[book_name] = {
                    'target_total_words': len(target_words),
                    'matched_words_count': matched_count,
                    'target_coverage_rate': round(coverage_rate, 2),
                    'extraction_precision': round(precision, 2),
                    'matched_words': sorted(list(matched_words)),
                    'matched_word_frequencies': dict(sorted(matched_frequencies.items(), 
                                                           key=lambda x: x[1], reverse=True)[:10])
                }
            
            university_analysis[university_name] = {
                'source_file': source_file,
                'total_words': len(normalized_words),
                'unique_words': len(unique_words),
                'vocabulary_coverage': vocabulary_coverage,
                'word_frequencies': dict(word_frequencies.most_common(20)),
                'ocr_confidence': item.get('ocr_confidence', 0),
                'pages_processed': item.get('pages_processed', 0)
            }
        
        return university_analysis
    
    def _extract_university_name(self, filename: str) -> str:
        """
        ファイル名から大学名・学部名を抽出
        
        Args:
            filename: ファイル名
            
        Returns:
            大学名・学部名
        """
        # ファイル名から大学名・学部名を抽出（学部別に分離）
        if '早稲田大学' in filename:
            if '法学部' in filename:
                return '早稲田大学_法学部'
            elif '政治経済学部' in filename:
                return '早稲田大学_政治経済学部'
            elif '商学部' in filename:
                return '早稲田大学_商学部'
            elif '文学部' in filename:
                return '早稲田大学_文学部'
            elif '理工学部' in filename:
                return '早稲田大学_理工学部'
            else:
                return '早稲田大学'
        elif '東京大学' in filename:
            return '東京大学'
        elif '慶應義塾大学' in filename or '慶應' in filename:
            return '慶應義塾大学'
        elif '京都大学' in filename:
            return '京都大学'
        elif '一橋大学' in filename:
            return '一橋大学'
        elif '大阪大学' in filename:
            return '大阪大学'
        elif '明治大学' in filename:
            return '明治大学'
        elif '立教大学' in filename:
            return '立教大学'
        elif '上智大学' in filename:
            return '上智大学'
        elif '青山学院大学' in filename:
            return '青山学院大学'
        else:
            # その他の場合は最初の単語を使用
            base_name = filename.replace('.pdf', '')
            parts = base_name.split('_')
            return parts[0] if parts else filename

    def generate_multi_vocabulary_report(
        self, 
        extraction_file: str, 
        output_file: str = None
    ) -> Dict:
        """
        複数単語帳分析レポートの生成
        
        Args:
            extraction_file: 抽出結果ファイルパス
            output_file: 出力ファイルパス（Noneの場合は自動生成）
            
        Returns:
            分析結果辞書
        """
        logger.info("複数単語帳分析開始...")
        
        # データ読み込み
        vocabulary_sets = self.load_vocabulary_lists()
        extracted_words, original_data = self.load_extracted_data(extraction_file)
        
        # 複数単語帳での一致率分析
        multi_stats = self.calculate_multi_vocabulary_coverage(vocabulary_sets, extracted_words)
        
        # 大学別分析（各単語帳に対して）
        university_analysis = self.analyze_by_university_multi(vocabulary_sets, original_data)
        
        # 総合レポート作成
        report = {
            'analysis_metadata': {
                'extraction_file': extraction_file,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'vocabulary_books': list(vocabulary_sets.keys()),
                'extraction_summary': original_data.get('extraction_summary', {})
            },
            'multi_vocabulary_coverage': multi_stats,
            'university_analysis': university_analysis,
            'recommendations': self._generate_multi_recommendations(multi_stats)
        }
        
        # ファイル出力
        if output_file is None:
            output_file = "multi_vocabulary_analysis_report.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析完了。結果を {output_file} に保存しました。")
        
        # 結果サマリーを表示
        self._print_multi_summary(multi_stats)
        
        # 大学別サマリーを表示
        self._print_university_multi_summary(university_analysis)
        
        return report
    
    def _generate_multi_recommendations(self, multi_stats: Dict) -> List[str]:
        """
        複数単語帳分析結果に基づく推奨事項生成
        """
        recommendations = []
        
        # 各単語帳のカバレッジ率を確認
        vocabulary_coverage = multi_stats['vocabulary_coverage']
        
        # Target 1900の結果
        if 'Target 1900' in vocabulary_coverage:
            target1900_coverage = vocabulary_coverage['Target 1900']['target_coverage_rate']
            if target1900_coverage < 20:
                recommendations.append("Target 1900カバレッジが低いです。基本語彙の強化が必要です。")
            elif target1900_coverage < 40:
                recommendations.append("Target 1900カバレッジは中程度です。重要単語の復習に重点を置いてください。")
            else:
                recommendations.append("Target 1900カバレッジは良好です。上級語彙学習に進むことをお勧めします。")
        
        # 最もカバレッジ率の高い単語帳を特定
        best_book = max(vocabulary_coverage.items(), key=lambda x: x[1]['target_coverage_rate'])
        recommendations.append(f"最も適合性が高い単語帳: {best_book[0]} (カバレッジ率: {best_book[1]['target_coverage_rate']:.1f}%)")
        
        # 複数単語帳での総合的な推奨
        high_coverage_books = [name for name, data in vocabulary_coverage.items() 
                              if data['target_coverage_rate'] > 25]
        
        if len(high_coverage_books) >= 3:
            recommendations.append("複数の単語帳で高いカバレッジを達成しています。語彙力は十分です。")
        elif len(high_coverage_books) >= 1:
            recommendations.append(f"{', '.join(high_coverage_books)}での学習を重点的に行うことをお勧めします。")
        else:
            recommendations.append("全般的に語彙力強化が必要です。基礎単語帳から始めることをお勧めします。")
        
        return recommendations
    
    def _generate_recommendations(self, basic_stats: Dict, frequency_analysis: Dict) -> List[str]:
        """
        分析結果に基づく推奨事項生成
        """
        recommendations = []
        
        coverage_rate = basic_stats['target_coverage_rate']
        precision = basic_stats['extraction_precision']
        
        if coverage_rate < 30:
            recommendations.append("Target 1900カバレッジが低いです。より多様な教材での学習を推奨します。")
        elif coverage_rate < 50:
            recommendations.append("Target 1900カバレッジは中程度です。重要単語の復習に重点を置いてください。")
        else:
            recommendations.append("Target 1900カバレッジは良好です。応用レベルの語彙学習に進むことをお勧めします。")
        
        if precision < 40:
            recommendations.append("抽出された単語の多くがTarget 1900外です。基礎語彙の強化が必要です。")
        
        # 頻度分析に基づく推奨
        high_freq = frequency_analysis.get('high_frequency', {})
        if high_freq.get('coverage_rate', 0) > 80:
            recommendations.append("高頻度単語のTarget 1900カバレッジは優秀です。")
        else:
            recommendations.append("頻出単語でTarget 1900外の語彙があります。これらの習得を優先してください。")
        
        return recommendations
    
    def _print_summary(self, stats: Dict):
        """分析結果サマリーの表示"""
        print("\n" + "="*60)
        print("📊 Target 1900 語彙分析結果サマリー")
        print("="*60)
        print(f"Target 1900総単語数: {stats['target_total_words']:,}")
        print(f"抽出単語総数: {stats['extracted_total_words']:,}")
        print(f"抽出ユニーク単語数: {stats['extracted_unique_words']:,}")
        print(f"一致単語数: {stats['matched_words_count']:,}")
        print()
        print(f"🎯 Target 1900カバレッジ率: {stats['target_coverage_rate']:.2f}%")
        print(f"🔍 抽出語彙精度: {stats['extraction_precision']:.2f}%")
        print()
        print("上位一致単語(頻度順):")
        for word, freq in list(stats['matched_word_frequencies'].items())[:10]:
            print(f"  • {word}: {freq}回")
        print("="*60)
        
    def _print_multi_summary(self, multi_stats: Dict):
        """複数単語帳分析結果サマリーの表示"""
        print("\n" + "="*70)
        print("📚 複数単語帳語彙分析結果サマリー")
        print("="*70)
        print(f"抽出単語総数: {multi_stats['extracted_total_words']:,}")
        print(f"抽出ユニーク単語数: {multi_stats['extracted_unique_words']:,}")
        print()
        
        # 各単語帳のカバレッジ率表示
        print("📊 単語帳別カバレッジ率:")
        for book_name, data in multi_stats['vocabulary_coverage'].items():
            print(f"  • {book_name}: {data['target_coverage_rate']:.2f}% "
                  f"(一致: {data['matched_words_count']:,}/{data['target_total_words']:,}語, "
                  f"精度: {data['extraction_precision']:.1f}%)")
        
        print("\n🔥 最頻出単語:")
        for word, freq in list(multi_stats['word_frequencies'].items())[:10]:
            print(f"  • {word}: {freq}回")
        print("="*70)
    
    def _print_university_multi_summary(self, university_analysis: Dict):
        """大学・学部別複数単語帳分析結果サマリーの表示"""
        print("\n" + "="*80)
        print("🏫 大学・学部別 複数単語帳語彙分析結果")
        print("="*80)
        
        for university_name, data in university_analysis.items():
            print(f"\n【{university_name}】")
            print(f"  ファイル名: {data['source_file']}")
            print(f"  総単語数: {data['total_words']:,}")
            print(f"  ユニーク単語数: {data['unique_words']:,}")
            print(f"  OCR信頼度: {data['ocr_confidence']:.1%}")
            print(f"  処理ページ数: {data['pages_processed']}")
            print()
            
            # 各単語帳のカバレッジ率表示
            print(f"  📚 単語帳別カバレッジ率:")
            for book_name, book_data in data['vocabulary_coverage'].items():
                print(f"    • {book_name}: {book_data['target_coverage_rate']:.2f}% "
                      f"(一致: {book_data['matched_words_count']:,}語, "
                      f"精度: {book_data['extraction_precision']:.1f}%)")
        
        print("="*80)
    
    def _print_university_summary(self, university_analysis: Dict):
        """大学・学部別分析結果サマリーの表示"""
        print("\n" + "="*60)
        print("🏫 大学・学部別 Target 1900 語彙分析結果")
        print("="*60)
        
        for university_name, data in university_analysis.items():
            print(f"\n【{university_name}】")
            print(f"  ファイル名: {data['source_file']}")
            print(f"  総単語数: {data['total_words']:,}")
            print(f"  ユニーク単語数: {data['unique_words']:,}")
            print(f"  Target 1900一致数: {data['matched_words_count']:,}")
            print(f"  カバレッジ率: {data['target_coverage_rate']:.2f}%")
            print(f"  抽出精度: {data['extraction_precision']:.2f}%")
            print(f"  OCR信頼度: {data['ocr_confidence']:.1%}")
            print(f"  処理ページ数: {data['pages_processed']}")
            
            # 上位頻出単語（一致語のみ）
            matched_words = set(data['matched_words'])
            top_matched = []
            for word, freq in data['word_frequencies'].items():
                if word in matched_words:
                    top_matched.append((word, freq))
                if len(top_matched) >= 5:
                    break
            
            if top_matched:
                print(f"  上位一致単語: {', '.join([f'{word}({freq})' for word, freq in top_matched])}")
        
        print("="*60)

def main():
    """メイン実行関数"""
    analyzer = MultiVocabularyAnalyzer()
    
    # ファイルパス設定
    extraction_file = "extraction_results_pure_english.json"
    output_file = "multi_vocabulary_analysis_report.json"
    
    try:
        # 複数単語帳分析実行
        report = analyzer.generate_multi_vocabulary_report(
            extraction_file=extraction_file,
            output_file=output_file
        )
        
        print(f"\n✅ 複数単語帳分析完了！詳細は {output_file} をご確認ください。")
        
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        raise

if __name__ == "__main__":
    main()