#!/usr/bin/env python3
"""
テキスト前処理ユーティリティ
既存のvocabulary_analyzer_multi.pyから移植・拡張
"""

import re
import string
from typing import List, Set, Dict, Optional
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import logging

logger = logging.getLogger(__name__)

class TextPreprocessor:
    def __init__(self, remove_stopwords: bool = True, lemmatize: bool = True):
        """
        テキスト前処理クラス
        
        Args:
            remove_stopwords: ストップワード除去フラグ
            lemmatize: レンマ化実行フラグ
        """
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        
        # NLTK データの初期化
        self._download_nltk_data()
        
        if lemmatize:
            self.lemmatizer = WordNetLemmatizer()
        
        if remove_stopwords:
            self.stop_words = set(stopwords.words('english'))
        else:
            self.stop_words = set()
    
    def _download_nltk_data(self):
        """必要なNLTKデータをダウンロード"""
        required_data = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        
        for data_name in required_data:
            try:
                if data_name == 'punkt':
                    nltk.data.find('tokenizers/punkt')
                elif data_name in ['stopwords', 'wordnet']:
                    nltk.data.find(f'corpora/{data_name}')
                else:
                    nltk.data.find(f'taggers/{data_name}')
            except LookupError:
                logger.info(f"Downloading NLTK data: {data_name}")
                nltk.download(data_name)
    
    def clean_text(self, text: str) -> str:
        """
        基本的なテキストクリーニング
        
        Args:
            text: クリーニング対象テキスト
            
        Returns:
            クリーニング済みテキスト
        """
        if not text:
            return ""
        
        # 基本的なクリーニング
        text = re.sub(r'\\n', ' ', text)  # 改行を空白に
        text = re.sub(r'\\t', ' ', text)  # タブを空白に
        text = re.sub(r'\s+', ' ', text)  # 連続空白を単一空白に
        text = text.strip()
        
        return text
    
    def split_sentences(self, text: str) -> List[str]:
        """
        文単位での分割
        
        Args:
            text: 分割対象テキスト
            
        Returns:
            文のリスト
        """
        if not text:
            return []
        
        # テキストクリーニング
        cleaned_text = self.clean_text(text)
        
        # 文分割
        sentences = sent_tokenize(cleaned_text)
        
        # 空文字や短すぎる文を除外
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return sentences
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        単語単位での分割
        
        Args:
            text: 分割対象テキスト
            
        Returns:
            単語のリスト
        """
        if not text:
            return []
        
        # 単語分割
        words = word_tokenize(text)
        
        # 基本的なフィルタリング
        filtered_words = []
        for word in words:
            # 記号のみの語は除外
            if word in string.punctuation:
                continue
            
            # 数字のみの語は除外
            if word.isdigit():
                continue
            
            # 短すぎる語は除外
            if len(word) < 2:
                continue
            
            filtered_words.append(word)
        
        return filtered_words
    
    def normalize_word(self, word: str) -> Optional[str]:
        """
        単語の正規化処理（既存コードから移植）
        
        Args:
            word: 正規化する単語
            
        Returns:
            正規化済み単語（除外対象の場合はNone）
        """
        if not word:
            return None
        
        # 基本的なクリーニング
        word = re.sub(r'[^\\w]', '', word.lower())
        
        # 短すぎる単語や数字のみの単語を除外
        if len(word) < 2 or word.isdigit():
            return None
        
        # ストップワードを除外
        if self.remove_stopwords and word in self.stop_words:
            return None
        
        # レンマ化（原形化）
        if self.lemmatize:
            try:
                lemmatized = self.lemmatizer.lemmatize(word, pos='v')  # 動詞として
                lemmatized = self.lemmatizer.lemmatize(lemmatized, pos='n')  # 名詞として
                return lemmatized
            except Exception as e:
                logger.warning(f"Lemmatization failed for word '{word}': {e}")
                return word
        
        return word
    
    def extract_normalized_words(self, text: str) -> List[str]:
        """
        テキストから正規化済み単語リストを抽出
        
        Args:
            text: 対象テキスト
            
        Returns:
            正規化済み単語のリスト
        """
        if not text:
            return []
        
        # 単語分割
        words = self.tokenize_words(text)
        
        # 正規化
        normalized_words = []
        for word in words:
            normalized = self.normalize_word(word)
            if normalized:
                normalized_words.append(normalized)
        
        return normalized_words
    
    def get_text_statistics(self, text: str) -> Dict:
        """
        テキストの基本統計情報を取得
        
        Args:
            text: 対象テキスト
            
        Returns:
            統計情報辞書
        """
        if not text:
            return {
                'total_characters': 0,
                'total_words': 0,
                'total_sentences': 0,
                'unique_words': 0,
                'avg_word_length': 0.0,
                'avg_sentence_length': 0.0
            }
        
        # 基本情報
        sentences = self.split_sentences(text)
        words = self.tokenize_words(text)
        unique_words = set(words)
        
        # 統計計算
        stats = {
            'total_characters': len(text),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'unique_words': len(unique_words),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0.0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0.0
        }
        
        return stats
    
    def extract_content_words(self, text: str) -> List[str]:
        """
        内容語（ストップワード除外）のみを抽出
        
        Args:
            text: 対象テキスト
            
        Returns:
            内容語のリスト
        """
        # 一時的にストップワード除去を有効化
        original_setting = self.remove_stopwords
        self.remove_stopwords = True
        
        try:
            content_words = self.extract_normalized_words(text)
            return content_words
        finally:
            # 設定を元に戻す
            self.remove_stopwords = original_setting

def main():
    """テスト用メイン関数"""
    preprocessor = TextPreprocessor()
    
    sample_text = """
    The quick brown fox jumps over the lazy dog. This is a sample sentence 
    for testing the text preprocessing functionality. We can analyze various 
    aspects of English text using this tool.
    """
    
    print("=== Text Preprocessing Test ===")
    print(f"Original text: {sample_text}")
    print()
    
    # 文分割テスト
    sentences = preprocessor.split_sentences(sample_text)
    print(f"Sentences ({len(sentences)}):")
    for i, sentence in enumerate(sentences, 1):
        print(f"  {i}. {sentence}")
    print()
    
    # 単語抽出テスト
    words = preprocessor.extract_normalized_words(sample_text)
    print(f"Normalized words ({len(words)}):")
    print(f"  {words}")
    print()
    
    # 統計情報テスト
    stats = preprocessor.get_text_statistics(sample_text)
    print("Text statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()