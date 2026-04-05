"""Retrospective case studies of LLM failures

Includes:
- GPT-4 context window overflow (March 2024)
- Claude API throughput degradation (Q3 2024)
- Gemini load-balancing failure (January 2025)
- Microsoft Copilot / Bing Chat incidents (Sep 2023 - Mar 2024)
- DeepSeek (深度求索) incidents (Jan - Mar 2025)
- Perplexity AI incidents (2024-2025)
"""

from case_studies.gpt4_case_study import GPT4CaseStudy, run_analysis as run_gpt4_analysis
from case_studies.claude_case_study import ClaudeCaseStudy, run_analysis as run_claude_analysis
from case_studies.gemini_case_study import GeminiCaseStudy, run_analysis as run_gemini_analysis
from case_studies.copilot_case_study import MicrosoftCopilotCaseStudy, run_analysis as run_copilot_analysis
from case_studies.deepseek_case_study import DeepSeekCaseStudy, run_analysis as run_deepseek_analysis
from case_studies.perplexity_case_study import PerplexityCaseStudy, run_analysis as run_perplexity_analysis

__all__ = [
    "GPT4CaseStudy",
    "run_gpt4_analysis",
    "ClaudeCaseStudy",
    "run_claude_analysis",
    "GeminiCaseStudy",
    "run_gemini_analysis",
    "MicrosoftCopilotCaseStudy",
    "run_copilot_analysis",
    "DeepSeekCaseStudy",
    "run_deepseek_analysis",
    "PerplexityCaseStudy",
    "run_perplexity_analysis"
]
