#!/usr/bin/env python3
"""
統合テキスト分析エンジン
語彙・文法・文構造分析を統合し、総合的な読解難易度を判定
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import datetime

from core.vocab_analyzer import VocabularyAnalyzer
from core.grammar_analyzer import GrammarAnalyzer
from core.sentence_analyzer import SentenceAnalyzer
from utils.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)

class TextAnalyzer:
    def __init__(self, config: Dict = None):
        """
        統合テキスト分析クラス
        
        Args:
            config: 設定辞書
        """
        self.config = config or {}
        
        # 各分析エンジンの初期化
        self.vocab_analyzer = VocabularyAnalyzer(self.config.get('vocabulary', {}))
        self.grammar_analyzer = GrammarAnalyzer(
            self.config.get('grammar_rules_path', 'config/grammar_rules.json')
        )
        self.sentence_analyzer = SentenceAnalyzer()
        self.preprocessor = TextPreprocessor()
        
    def analyze_text_comprehensive(
        self, 
        text: str, 
        vocabulary_data_path: str = "data/vocabulary_books/"
    ) -> Dict:
        """
        テキストの総合分析を実行
        
        Args:
            text: 分析対象テキスト
            vocabulary_data_path: 単語帳データディレクトリパス
            
        Returns:
            総合分析結果
        """
        if not text or not text.strip():
            logger.warning("分析対象テキストが空です")
            return {}
        
        logger.info("統合テキスト分析を開始します")
        
        # 基本的なテキスト統計
        basic_stats = self.preprocessor.get_text_statistics(text)
        
        # 1. 語彙分析
        logger.info("語彙分析を実行中...")
        vocabulary_sets = self.vocab_analyzer.load_vocabulary_lists(vocabulary_data_path)
        vocab_analysis = self.vocab_analyzer.analyze_text_vocabulary(text, vocabulary_sets)
        
        # 2. 文法分析
        logger.info("文法分析を実行中...")
        grammar_analysis = self.grammar_analyzer.analyze_grammar_frequency(text)
        
        # 3. 文構造分析
        logger.info("文構造分析を実行中...")
        sentence_analysis = self.sentence_analyzer.analyze_sentence_structure(text)
        
        # 4. 総合評価の計算
        logger.info("総合評価を計算中...")
        comprehensive_assessment = self._calculate_comprehensive_assessment(
            vocab_analysis, grammar_analysis, sentence_analysis
        )
        
        # 5. 統合レポートの生成
        integrated_report = self._generate_integrated_report(
            vocab_analysis, grammar_analysis, sentence_analysis, comprehensive_assessment
        )
        
        # 総合分析結果
        comprehensive_result = {
            'metadata': {
                'analysis_timestamp': datetime.datetime.now().isoformat(),
                'text_length': len(text),
                'analysis_version': '1.0.0'
            },
            'basic_statistics': basic_stats,
            'vocabulary_analysis': vocab_analysis,
            'grammar_analysis': grammar_analysis,
            'sentence_analysis': sentence_analysis,
            'comprehensive_assessment': comprehensive_assessment,
            'integrated_report': integrated_report
        }
        
        logger.info("統合テキスト分析が完了しました")
        return comprehensive_result
    
    def _calculate_comprehensive_assessment(
        self, 
        vocab_analysis: Dict, 
        grammar_analysis: Dict, 
        sentence_analysis: Dict
    ) -> Dict:
        """
        総合評価の計算
        
        Args:
            vocab_analysis: 語彙分析結果
            grammar_analysis: 文法分析結果
            sentence_analysis: 文構造分析結果
            
        Returns:
            総合評価結果
        """
        # 各分析結果からスコアを抽出
        vocab_score = self._extract_vocabulary_score(vocab_analysis)
        grammar_score = self._extract_grammar_score(grammar_analysis)
        sentence_score = self._extract_sentence_score(sentence_analysis)
        
        # 重み付き総合スコア計算
        weights = {
            'vocabulary': 0.4,   # 語彙の重要度: 40%
            'grammar': 0.35,     # 文法の重要度: 35%
            'sentence': 0.25     # 文構造の重要度: 25%
        }
        
        overall_score = (
            vocab_score * weights['vocabulary'] +
            grammar_score * weights['grammar'] +
            sentence_score * weights['sentence']
        )
        
        # 難易度レベルの判定
        difficulty_level = self._determine_overall_difficulty(overall_score)
        
        # 読解時間の推定
        estimated_reading_time = self._estimate_reading_time(
            sentence_analysis.get('basic_statistics', {}),
            overall_score
        )
        
        comprehensive_assessment = {
            'component_scores': {
                'vocabulary_score': round(vocab_score, 2),
                'grammar_score': round(grammar_score, 2),
                'sentence_score': round(sentence_score, 2)
            },
            'overall_difficulty_score': round(overall_score, 2),
            'difficulty_level': difficulty_level,
            'reading_level': self._map_difficulty_to_reading_level(difficulty_level),
            'estimated_reading_time_minutes': estimated_reading_time,
            'score_breakdown': {
                'vocabulary_contribution': round(vocab_score * weights['vocabulary'], 2),
                'grammar_contribution': round(grammar_score * weights['grammar'], 2),
                'sentence_contribution': round(sentence_score * weights['sentence'], 2)
            }
        }
        
        return comprehensive_assessment
    
    def _extract_vocabulary_score(self, vocab_analysis: Dict) -> float:
        """語彙分析からスコアを抽出"""
        summary = vocab_analysis.get('summary', {})
        
        # 平均語彙カバレッジ率を基準にスコア計算
        avg_coverage = summary.get('average_vocabulary_coverage_rate', 0)
        
        # カバレッジ率が高いほど難易度は低い（読みやすい）
        if avg_coverage >= 70:
            return 20  # 易しい
        elif avg_coverage >= 50:
            return 40  # やや易しい
        elif avg_coverage >= 30:
            return 60  # 中程度
        elif avg_coverage >= 15:
            return 80  # やや難しい
        else:
            return 100  # 難しい
    
    def _extract_grammar_score(self, grammar_analysis: Dict) -> float:
        """文法分析からスコアを抽出"""
        summary = grammar_analysis.get('summary', {})
        
        # 文法密度と複雑度スコアを基準に計算
        grammar_density = summary.get('grammar_density', 0)
        avg_difficulty = summary.get('average_difficulty_score', 0)
        
        # 文法項目の使用頻度と難易度に基づくスコア
        density_score = min(grammar_density * 2, 50)  # 密度による加点（最大50点）
        difficulty_score = min(avg_difficulty * 10, 50)  # 難易度による加点（最大50点）
        
        return density_score + difficulty_score
    
    def _extract_sentence_score(self, sentence_analysis: Dict) -> float:
        """文構造分析からスコアを抽出"""
        basic_stats = sentence_analysis.get('basic_statistics', {})
        complexity = sentence_analysis.get('complexity_analysis', {})
        readability = sentence_analysis.get('readability_scores', {})
        
        # 平均文長によるスコア
        avg_length = basic_stats.get('avg_words_per_sentence', 0)
        length_score = min(avg_length * 2, 40)  # 文長による加点（最大40点）
        
        # 複雑さスコア
        complexity_score = complexity.get('overall_complexity_score', 0)
        
        # 読みやすさスコア（Flesch Reading Easeを逆転）
        flesch_score = readability.get('flesch_reading_ease', 50)
        readability_score = max(0, 100 - flesch_score)
        
        # 総合文構造スコア
        return (length_score + complexity_score + readability_score * 0.3) / 2
    
    def _determine_overall_difficulty(self, score: float) -> str:
        """総合スコアから難易度レベルを判定"""
        if score < 25:
            return "易"
        elif score < 45:
            return "やや易"
        elif score < 65:
            return "中"
        elif score < 85:
            return "やや難"
        else:
            return "難"
    
    def _map_difficulty_to_reading_level(self, difficulty: str) -> str:
        """難易度レベルを読解レベルにマッピング"""
        mapping = {
            "易": "中学レベル",
            "やや易": "高校基礎レベル",
            "中": "高校標準レベル",
            "やや難": "大学受験レベル",
            "難": "大学・専門レベル"
        }
        return mapping.get(difficulty, "不明")
    
    def _estimate_reading_time(self, basic_stats: Dict, difficulty_score: float) -> int:
        """読解時間を推定"""
        total_words = basic_stats.get('total_words', 0)
        
        # 基本読解速度（語/分）: 難易度により調整
        if difficulty_score < 25:
            reading_speed = 200  # 易しい文章
        elif difficulty_score < 45:
            reading_speed = 150  # やや易しい文章
        elif difficulty_score < 65:
            reading_speed = 120  # 中程度の文章
        elif difficulty_score < 85:
            reading_speed = 100  # やや難しい文章
        else:
            reading_speed = 80   # 難しい文章
        
        # 推定読解時間（分）
        estimated_time = max(1, round(total_words / reading_speed))
        
        return estimated_time
    
    def _generate_integrated_report(
        self, 
        vocab_analysis: Dict, 
        grammar_analysis: Dict, 
        sentence_analysis: Dict,
        comprehensive_assessment: Dict
    ) -> Dict:
        """統合レポートの生成"""
        
        # 各分析からの推奨事項を統合
        vocab_recommendations = self.vocab_analyzer.generate_recommendations(vocab_analysis)
        grammar_report = self.grammar_analyzer.generate_grammar_report(grammar_analysis)
        
        # 総合的な学習推奨事項
        study_recommendations = self._generate_study_recommendations(
            vocab_analysis, grammar_analysis, sentence_analysis, comprehensive_assessment
        )
        
        integrated_report = {
            'executive_summary': {
                'overall_assessment': comprehensive_assessment['difficulty_level'],
                'reading_level': comprehensive_assessment['reading_level'],
                'estimated_reading_time': comprehensive_assessment['estimated_reading_time_minutes'],
                'key_challenges': self._identify_key_challenges(vocab_analysis, grammar_analysis, sentence_analysis)
            },
            'detailed_findings': {
                'vocabulary_insights': {
                    'best_vocabulary_book': vocab_analysis.get('summary', {}).get('best_coverage_book', {}),
                    'coverage_summary': vocab_analysis.get('summary', {}),
                    'recommendations': vocab_recommendations
                },
                'grammar_insights': {
                    'complexity_level': grammar_analysis.get('summary', {}).get('complexity_level', '不明'),
                    'most_frequent_items': grammar_report.get('key_findings', {}).get('most_frequent_grammar', []),
                    'recommendations': grammar_report.get('recommendations', [])
                },
                'structure_insights': {
                    'sentence_complexity': sentence_analysis.get('complexity_analysis', {}).get('complexity_level', '不明'),
                    'readability_level': sentence_analysis.get('readability_scores', {}).get('reading_level', '不明'),
                    'dominant_patterns': sentence_analysis.get('structure_patterns', {}).get('dominant_patterns', [])
                }
            },
            'study_recommendations': study_recommendations,
            'action_plan': self._create_action_plan(comprehensive_assessment, study_recommendations)
        }
        
        return integrated_report
    
    def _identify_key_challenges(
        self, 
        vocab_analysis: Dict, 
        grammar_analysis: Dict, 
        sentence_analysis: Dict
    ) -> List[str]:
        """主要な学習課題を特定"""
        challenges = []
        
        # 語彙レベルの課題
        vocab_summary = vocab_analysis.get('summary', {})
        avg_coverage = vocab_summary.get('average_vocabulary_coverage_rate', 0)
        
        if avg_coverage < 30:
            challenges.append("語彙力不足: 基礎単語の習得が必要")
        elif avg_coverage < 50:
            challenges.append("語彙力やや不足: 中級単語の強化が必要")
        
        # 文法レベルの課題
        grammar_summary = grammar_analysis.get('summary', {})
        complexity_level = grammar_summary.get('complexity_level', '')
        
        if complexity_level in ['上級', '中級']:
            challenges.append(f"文法構造が複雑: {complexity_level}レベルの文法項目が多用")
        
        # 文構造レベルの課題
        sentence_complexity = sentence_analysis.get('complexity_analysis', {})
        complexity_score = sentence_complexity.get('overall_complexity_score', 0)
        
        if complexity_score > 50:
            challenges.append("文構造が複雑: 長文・複文の理解力向上が必要")
        
        return challenges if challenges else ["特に大きな課題は見つかりませんでした"]
    
    def _generate_study_recommendations(
        self, 
        vocab_analysis: Dict, 
        grammar_analysis: Dict, 
        sentence_analysis: Dict,
        comprehensive_assessment: Dict
    ) -> Dict:
        """学習推奨事項の生成"""
        difficulty_level = comprehensive_assessment['difficulty_level']
        
        recommendations = {
            'priority_areas': [],
            'vocabulary_study': [],
            'grammar_study': [],
            'reading_strategy': []
        }
        
        # 優先学習分野の特定
        scores = comprehensive_assessment['component_scores']
        if scores['vocabulary_score'] > 70:
            recommendations['priority_areas'].append("語彙力強化")
        if scores['grammar_score'] > 70:
            recommendations['priority_areas'].append("文法理解")
        if scores['sentence_score'] > 70:
            recommendations['priority_areas'].append("文構造把握")
        
        # 語彙学習推奨
        best_book = vocab_analysis.get('summary', {}).get('best_coverage_book', {})
        if best_book:
            recommendations['vocabulary_study'].append(f"推奨単語帳: {best_book.get('name', '不明')}")
        
        avg_coverage = vocab_analysis.get('summary', {}).get('average_vocabulary_coverage_rate', 0)
        if avg_coverage < 50:
            recommendations['vocabulary_study'].append("基礎語彙の体系的学習")
            recommendations['vocabulary_study'].append("語根・接頭辞・接尾辞の学習")
        
        # 文法学習推奨
        grammar_items = grammar_analysis.get('grammar_items', {})
        high_freq_grammar = [
            name for name, data in grammar_items.items() 
            if data.get('count', 0) > 0 and data.get('frequency_per_100_words', 0) > 2.0
        ]
        
        if high_freq_grammar:
            recommendations['grammar_study'].extend([f"{item}の集中学習" for item in high_freq_grammar[:3]])
        
        # 読解戦略推奨
        if difficulty_level in ['やや難', '難']:
            recommendations['reading_strategy'].extend([
                "段落ごとの要約練習",
                "未知語の推測練習",
                "文構造の視覚化練習"
            ])
        else:
            recommendations['reading_strategy'].extend([
                "音読による流暢性向上",
                "多読による慣用表現習得"
            ])
        
        return recommendations
    
    def _create_action_plan(self, comprehensive_assessment: Dict, study_recommendations: Dict) -> Dict:
        """具体的な行動計画の作成"""
        difficulty_level = comprehensive_assessment['difficulty_level']
        estimated_time = comprehensive_assessment['estimated_reading_time_minutes']
        
        # 学習期間の推定
        if difficulty_level in ['易', 'やや易']:
            study_period = "2-4週間"
            daily_study_time = "30-45分"
        elif difficulty_level == '中':
            study_period = "4-6週間"
            daily_study_time = "45-60分"
        else:
            study_period = "6-8週間"
            daily_study_time = "60-90分"
        
        action_plan = {
            'study_schedule': {
                'recommended_study_period': study_period,
                'daily_study_time': daily_study_time,
                'weekly_goals': self._create_weekly_goals(study_recommendations)
            },
            'immediate_actions': [
                f"推奨単語帳での語彙学習開始",
                f"文法項目の体系的復習",
                f"同レベル文章での多読練習"
            ],
            'progress_tracking': {
                'vocabulary_milestones': ["週次単語テスト", "カバレッジ率測定"],
                'grammar_milestones': ["文法項目別理解度チェック"],
                'reading_milestones': ["読解速度測定", "理解度テスト"]
            }
        }
        
        return action_plan
    
    def _create_weekly_goals(self, study_recommendations: Dict) -> List[str]:
        """週次目標の作成"""
        goals = []
        
        priority_areas = study_recommendations.get('priority_areas', [])
        
        if "語彙力強化" in priority_areas:
            goals.append("Week 1-2: 基礎語彙500語の習得")
            goals.append("Week 3-4: 応用語彙300語の習得")
        
        if "文法理解" in priority_areas:
            goals.append("Week 1: 高頻度文法項目の復習")
            goals.append("Week 2-3: 複雑文構造の練習")
        
        if "文構造把握" in priority_areas:
            goals.append("Week 2-4: 長文読解練習（段階的難易度アップ）")
        
        return goals if goals else ["Week 1-4: 総合的読解力向上"]
    
    def export_analysis_result(self, analysis_result: Dict, output_path: str):
        """分析結果をファイルに出力"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析結果を出力しました: {output_path}")
            
        except Exception as e:
            logger.error(f"分析結果の出力に失敗しました: {e}")

