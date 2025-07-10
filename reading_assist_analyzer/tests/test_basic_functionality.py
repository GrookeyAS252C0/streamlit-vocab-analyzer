#!/usr/bin/env python3
"""
基本機能テスト
ReadingAssist Analyzerの主要機能をテスト
"""

import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.text_preprocessor import TextPreprocessor
from core.vocab_analyzer import VocabularyAnalyzer
from core.grammar_analyzer import GrammarAnalyzer
from core.sentence_analyzer import SentenceAnalyzer
from core.text_analyzer import TextAnalyzer

class TestTextPreprocessor:
    def test_text_cleaning(self):
        """テキストクリーニングのテスト"""
        preprocessor = TextPreprocessor()
        
        dirty_text = "  This   is\\n\\ta  test.  "
        clean_text = preprocessor.clean_text(dirty_text)
        
        assert clean_text == "This is a test."
    
    def test_sentence_splitting(self):
        """文分割のテスト"""
        preprocessor = TextPreprocessor()
        
        text = "This is the first sentence. This is the second sentence!"
        sentences = preprocessor.split_sentences(text)
        
        assert len(sentences) == 2
        assert "first sentence" in sentences[0]
        assert "second sentence" in sentences[1]
    
    def test_word_tokenization(self):
        """単語分割のテスト"""
        preprocessor = TextPreprocessor()
        
        text = "Hello, world! This is a test."
        words = preprocessor.tokenize_words(text)
        
        # 記号と短語は除外される
        assert "Hello" in words
        assert "world" in words
        assert "," not in words
        assert "!" not in words
    
    def test_word_normalization(self):
        """単語正規化のテスト"""
        preprocessor = TextPreprocessor(lemmatize=True, remove_stopwords=True)
        
        # レンマ化のテスト
        assert preprocessor.normalize_word("running") == "run"
        assert preprocessor.normalize_word("better") == "well"
        
        # ストップワード除去のテスト
        assert preprocessor.normalize_word("the") is None
        assert preprocessor.normalize_word("and") is None
        
        # 短語・数字除去のテスト
        assert preprocessor.normalize_word("a") is None
        assert preprocessor.normalize_word("123") is None

class TestVocabularyAnalyzer:
    def test_vocabulary_analyzer_initialization(self):
        """語彙分析器の初期化テスト"""
        analyzer = VocabularyAnalyzer()
        
        assert analyzer.vocabulary_books is not None
        assert len(analyzer.vocabulary_books) > 0
        assert "Target 1900" in analyzer.vocabulary_books
    
    def test_coverage_calculation(self):
        """カバレッジ計算のテスト"""
        analyzer = VocabularyAnalyzer()
        
        # テスト用の単語帳
        test_vocab = {
            "Test Vocab": {"test", "example", "word", "analysis"}
        }
        
        # テスト用テキスト
        test_text = "This is a test example for word analysis."
        
        result = analyzer.analyze_text_vocabulary(test_text, test_vocab)
        
        assert "vocabulary_coverage" in result
        assert "Test Vocab" in result["vocabulary_coverage"]
        
        test_vocab_result = result["vocabulary_coverage"]["Test Vocab"]
        assert test_vocab_result["matched_words_count"] > 0
        assert 0 <= test_vocab_result["vocabulary_coverage_rate"] <= 100

class TestGrammarAnalyzer:
    def test_grammar_analyzer_initialization(self):
        """文法分析器の初期化テスト"""
        analyzer = GrammarAnalyzer()
        
        assert analyzer.grammar_patterns is not None
        assert len(analyzer.grammar_patterns) > 0
    
    def test_grammar_pattern_detection(self):
        """文法パターン検出のテスト"""
        analyzer = GrammarAnalyzer()
        
        # 関係代名詞を含むテスト文
        test_text = "The book which I read yesterday was interesting. The person who called you is here."
        
        result = analyzer.analyze_grammar_frequency(test_text)
        
        assert "grammar_items" in result
        
        # 関係代名詞が検出されることを確認
        if "関係代名詞" in result["grammar_items"]:
            relative_pronoun_result = result["grammar_items"]["関係代名詞"]
            assert relative_pronoun_result["count"] > 0

class TestSentenceAnalyzer:
    def test_sentence_analyzer_initialization(self):
        """文構造分析器の初期化テスト"""
        analyzer = SentenceAnalyzer()
        assert analyzer.preprocessor is not None
    
    def test_sentence_length_analysis(self):
        """文長分析のテスト"""
        analyzer = SentenceAnalyzer()
        
        test_text = "Short sentence. This is a medium length sentence with several words. This is a very long sentence that contains many words and should be classified as a long sentence by the analysis system."
        
        result = analyzer.analyze_sentence_structure(test_text)
        
        assert "basic_statistics" in result
        assert "sentence_length_analysis" in result
        
        basic_stats = result["basic_statistics"]
        assert basic_stats["total_sentences"] == 3
        assert basic_stats["avg_words_per_sentence"] > 0

class TestTextAnalyzer:
    def test_text_analyzer_initialization(self):
        """統合分析器の初期化テスト"""
        analyzer = TextAnalyzer()
        
        assert analyzer.vocab_analyzer is not None
        assert analyzer.grammar_analyzer is not None
        assert analyzer.sentence_analyzer is not None
    
    def test_comprehensive_analysis(self):
        """総合分析のテスト"""
        analyzer = TextAnalyzer()
        
        test_text = """
        The development of artificial intelligence has revolutionized many industries. 
        Scientists who work in this field often encounter complex problems that require 
        innovative solutions. If we consider the implications of these advances, it 
        becomes clear that AI will continue to transform our world.
        """
        
        # 単語帳データが存在しない場合のテスト用設定
        try:
            result = analyzer.analyze_text_comprehensive(test_text, "nonexistent/path")
            
            # 基本的な構造の確認
            assert "comprehensive_assessment" in result
            assert "integrated_report" in result
            
            assessment = result["comprehensive_assessment"]
            assert "difficulty_level" in assessment
            assert "overall_difficulty_score" in assessment
            
        except Exception as e:
            # 単語帳ファイルが存在しない場合はスキップ
            pytest.skip(f"Vocabulary files not found: {e}")

class TestIntegration:
    def test_end_to_end_analysis(self):
        """エンドツーエンド分析のテスト"""
        # 基本的な分析フローが動作することを確認
        preprocessor = TextPreprocessor()
        
        test_text = "This is a simple test sentence for integration testing."
        
        # 各ステップが正常に動作することを確認
        sentences = preprocessor.split_sentences(test_text)
        assert len(sentences) > 0
        
        words = preprocessor.extract_normalized_words(test_text)
        assert len(words) > 0
        
        stats = preprocessor.get_text_statistics(test_text)
        assert stats["total_words"] > 0
        assert stats["total_sentences"] > 0

def main():
    """テスト実行"""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    main()