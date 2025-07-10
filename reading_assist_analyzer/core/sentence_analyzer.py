#!/usr/bin/env python3
"""
文構造分析エンジン
文長、文の複雑さ、読みやすさ指標を分析
"""

import re
import logging
import statistics
from typing import Dict, List, Tuple, Optional
from collections import Counter
import textstat

from utils.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)

class SentenceAnalyzer:
    def __init__(self):
        """文構造分析クラス"""
        self.preprocessor = TextPreprocessor(remove_stopwords=False)  # ストップワード除去しない
    
    def analyze_sentence_structure(self, text: str) -> Dict:
        """
        文構造の総合分析
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            文構造分析結果
        """
        if not text:
            return {}
        
        # 文分割
        sentences = self.preprocessor.split_sentences(text)
        
        if not sentences:
            return {}
        
        analysis_result = {
            'basic_statistics': self._calculate_basic_statistics(sentences),
            'sentence_length_analysis': self._analyze_sentence_lengths(sentences),
            'complexity_analysis': self._analyze_sentence_complexity(sentences),
            'readability_scores': self._calculate_readability_scores(text),
            'structure_patterns': self._analyze_structure_patterns(sentences),
            'detailed_sentences': self._analyze_individual_sentences(sentences)
        }
        
        return analysis_result
    
    def _calculate_basic_statistics(self, sentences: List[str]) -> Dict:
        """
        基本統計情報の計算
        
        Args:
            sentences: 文のリスト
            
        Returns:
            基本統計情報
        """
        total_words = 0
        total_chars = 0
        
        for sentence in sentences:
            words = self.preprocessor.tokenize_words(sentence)
            total_words += len(words)
            total_chars += len(sentence)
        
        basic_stats = {
            'total_sentences': len(sentences),
            'total_words': total_words,
            'total_characters': total_chars,
            'avg_words_per_sentence': round(total_words / len(sentences), 2) if sentences else 0,
            'avg_chars_per_sentence': round(total_chars / len(sentences), 2) if sentences else 0,
            'avg_chars_per_word': round(total_chars / total_words, 2) if total_words > 0 else 0
        }
        
        return basic_stats
    
    def _analyze_sentence_lengths(self, sentences: List[str]) -> Dict:
        """
        文長分析
        
        Args:
            sentences: 文のリスト
            
        Returns:
            文長分析結果
        """
        sentence_lengths = []
        
        for sentence in sentences:
            words = self.preprocessor.tokenize_words(sentence)
            sentence_lengths.append(len(words))
        
        if not sentence_lengths:
            return {}
        
        # 統計計算
        length_stats = {
            'mean_length': round(statistics.mean(sentence_lengths), 2),
            'median_length': statistics.median(sentence_lengths),
            'std_deviation': round(statistics.stdev(sentence_lengths), 2) if len(sentence_lengths) > 1 else 0,
            'min_length': min(sentence_lengths),
            'max_length': max(sentence_lengths),
            'length_distribution': self._categorize_sentence_lengths(sentence_lengths)
        }
        
        return length_stats
    
    def _categorize_sentence_lengths(self, lengths: List[int]) -> Dict:
        """
        文長を カテゴリ別に分類
        
        Args:
            lengths: 文長のリスト
            
        Returns:
            文長分布
        """
        categories = {
            'short': 0,      # 1-10語
            'medium': 0,     # 11-20語
            'long': 0,       # 21-30語
            'very_long': 0   # 31語以上
        }
        
        for length in lengths:
            if length <= 10:
                categories['short'] += 1
            elif length <= 20:
                categories['medium'] += 1
            elif length <= 30:
                categories['long'] += 1
            else:
                categories['very_long'] += 1
        
        total = len(lengths)
        
        # パーセンテージ計算
        distribution = {
            'short_sentences': {
                'count': categories['short'],
                'percentage': round(categories['short'] / total * 100, 1)
            },
            'medium_sentences': {
                'count': categories['medium'],
                'percentage': round(categories['medium'] / total * 100, 1)
            },
            'long_sentences': {
                'count': categories['long'],
                'percentage': round(categories['long'] / total * 100, 1)
            },
            'very_long_sentences': {
                'count': categories['very_long'],
                'percentage': round(categories['very_long'] / total * 100, 1)
            }
        }
        
        return distribution
    
    def _analyze_sentence_complexity(self, sentences: List[str]) -> Dict:
        """
        文の複雑さ分析
        
        Args:
            sentences: 文のリスト
            
        Returns:
            複雑さ分析結果
        """
        complexity_indicators = {
            'complex_sentences': 0,      # 複文・重文
            'simple_sentences': 0,       # 単文
            'coordination_count': 0,     # 等位接続詞
            'subordination_count': 0,    # 従属接続詞
            'relative_clauses': 0,       # 関係節
            'nested_structures': 0       # 入れ子構造
        }
        
        # 複雑さ判定パターン
        coordination_patterns = [
            r'\\b(and|but|or|so|yet|for)\\b',
            r'\\bnot\\s+only\\s+.*\\s+but\\s+also\\b'
        ]
        
        subordination_patterns = [
            r'\\b(because|since|although|though|while|whereas|if|unless|when|before|after|until)\\b',
            r'\\bthat\\s+\\w+\\s+(can|could|will|would|should|may|might|must)\\b'
        ]
        
        relative_patterns = [
            r'\\b(who|which|that|whose|whom)\\s+\\w+\\b',
            r'\\bwhere\\s+\\w+\\b'
        ]
        
        for sentence in sentences:
            words = self.preprocessor.tokenize_words(sentence)
            
            # 基本的な複雑さ判定（語数ベース）
            if len(words) > 20:
                complexity_indicators['complex_sentences'] += 1
            else:
                complexity_indicators['simple_sentences'] += 1
            
            # パターンマッチによる複雑さ判定
            coordination_count = sum(len(re.findall(pattern, sentence, re.IGNORECASE)) 
                                   for pattern in coordination_patterns)
            complexity_indicators['coordination_count'] += coordination_count
            
            subordination_count = sum(len(re.findall(pattern, sentence, re.IGNORECASE)) 
                                    for pattern in subordination_patterns)
            complexity_indicators['subordination_count'] += subordination_count
            
            relative_count = sum(len(re.findall(pattern, sentence, re.IGNORECASE)) 
                               for pattern in relative_patterns)
            complexity_indicators['relative_clauses'] += relative_count
            
            # 入れ子構造の検出（カンマの数で近似）
            comma_count = sentence.count(',')
            if comma_count >= 3:
                complexity_indicators['nested_structures'] += 1
        
        total_sentences = len(sentences)
        
        # 複雑さスコアの計算
        complexity_score = (
            (complexity_indicators['complex_sentences'] / total_sentences * 0.3) +
            (complexity_indicators['subordination_count'] / total_sentences * 0.3) +
            (complexity_indicators['relative_clauses'] / total_sentences * 0.2) +
            (complexity_indicators['coordination_count'] / total_sentences * 0.1) +
            (complexity_indicators['nested_structures'] / total_sentences * 0.1)
        ) * 100
        
        complexity_analysis = {
            'complexity_indicators': complexity_indicators,
            'complexity_ratios': {
                'complex_sentence_ratio': round(complexity_indicators['complex_sentences'] / total_sentences * 100, 1),
                'subordination_ratio': round(complexity_indicators['subordination_count'] / total_sentences * 100, 1),
                'relative_clause_ratio': round(complexity_indicators['relative_clauses'] / total_sentences * 100, 1)
            },
            'overall_complexity_score': round(complexity_score, 2),
            'complexity_level': self._determine_complexity_level(complexity_score)
        }
        
        return complexity_analysis
    
    def _determine_complexity_level(self, score: float) -> str:
        """
        複雑さスコアから難易度レベルを判定
        
        Args:
            score: 複雑さスコア
            
        Returns:
            難易度レベル
        """
        if score < 20:
            return "易"
        elif score < 40:
            return "中"
        elif score < 60:
            return "やや難"
        else:
            return "難"
    
    def _calculate_readability_scores(self, text: str) -> Dict:
        """
        読みやすさ指標の計算
        
        Args:
            text: 対象テキスト
            
        Returns:
            読みやすさ指標
        """
        try:
            readability_scores = {
                'flesch_reading_ease': round(textstat.flesch_reading_ease(text), 2),
                'flesch_kincaid_grade': round(textstat.flesch_kincaid_grade(text), 2),
                'automated_readability_index': round(textstat.automated_readability_index(text), 2),
                'coleman_liau_index': round(textstat.coleman_liau_index(text), 2),
                'gunning_fog': round(textstat.gunning_fog(text), 2),
                'reading_level': self._interpret_readability_score(textstat.flesch_reading_ease(text))
            }
        except Exception as e:
            logger.warning(f"読みやすさ指標の計算に失敗: {e}")
            readability_scores = {
                'flesch_reading_ease': 0,
                'flesch_kincaid_grade': 0,
                'automated_readability_index': 0,
                'coleman_liau_index': 0,
                'gunning_fog': 0,
                'reading_level': '不明'
            }
        
        return readability_scores
    
    def _interpret_readability_score(self, score: float) -> str:
        """
        Flesch Reading Easeスコアを解釈
        
        Args:
            score: Flesch Reading Easeスコア
            
        Returns:
            読みやすさレベル
        """
        if score >= 90:
            return "非常に易しい"
        elif score >= 80:
            return "易しい"
        elif score >= 70:
            return "やや易しい"
        elif score >= 60:
            return "標準"
        elif score >= 50:
            return "やや難しい"
        elif score >= 30:
            return "難しい"
        else:
            return "非常に難しい"
    
    def _analyze_structure_patterns(self, sentences: List[str]) -> Dict:
        """
        文構造パターンの分析
        
        Args:
            sentences: 文のリスト
            
        Returns:
            構造パターン分析結果
        """
        patterns = {
            'questions': 0,           # 疑問文
            'exclamations': 0,        # 感嘆文
            'imperatives': 0,         # 命令文
            'conditionals': 0,        # 条件文
            'passive_voice': 0,       # 受動態
            'direct_speech': 0        # 直接話法
        }
        
        for sentence in sentences:
            # 疑問文
            if re.search(r'\\?$', sentence.strip()) or re.search(r'^(What|When|Where|Why|How|Who|Which)', sentence.strip(), re.IGNORECASE):
                patterns['questions'] += 1
            
            # 感嘆文
            if re.search(r'!$', sentence.strip()):
                patterns['exclamations'] += 1
            
            # 命令文（簡易判定）
            if re.search(r'^(Please|Let|Do not|Don\'t)', sentence.strip(), re.IGNORECASE):
                patterns['imperatives'] += 1
            
            # 条件文
            if re.search(r'\\bif\\s+\\w+', sentence, re.IGNORECASE):
                patterns['conditionals'] += 1
            
            # 受動態
            if re.search(r'\\b(is|are|was|were|be|been)\\s+\\w+ed\\b', sentence, re.IGNORECASE):
                patterns['passive_voice'] += 1
            
            # 直接話法
            if '"' in sentence or "'" in sentence:
                patterns['direct_speech'] += 1
        
        total_sentences = len(sentences)
        pattern_percentages = {
            f"{pattern}_percentage": round(count / total_sentences * 100, 1)
            for pattern, count in patterns.items()
        }
        
        structure_patterns = {
            'pattern_counts': patterns,
            'pattern_percentages': pattern_percentages,
            'dominant_patterns': [
                pattern for pattern, count in patterns.items()
                if count / total_sentences > 0.1  # 10%以上の出現率
            ]
        }
        
        return structure_patterns
    
    def _analyze_individual_sentences(self, sentences: List[str]) -> List[Dict]:
        """
        個別文の詳細分析
        
        Args:
            sentences: 文のリスト
            
        Returns:
            個別文分析結果リスト
        """
        detailed_analysis = []
        
        for i, sentence in enumerate(sentences):
            words = self.preprocessor.tokenize_words(sentence)
            
            sentence_analysis = {
                'sentence_number': i + 1,
                'text': sentence[:100] + "..." if len(sentence) > 100 else sentence,  # 長い場合は省略
                'word_count': len(words),
                'character_count': len(sentence),
                'complexity_level': 'simple' if len(words) <= 15 else 'moderate' if len(words) <= 25 else 'complex',
                'has_subordinate_clause': bool(re.search(r'\\b(because|since|although|though|while|if|when)\\b', sentence, re.IGNORECASE)),
                'has_relative_clause': bool(re.search(r'\\b(who|which|that|whose|whom)\\b', sentence, re.IGNORECASE)),
                'sentence_type': self._classify_sentence_type(sentence)
            }
            
            detailed_analysis.append(sentence_analysis)
        
        return detailed_analysis[:20]  # 最初の20文のみ保存（長文対応）
    
    def _classify_sentence_type(self, sentence: str) -> str:
        """
        文タイプの分類
        
        Args:
            sentence: 対象文
            
        Returns:
            文タイプ
        """
        sentence = sentence.strip()
        
        if sentence.endswith('?'):
            return '疑問文'
        elif sentence.endswith('!'):
            return '感嘆文'
        elif re.search(r'^(Please|Let|Do not)', sentence, re.IGNORECASE):
            return '命令文'
        else:
            return '平叙文'

def main():
    """テスト用メイン関数"""
    analyzer = SentenceAnalyzer()
    
    sample_text = """
    The discovery of quantum mechanics revolutionized our understanding of the physical world. 
    Scientists who study particle physics often encounter phenomena that seem impossible 
    according to classical physics. If we hadn't developed new mathematical frameworks, 
    these observations would have remained unexplained. What makes quantum mechanics so 
    fascinating is its counterintuitive nature.
    """
    
    print("=== Sentence Structure Analysis Test ===")
    print(f"Sample text: {sample_text}")
    print()
    
    # 分析実行
    result = analyzer.analyze_sentence_structure(sample_text)
    
    # 結果表示
    print("Sentence Analysis Results:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()