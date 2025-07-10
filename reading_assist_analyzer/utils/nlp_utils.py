#!/usr/bin/env python3
"""
NLP共通ユーティリティ
自然言語処理の共通機能を提供
"""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

class NLPUtils:
    """NLP共通ユーティリティクラス"""
    
    @staticmethod
    def clean_unicode_text(text: str) -> str:
        """
        Unicodeテキストのクリーニング
        
        Args:
            text: クリーニング対象テキスト
            
        Returns:
            クリーニング済みテキスト
        """
        if not text:
            return ""
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 制御文字の除去
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        # 余分な空白の正規化
        text = re.sub(r'\\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_sentences_advanced(text: str) -> List[str]:
        """
        高度な文分割（略語等を考慮）
        
        Args:
            text: 分割対象テキスト
            
        Returns:
            文のリスト
        """
        if not text:
            return []
        
        # 略語のパターン（Mr., Dr., etc.）
        abbreviations = {
            'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Inc.', 'Ltd.', 'Corp.',
            'vs.', 'etc.', 'i.e.', 'e.g.', 'cf.', 'et al.', 'Ph.D.', 'B.A.',
            'M.A.', 'U.S.', 'U.K.', 'U.N.', 'E.U.', 'No.', 'vol.', 'p.',
            'pp.', 'ch.', 'sec.', 'fig.', 'Jan.', 'Feb.', 'Mar.', 'Apr.',
            'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.'
        }
        
        # 略語を一時的に保護
        protected_text = text
        replacements = {}
        
        for i, abbrev in enumerate(abbreviations):
            if abbrev in protected_text:
                placeholder = f"__ABBREV_{i}__"
                replacements[placeholder] = abbrev
                protected_text = protected_text.replace(abbrev, placeholder)
        
        # 基本的な文分割
        sentences = re.split(r'[.!?]+\\s+', protected_text)
        
        # 略語を復元
        for i, sentence in enumerate(sentences):
            for placeholder, abbrev in replacements.items():
                sentence = sentence.replace(placeholder, abbrev)
            sentences[i] = sentence.strip()
        
        # 空文字や短すぎる文を除外
        sentences = [s for s in sentences if s and len(s.split()) >= 3]
        
        return sentences
    
    @staticmethod
    def detect_language_confidence(text: str) -> Tuple[str, float]:
        """
        言語検出と信頼度の計算
        
        Args:
            text: 検出対象テキスト
            
        Returns:
            (言語コード, 信頼度)のタプル
        """
        try:
            from langdetect import detect, detect_langs
            
            if len(text.strip()) < 10:
                return "unknown", 0.0
            
            # 言語検出
            detected_langs = detect_langs(text)
            
            if detected_langs:
                primary_lang = detected_langs[0]
                return primary_lang.lang, primary_lang.prob
            else:
                return "unknown", 0.0
                
        except ImportError:
            logger.warning("langdetectパッケージがインストールされていません")
            # 簡易的な英語判定
            english_score = NLPUtils.calculate_english_score(text)
            if english_score > 0.7:
                return "en", english_score
            else:
                return "unknown", 0.0
        except Exception as e:
            logger.warning(f"言語検出エラー: {e}")
            return "unknown", 0.0
    
    @staticmethod
    def calculate_english_score(text: str) -> float:
        """
        テキストの英語らしさスコアを計算
        
        Args:
            text: 評価対象テキスト
            
        Returns:
            英語らしさスコア (0.0-1.0)
        """
        if not text:
            return 0.0
        
        # 英語の特徴的なパターン
        english_patterns = [
            r'\\bthe\\b', r'\\band\\b', r'\\bof\\b', r'\\bto\\b', r'\\ba\\b',
            r'\\bin\\b', r'\\bis\\b', r'\\bit\\b', r'\\byou\\b', r'\\bthat\\b',
            r'\\bhe\\b', r'\\bwas\\b', r'\\bfor\\b', r'\\bon\\b', r'\\bare\\b',
            r'\\bwith\\b', r'\\bas\\b', r'\\bI\\b', r'\\bhis\\b', r'\\bthey\\b'
        ]
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        english_word_count = 0
        for pattern in english_patterns:
            english_word_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        # 英語の文字パターン（アルファベットの割合）
        alpha_chars = sum(1 for char in text if char.isalpha())
        total_chars = len(text)
        
        if total_chars == 0:
            alpha_ratio = 0
        else:
            alpha_ratio = alpha_chars / total_chars
        
        # スコア計算
        word_score = min(english_word_count / total_words, 1.0) * 0.7
        char_score = alpha_ratio * 0.3
        
        return word_score + char_score
    
    @staticmethod
    def extract_academic_vocabulary(text: str) -> Set[str]:
        """
        学術語彙の抽出
        
        Args:
            text: 対象テキスト
            
        Returns:
            学術語彙のセット
        """
        # 学術的な接頭辞・接尾辞のパターン
        academic_patterns = [
            r'\\b\\w*ology\\b',  # -ology (生物学、心理学等)
            r'\\b\\w*tion\\b',   # -tion (creation, education等)
            r'\\b\\w*sion\\b',   # -sion (decision, conclusion等)
            r'\\b\\w*ment\\b',   # -ment (development, agreement等)
            r'\\b\\w*ness\\b',   # -ness (effectiveness, awareness等)
            r'\\b\\w*ity\\b',    # -ity (complexity, reality等)
            r'\\b\\w*ism\\b',    # -ism (capitalism, idealism等)
            r'\\b\\w*ical\\b',   # -ical (political, economical等)
            r'\\b\\w*ive\\b',    # -ive (comprehensive, effective等)
            r'\\bpre\\w*\\b',    # pre- (preliminary, previous等)
            r'\\bpost\\w*\\b',   # post- (postmodern, postwar等)
            r'\\binter\\w*\\b',  # inter- (international, interaction等)
            r'\\bmulti\\w*\\b',  # multi- (multimedia, multicultural等)
            r'\\banti\\w*\\b',   # anti- (antibiotic, antisocial等)
        ]
        
        academic_words = set()
        
        for pattern in academic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 5:  # 短すぎる語は除外
                    academic_words.add(match.lower())
        
        return academic_words
    
    @staticmethod
    def calculate_lexical_diversity(words: List[str]) -> Dict[str, float]:
        """
        語彙の多様性指標を計算
        
        Args:
            words: 単語のリスト
            
        Returns:
            多様性指標の辞書
        """
        if not words:
            return {
                'type_token_ratio': 0.0,
                'root_ttr': 0.0,
                'corrected_ttr': 0.0,
                'bilogarithmic_ttr': 0.0
            }
        
        total_words = len(words)
        unique_words = len(set(words))
        
        # Type-Token Ratio (TTR)
        ttr = unique_words / total_words if total_words > 0 else 0
        
        # Root TTR
        root_ttr = unique_words / (total_words ** 0.5) if total_words > 0 else 0
        
        # Corrected TTR
        corrected_ttr = unique_words / (2 * total_words) ** 0.5 if total_words > 0 else 0
        
        # Bilogarithmic TTR
        import math
        if total_words > 1 and unique_words > 1:
            bilog_ttr = math.log(unique_words) / math.log(total_words)
        else:
            bilog_ttr = 0
        
        return {
            'type_token_ratio': round(ttr, 4),
            'root_ttr': round(root_ttr, 4),
            'corrected_ttr': round(corrected_ttr, 4),
            'bilogarithmic_ttr': round(bilog_ttr, 4)
        }
    
    @staticmethod
    def extract_collocations(words: List[str], window_size: int = 2) -> Dict[str, int]:
        """
        コロケーション（連語）の抽出
        
        Args:
            words: 単語のリスト
            window_size: ウィンドウサイズ
            
        Returns:
            コロケーションと出現回数の辞書
        """
        if len(words) < window_size:
            return {}
        
        collocations = {}
        
        for i in range(len(words) - window_size + 1):
            # n-gram生成
            ngram = ' '.join(words[i:i + window_size])
            
            if ngram in collocations:
                collocations[ngram] += 1
            else:
                collocations[ngram] = 1
        
        # 出現回数でソート（頻度の高い順）
        sorted_collocations = dict(
            sorted(collocations.items(), key=lambda x: x[1], reverse=True)
        )
        
        return sorted_collocations
    
    @staticmethod
    def validate_text_quality(text: str) -> Dict[str, any]:
        """
        テキスト品質の検証
        
        Args:
            text: 検証対象テキスト
            
        Returns:
            品質評価結果
        """
        if not text:
            return {
                'is_valid': False,
                'issues': ['テキストが空です'],
                'length_check': False,
                'language_check': False,
                'encoding_check': False
            }
        
        issues = []
        
        # 長さチェック
        length_check = len(text.strip()) >= 50
        if not length_check:
            issues.append('テキストが短すぎます（50文字未満）')
        
        # 言語チェック
        lang, confidence = NLPUtils.detect_language_confidence(text)
        language_check = lang == 'en' and confidence > 0.7
        if not language_check:
            issues.append(f'英語の信頼度が低いです（{lang}: {confidence:.2f}）')
        
        # エンコーディングチェック
        try:
            text.encode('utf-8')
            encoding_check = True
        except UnicodeEncodeError:
            encoding_check = False
            issues.append('文字エンコーディングに問題があります')
        
        # 文字種チェック
        alpha_ratio = sum(1 for char in text if char.isalpha()) / len(text)
        if alpha_ratio < 0.5:
            issues.append('アルファベット文字の割合が低すぎます')
        
        is_valid = length_check and language_check and encoding_check
        
        return {
            'is_valid': is_valid,
            'issues': issues,
            'length_check': length_check,
            'language_check': language_check,
            'encoding_check': encoding_check,
            'language_detected': lang,
            'language_confidence': confidence,
            'alphabet_ratio': round(alpha_ratio, 3)
        }

def main():
    """テスト用メイン関数"""
    sample_text = """
    The development of artificial intelligence has fundamentally transformed 
    the technological landscape. Researchers who work in this interdisciplinary 
    field often encounter complex methodological challenges that require 
    innovative solutions and comprehensive analysis.
    """
    
    print("=== NLP Utils Test ===")
    
    # テキスト品質検証
    quality = NLPUtils.validate_text_quality(sample_text)
    print(f"Text Quality: {quality}")
    print()
    
    # 言語検出
    lang, confidence = NLPUtils.detect_language_confidence(sample_text)
    print(f"Language: {lang} (confidence: {confidence:.3f})")
    print()
    
    # 学術語彙抽出
    academic_words = NLPUtils.extract_academic_vocabulary(sample_text)
    print(f"Academic vocabulary: {academic_words}")
    print()
    
    # 語彙多様性
    words = sample_text.split()
    diversity = NLPUtils.calculate_lexical_diversity(words)
    print(f"Lexical diversity: {diversity}")
    print()
    
    # コロケーション抽出
    collocations = NLPUtils.extract_collocations(words, 2)
    print(f"Top collocations: {dict(list(collocations.items())[:5])}")

if __name__ == "__main__":
    main()