def main():
    """テスト用メイン関数"""
    import json
    
    # 設定読み込み
    config_path = Path("config/settings.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    analyzer = TextAnalyzer(config.get('analysis', {}))
    
    sample_text = """
    The revolutionary advances in artificial intelligence have fundamentally transformed 
    the landscape of modern technology. Scientists who previously worked in isolation 
    now collaborate across international boundaries, sharing datasets that would have 
    been impossible to process without machine learning algorithms. If we consider the 
    implications of these developments, it becomes apparent that the integration of AI 
    systems into various industries has created unprecedented opportunities for innovation.
    
    However, the complexity of neural networks, which form the backbone of contemporary 
    AI applications, requires sophisticated mathematical frameworks that challenge even 
    experienced researchers. The algorithms that drive these systems can process vast 
    amounts of information in microseconds, identifying patterns that human analysts 
    might overlook entirely.
    """
    
    print("=== Comprehensive Text Analysis Test ===")
    print(f"Sample text length: {len(sample_text)} characters")
    print()
    
    # 分析実行
    result = analyzer.analyze_text_comprehensive(sample_text)
    
    # 主要結果の表示
    assessment = result.get('comprehensive_assessment', {})
    report = result.get('integrated_report', {})
    
    print("=== Analysis Summary ===")
    print(f"Overall Difficulty: {assessment.get('difficulty_level', '不明')}")
    print(f"Reading Level: {assessment.get('reading_level', '不明')}")
    print(f"Estimated Reading Time: {assessment.get('estimated_reading_time_minutes', 0)} minutes")
    print()
    
    print("=== Key Challenges ===")
    challenges = report.get('executive_summary', {}).get('key_challenges', [])
    for i, challenge in enumerate(challenges, 1):
        print(f"{i}. {challenge}")
    print()
    
    print("=== Study Recommendations ===")
    recommendations = report.get('study_recommendations', {})
    for area, items in recommendations.items():
        print(f"{area}:")
        for item in items[:3]:  # 最初の3項目のみ表示
            print(f"  - {item}")
        print()

if __name__ == "__main__":
    main()