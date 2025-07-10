#!/usr/bin/env python3
"""
単語帳分析エンジン
既存のvocabulary_analyzer_multi.pyから移植・最適化
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
import pandas as pd

from utils.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)

class VocabularyAnalyzer:
    def __init__(self, config: Dict = None):
        """
        単語帳分析クラス
        
        Args:
            config: 設定辞書
        """
        self.config = config or {}
        self.preprocessor = TextPreprocessor(
            remove_stopwords=self.config.get('remove_stopwords', True),
            lemmatize=self.config.get('lemmatization', True)
        )
        
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
            'Target 1200': {
                'file': 'target1200.csv',
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
    
    def load_vocabulary_lists(self, data_path: str = "data/vocabulary_books/") -> Dict[str, Set[str]]:
        """
        すべての単語帳を読み込み
        
        Args:
            data_path: 単語帳データディレクトリパス
            
        Returns:
            {単語帳名: 正規化済み単語セット}の辞書
        """
        vocabulary_sets = {}
        data_path = Path(data_path)
        
        for book_name, config in self.vocabulary_books.items():
            try:
                file_path = data_path / config['file']
                word_column = config['word_column']
                
                logger.info(f"{book_name} を読み込み中: {file_path}")
                
                if not file_path.exists():
                    logger.warning(f"単語帳ファイルが見つかりません: {file_path}")
                    continue
                
                # CSV読み込み（BOM対応）
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
                if word_column not in df.columns:
                    logger.error(f"{book_name}: '{word_column}'列が見つかりません")
                    continue
                
                words = set()
                for word in df[word_column].dropna():
                    word = str(word).strip()
                    if word:
                        normalized = self.preprocessor.normalize_word(word)
                        if normalized:
                            words.add(normalized)
                
                vocabulary_sets[book_name] = words
                logger.info(f"{book_name}: {len(words)}語読み込み完了")
                
            except Exception as e:
                logger.error(f"{book_name}読み込みエラー: {e}")
                continue
        
        return vocabulary_sets
    
    def analyze_text_vocabulary(self, text: str, vocabulary_sets: Dict[str, Set[str]]) -> Dict:
        """
        テキストの語彙分析実行
        
        Args:
            text: 分析対象テキスト
            vocabulary_sets: 単語帳セット辞書
            
        Returns:
            分析結果辞書
        """
        if not text:
            return {}
        
        # テキストから単語抽出・正規化
        extracted_words = self.preprocessor.extract_normalized_words(text)
        unique_extracted = set(extracted_words)
        word_frequencies = Counter(extracted_words)
        
        # 基本統計
        analysis_result = {
            'text_statistics': {
                'total_words': len(extracted_words),
                'unique_words': len(unique_extracted),
                'word_frequencies': dict(word_frequencies.most_common(50))
            },
            'vocabulary_coverage': {},
            'summary': {}
        }
        
        # 各単語帳との比較分析
        for book_name, target_words in vocabulary_sets.items():
            coverage_result = self._calculate_vocabulary_coverage(
                unique_extracted, target_words, word_frequencies
            )
            analysis_result['vocabulary_coverage'][book_name] = coverage_result
        
        # サマリー統計の計算
        analysis_result['summary'] = self._calculate_summary_statistics(
            analysis_result['vocabulary_coverage']
        )
        
        return analysis_result
    
    def _calculate_vocabulary_coverage(
        self, 
        extracted_words: Set[str], 
        target_words: Set[str], 
        word_frequencies: Counter
    ) -> Dict:
        """
        単語帳カバレッジの計算
        
        Args:
            extracted_words: 抽出された単語セット
            target_words: 単語帳の単語セット
            word_frequencies: 単語頻度
            
        Returns:
            カバレッジ分析結果
        """
        # 一致単語
        matched_words = target_words.intersection(extracted_words)
        
        # 統計計算
        vocabulary_utilization_rate = len(matched_words) / len(target_words) * 100 if target_words else 0
        vocabulary_coverage_rate = len(matched_words) / len(extracted_words) * 100 if extracted_words else 0
        
        # 頻度分析
        matched_frequencies = {word: word_frequencies[word] for word in matched_words}
        
        coverage_result = {
            'target_total_words': len(target_words),
            'extracted_unique_words': len(extracted_words),
            'matched_words_count': len(matched_words),
            'vocabulary_utilization_rate': round(vocabulary_utilization_rate, 2),
            'vocabulary_coverage_rate': round(vocabulary_coverage_rate, 2),
            'matched_words': sorted(list(matched_words)),
            'unmatched_from_target': sorted(list(target_words - matched_words)),
            'unmatched_from_extracted': sorted(list(extracted_words - target_words)),
            'matched_word_frequencies': dict(sorted(
                matched_frequencies.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:30])
        }
        
        return coverage_result
    
    def _calculate_summary_statistics(self, vocabulary_coverage: Dict) -> Dict:
        """
        サマリー統計の計算
        
        Args:
            vocabulary_coverage: 語彙カバレッジ分析結果
            
        Returns:
            サマリー統計
        """
        if not vocabulary_coverage:
            return {}
        
        # 各指標の平均値計算
        utilization_rates = [data['vocabulary_utilization_rate'] for data in vocabulary_coverage.values()]
        coverage_rates = [data['vocabulary_coverage_rate'] for data in vocabulary_coverage.values()]
        
        # 最適単語帳の特定
        best_coverage_book = max(
            vocabulary_coverage.items(), 
            key=lambda x: x[1]['vocabulary_coverage_rate']
        )
        
        best_utilization_book = max(
            vocabulary_coverage.items(),
            key=lambda x: x[1]['vocabulary_utilization_rate']
        )
        
        summary = {
            'average_vocabulary_utilization_rate': round(sum(utilization_rates) / len(utilization_rates), 2),
            'average_vocabulary_coverage_rate': round(sum(coverage_rates) / len(coverage_rates), 2),
            'best_coverage_book': {
                'name': best_coverage_book[0],
                'rate': best_coverage_book[1]['vocabulary_coverage_rate']
            },
            'best_utilization_book': {
                'name': best_utilization_book[0],
                'rate': best_utilization_book[1]['vocabulary_utilization_rate']
            },
            'total_vocabulary_books': len(vocabulary_coverage)
        }
        
        return summary
    
    def generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """
        分析結果に基づく推奨事項生成
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            推奨事項リスト
        """
        recommendations = []
        
        if not analysis_result.get('vocabulary_coverage'):
            return ["分析データが不足しています。"]
        
        summary = analysis_result.get('summary', {})
        vocabulary_coverage = analysis_result['vocabulary_coverage']
        
        # 最適単語帳の推奨
        best_book = summary.get('best_coverage_book', {})
        if best_book:
            recommendations.append(
                f"最も効果的な単語帳: {best_book['name']} "
                f"(語彙カバレッジ率: {best_book['rate']:.1f}%)"
            )
        
        # カバレッジ率による評価
        avg_coverage = summary.get('average_vocabulary_coverage_rate', 0)
        if avg_coverage < 30:
            recommendations.append(
                f"語彙カバレッジ率が低いです({avg_coverage:.1f}%)。"
                "より基礎的な単語帳から始めることをお勧めします。"
            )
        elif avg_coverage < 50:
            recommendations.append(
                f"語彙カバレッジ率は中程度です({avg_coverage:.1f}%)。"
                "現在の単語帳で継続学習をお勧めします。"
            )
        else:
            recommendations.append(
                f"語彙カバレッジ率は良好です({avg_coverage:.1f}%)。"
                "より高度な語彙学習に進むことができます。"
            )
        
        # 高カバレッジ率の単語帳リスト
        high_coverage_books = [
            name for name, data in vocabulary_coverage.items() 
            if data['vocabulary_coverage_rate'] > 40
        ]
        
        if len(high_coverage_books) >= 2:
            recommendations.append(
                f"複数の単語帳で高い語彙カバレッジ率を達成: {', '.join(high_coverage_books)}"
            )
        
        return recommendations
    
    def export_detailed_analysis(self, analysis_result: Dict, output_path: str):
        """
        詳細分析結果をJSONファイルに出力
        
        Args:
            analysis_result: 分析結果
            output_path: 出力ファイルパス
        """
        try:
            output_path = Path(output_path)
            
            # 推奨事項を追加
            detailed_result = analysis_result.copy()
            detailed_result['recommendations'] = self.generate_recommendations(analysis_result)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"詳細分析結果を出力しました: {output_path}")
            
        except Exception as e:
            logger.error(f"分析結果の出力に失敗しました: {e}")

def main():
    """テスト用メイン関数"""
    analyzer = VocabularyAnalyzer()
    
    # サンプルテキスト
    sample_text = """
    The advancement of artificial intelligence has revolutionized numerous industries. 
    Machine learning algorithms can now process vast amounts of data to identify patterns 
    and make predictions with remarkable accuracy. However, the implementation of these 
    technologies requires careful consideration of ethical implications and potential 
    societal impacts.
    """
    
    print("=== Vocabulary Analysis Test ===")
    print(f"Sample text: {sample_text}")
    print()
    
    # 単語帳読み込み（テスト用にダミーデータ）
    vocabulary_sets = {
        'Test Vocabulary': {
            'advancement', 'artificial', 'intelligence', 'revolutionized', 
            'industries', 'machine', 'learning', 'algorithms', 'process',
            'data', 'identify', 'patterns', 'predictions', 'accuracy'
        }
    }
    
    # 分析実行
    result = analyzer.analyze_text_vocabulary(sample_text, vocabulary_sets)
    
    # 結果表示
    print("Analysis Results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 推奨事項表示
    recommendations = analyzer.generate_recommendations(result)
    print("\\nRecommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

if __name__ == "__main__":
    main()