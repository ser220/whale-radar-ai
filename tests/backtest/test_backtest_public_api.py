import app.backtest as backtest
from app.backtest import (
    AIReviewGenerator,
    AISummaryGenerator,
    BacktestAIReview,
    BacktestAISummary,
    BacktestAnalyticsCalculator,
    BacktestAnalyticsReport,
    BacktestBenchmarkReport,
    BacktestDecisionReport,
    BacktestEquityCurve,
    BacktestEvaluationEvaluator,
    BacktestEvaluationReport,
    BacktestFinalReport,
    BacktestPerformanceAggregator,
    BacktestPerformanceReport,
    BacktestRecommendation,
    BacktestReport,
    BacktestReportGenerator,
    BacktestRiskReport,
    BacktestSessionConfig,
    BacktestSessionResult,
    BacktestSessionService,
    BacktestStrategyRanking,
    BenchmarkCalculator,
    DecisionReportCalculator,
    EquityCurveCalculator,
    EquityPoint,
    RankingCalculator,
    RecommendationCalculator,
    ReportGenerator,
    RiskMetricsCalculator,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "BacktestSessionResult",
    "BacktestSessionService",
    "BacktestSessionConfig",
    "BacktestPerformanceAggregator",
    "BacktestPerformanceReport",
    "BacktestReport",
    "BacktestReportGenerator",
    "BacktestAnalyticsCalculator",
    "BacktestAnalyticsReport",
    "BacktestEquityCurve",
    "EquityCurveCalculator",
    "EquityPoint",
    "BacktestRiskReport",
    "RiskMetricsCalculator",
    "BacktestBenchmarkReport",
    "BenchmarkCalculator",
    "BacktestEvaluationReport",
    "BacktestEvaluationEvaluator",
    "BacktestStrategyRanking",
    "RankingCalculator",
    "BacktestRecommendation",
    "RecommendationCalculator",
    "BacktestDecisionReport",
    "DecisionReportCalculator",
    "BacktestFinalReport",
    "ReportGenerator",
    "AISummaryGenerator",
    "BacktestAISummary",
    "AIReviewGenerator",
    "BacktestAIReview",
)

EXPLICIT_IMPORTS = {
    "AIReviewGenerator": AIReviewGenerator,
    "AISummaryGenerator": AISummaryGenerator,
    "BacktestAIReview": BacktestAIReview,
    "BacktestAISummary": BacktestAISummary,
    "BacktestAnalyticsCalculator": BacktestAnalyticsCalculator,
    "BacktestAnalyticsReport": BacktestAnalyticsReport,
    "BacktestBenchmarkReport": BacktestBenchmarkReport,
    "BacktestDecisionReport": BacktestDecisionReport,
    "BacktestEquityCurve": BacktestEquityCurve,
    "BacktestEvaluationEvaluator": BacktestEvaluationEvaluator,
    "BacktestEvaluationReport": BacktestEvaluationReport,
    "BacktestFinalReport": BacktestFinalReport,
    "BacktestPerformanceAggregator": BacktestPerformanceAggregator,
    "BacktestPerformanceReport": BacktestPerformanceReport,
    "BacktestRecommendation": BacktestRecommendation,
    "BacktestReport": BacktestReport,
    "BacktestReportGenerator": BacktestReportGenerator,
    "BacktestRiskReport": BacktestRiskReport,
    "BacktestSessionConfig": BacktestSessionConfig,
    "BacktestSessionResult": BacktestSessionResult,
    "BacktestSessionService": BacktestSessionService,
    "BacktestStrategyRanking": BacktestStrategyRanking,
    "BenchmarkCalculator": BenchmarkCalculator,
    "DecisionReportCalculator": DecisionReportCalculator,
    "EquityCurveCalculator": EquityCurveCalculator,
    "EquityPoint": EquityPoint,
    "RankingCalculator": RankingCalculator,
    "RecommendationCalculator": RecommendationCalculator,
    "ReportGenerator": ReportGenerator,
    "RiskMetricsCalculator": RiskMetricsCalculator,
}


def test_backtest_all_contains_exact_expected_symbols() -> None:
    assert tuple(backtest.__all__) == (
        EXPECTED_PUBLIC_SYMBOLS
    )
    assert len(backtest.__all__) == 30


def test_backtest_all_symbols_are_unique_and_resolvable() -> None:
    assert len(set(backtest.__all__)) == len(
        backtest.__all__
    )

    for symbol in backtest.__all__:
        assert hasattr(
            backtest,
            symbol,
        )


def test_benchmark_calculator_is_publicly_exported() -> None:
    assert "BenchmarkCalculator" in (
        backtest.__all__
    )

    namespace = {}
    exec(
        "from app.backtest import *",
        namespace,
    )

    assert namespace[
        "BenchmarkCalculator"
    ] is BenchmarkCalculator


def test_explicit_backtest_imports_remain_unchanged() -> None:
    assert set(EXPLICIT_IMPORTS) == set(
        EXPECTED_PUBLIC_SYMBOLS
    )

    for symbol, imported_value in (
        EXPLICIT_IMPORTS.items()
    ):
        assert imported_value is getattr(
            backtest,
            symbol,
        )
