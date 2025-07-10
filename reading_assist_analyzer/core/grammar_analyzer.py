#!/usr/bin/env python3
"""
文法項目分析エンジン
英文の文法構造を分析し、各文法項目の出現頻度と難易度を評価
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class GrammarAnalyzer:
    def __init__(self, grammar_rules_path: str = "config/grammar_rules.json"):
        """
        文法分析クラス
        
        Args:
            grammar_rules_path: 文法ルールファイルのパス
        """
        self.grammar_rules_path = Path(grammar_rules_path)
        self.grammar_patterns = {}
        self.difficulty_weights = {}
        self.importance_weights = {}
        
        self._load_grammar_rules()
    
    def _load_grammar_rules(self):
        """文法ルールを読み込み"""
        try:
            if self.grammar_rules_path.exists():
                with open(self.grammar_rules_path, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                self.grammar_patterns = rules_data.get('grammar_patterns', {})
                self.difficulty_weights = rules_data.get('difficulty_weights', {
                    'basic': 1.0, 'intermediate': 1.5, 'advanced': 2.0
                })
                self.importance_weights = rules_data.get('importance_weights', {
                    'low': 0.5, 'medium': 1.0, 'high': 1.5
                })
                
                logger.info(f"文法ルールを読み込みました: {len(self.grammar_patterns)}項目")
            else:
                logger.warning(f"文法ルールファイルが見つかりません: {self.grammar_rules_path}")
                self._create_default_rules()
                
        except Exception as e:
            logger.error(f"文法ルール読み込みエラー: {e}")
            self._create_default_rules()
    
    def _create_default_rules(self):
        """デフォルト文法ルールを作成"""
        self.grammar_patterns = {
            '関係代名詞': {
                'patterns': [r'\\b(who|which|that|whose|whom)\\b'],
                'description': '関係代名詞の使用',
                'difficulty_level': 'intermediate',
                'importance': 'high'
            },
            '完了形': {
                'patterns': [r'\\bhave\\s+\\w+ed\\b', r'\\bhas\\s+\\w+ed\\b', r'\\bhad\\s+\\w+ed\\b'],
                'description': '完了形の構文',
                'difficulty_level': 'intermediate',
                'importance': 'high'
            },
            '受動態': {
                'patterns': [r'\\b(is|are|was|were|be|been)\\s+\\w+ed\\b'],
                'description': '受動態の構文',
                'difficulty_level': 'intermediate',
                'importance': 'high'
            }
        }
        
        self.difficulty_weights = {'basic': 1.0, 'intermediate': 1.5, 'advanced': 2.0}
        self.importance_weights = {'low': 0.5, 'medium': 1.0, 'high': 1.5}
    
    def analyze_grammar_frequency(self, text: str) -> Dict:
        """
        文法項目の出現頻度を分析
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            文法項目分析結果
        """
        if not text:
            return {}
        
        # テキストの前処理
        text = self._preprocess_text(text)
        
        grammar_analysis = {
            'grammar_items': {},
            'summary': {},
            'difficulty_analysis': {},
            'text_statistics': {
                'total_characters': len(text),
                'total_words': len(text.split())
            }
        }
        
        # 各文法項目の分析
        total_matches = 0
        difficulty_scores = []
        
        for grammar_name, grammar_info in self.grammar_patterns.items():
            matches = self._find_grammar_matches(text, grammar_info['patterns'])
            
            if matches:
                total_matches += len(matches)
                
                # 難易度スコア計算
                difficulty_level = grammar_info.get('difficulty_level', 'basic')
                importance = grammar_info.get('importance', 'medium')
                
                difficulty_score = (
                    self.difficulty_weights.get(difficulty_level, 1.0) * 
                    self.importance_weights.get(importance, 1.0) * 
                    len(matches)
                )
                difficulty_scores.append(difficulty_score)
                
                grammar_analysis['grammar_items'][grammar_name] = {
                    'count': len(matches),
                    'frequency_per_100_words': round(len(matches) / len(text.split()) * 100, 2),
                    'matches': matches[:10],  # 最初の10個の例のみ保存
                    'difficulty_level': difficulty_level,
                    'importance': importance,
                    'difficulty_score': round(difficulty_score, 2),
                    'description': grammar_info.get('description', '')
                }
        
        # サマリー統計の計算
        word_count = len(text.split())
        grammar_analysis['summary'] = {
            'total_grammar_items': len([item for item in grammar_analysis['grammar_items'].values() if item['count'] > 0]),
            'total_grammar_occurrences': total_matches,
            'grammar_density': round(total_matches / word_count * 100, 2) if word_count > 0 else 0,
            'average_difficulty_score': round(sum(difficulty_scores) / len(difficulty_scores), 2) if difficulty_scores else 0,
            'complexity_level': self._determine_complexity_level(difficulty_scores)
        }
        
        # 難易度レベル別分析
        grammar_analysis['difficulty_analysis'] = self._analyze_difficulty_distribution(
            grammar_analysis['grammar_items']
        )
        
        return grammar_analysis
    
    def _preprocess_text(self, text: str) -> str:
        """テキストの前処理"""
        # 基本的なクリーニング
        text = re.sub(r'\\s+', ' ', text)  # 複数空白を単一空白に
        text = text.strip()
        return text
    
    def _find_grammar_matches(self, text: str, patterns: List[str]) -> List[str]:
        """
        指定されたパターンでテキストから文法項目を検出
        
        Args:
            text: 検索対象テキスト
            patterns: 正規表現パターンのリスト
            
        Returns:
            マッチした文字列のリスト
        """
        matches = []
        
        for pattern in patterns:
            try:
                found_matches = re.findall(pattern, text, re.IGNORECASE)
                
                # マッチ結果の正規化
                if isinstance(found_matches[0], tuple) if found_matches else False:
                    # タプルの場合は最初の要素を使用
                    matches.extend([match[0] for match in found_matches])
                else:
                    matches.extend(found_matches)
                    
            except re.error as e:
                logger.warning(f"正規表現エラー: {pattern} - {e}")
                continue
        
        return matches
    
    def _determine_complexity_level(self, difficulty_scores: List[float]) -> str:
        """
        難易度スコアから文章の複雑度レベルを判定
        
        Args:
            difficulty_scores: 難易度スコアのリスト
            
        Returns:
            複雑度レベル
        """
        if not difficulty_scores:
            return "基礎"
        
        avg_score = sum(difficulty_scores) / len(difficulty_scores)
        
        if avg_score < 1.0:
            return "基礎"
        elif avg_score < 2.0:
            return "中級"
        else:
            return "上級"
    
    def _analyze_difficulty_distribution(self, grammar_items: Dict) -> Dict:
        """
        難易度レベル別の分布を分析
        
        Args:
            grammar_items: 文法項目分析結果
            
        Returns:
            難易度分布分析結果
        """
        distribution = {
            'basic': {'count': 0, 'items': []},
            'intermediate': {'count': 0, 'items': []},
            'advanced': {'count': 0, 'items': []}
        }
        
        for grammar_name, data in grammar_items.items():
            if data['count'] > 0:
                level = data['difficulty_level']
                if level in distribution:
                    distribution[level]['count'] += data['count']
                    distribution[level]['items'].append({
                        'name': grammar_name,
                        'count': data['count'],
                        'frequency': data['frequency_per_100_words']
                    })
        
        # パーセンテージ計算
        total_occurrences = sum(level_data['count'] for level_data in distribution.values())
        
        for level, data in distribution.items():
            data['percentage'] = round(data['count'] / total_occurrences * 100, 1) if total_occurrences > 0 else 0
        
        return distribution
    
    def generate_grammar_report(self, grammar_analysis: Dict) -> Dict:
        """
        文法分析レポートを生成
        
        Args:
            grammar_analysis: 文法分析結果
            
        Returns:
            文法レポート
        """
        if not grammar_analysis:
            return {}
        
        summary = grammar_analysis.get('summary', {})
        difficulty_analysis = grammar_analysis.get('difficulty_analysis', {})
        
        # 推奨事項の生成
        recommendations = []
        
        complexity_level = summary.get('complexity_level', '基礎')
        grammar_density = summary.get('grammar_density', 0)
        
        if grammar_density < 5:
            recommendations.append("文法項目の使用頻度が低く、比較的読みやすい文章です。")
        elif grammar_density < 15:
            recommendations.append("適度な文法項目が使用されており、標準的な難易度です。")
        else:
            recommendations.append("文法項目の使用頻度が高く、やや高難度の文章です。")
        
        if complexity_level == "上級":
            recommendations.append("高度な文法項目が多く含まれています。段階的な学習をお勧めします。")
        elif complexity_level == "中級":
            recommendations.append("中級レベルの文法項目が中心です。継続的な学習で理解度が向上するでしょう。")
        else:
            recommendations.append("基礎的な文法項目が中心で、学習しやすい内容です。")
        
        # 重点学習項目の特定
        high_frequency_items = [
            name for name, data in grammar_analysis.get('grammar_items', {}).items()
            if data['count'] > 0 and data['frequency_per_100_words'] > 2.0
        ]
        
        if high_frequency_items:
            recommendations.append(f"重点学習項目: {', '.join(high_frequency_items)}")
        
        report = {
            'overall_assessment': {
                'complexity_level': complexity_level,
                'grammar_density': grammar_density,
                'readability': 'easy' if grammar_density < 10 else 'moderate' if grammar_density < 20 else 'difficult'
            },
            'key_findings': {
                'most_frequent_grammar': self._get_most_frequent_grammar(grammar_analysis.get('grammar_items', {})),
                'difficulty_distribution': difficulty_analysis,
                'study_focus_areas': high_frequency_items
            },
            'recommendations': recommendations
        }
        
        return report
    
    def _get_most_frequent_grammar(self, grammar_items: Dict) -> List[Dict]:
        """
        最も頻出する文法項目を取得
        
        Args:
            grammar_items: 文法項目分析結果
            
        Returns:
            頻出文法項目リスト
        """
        items = [
            {
                'name': name,
                'count': data['count'],
                'frequency': data['frequency_per_100_words']
            }
            for name, data in grammar_items.items()
            if data['count'] > 0
        ]
        
        # 出現回数でソート
        items.sort(key=lambda x: x['count'], reverse=True)
        
        return items[:5]  # 上位5項目

def main():
    """テスト用メイン関数"""
    analyzer = GrammarAnalyzer()
    
    sample_text = """
    The scientist who discovered this phenomenon has been studying quantum mechanics 
    for over twenty years. If he had not persevered through countless failed experiments, 
    this breakthrough would never have been achieved. The research, which was conducted 
    in collaboration with international teams, demonstrates the potential for 
    revolutionary applications in technology.
    """
    
    print("=== Grammar Analysis Test ===")
    print(f"Sample text: {sample_text}")
    print()
    
    # 分析実行
    result = analyzer.analyze_grammar_frequency(sample_text)
    
    # 結果表示
    print("Grammar Analysis Results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # レポート生成
    report = analyzer.generate_grammar_report(result)
    print("\\nGrammar Report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()