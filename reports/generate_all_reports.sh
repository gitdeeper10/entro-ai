#!/bin/bash
# ENTRO-AI Reports Generator
# تشغيل هذا السكريبت يوميًا عبر cron

echo "========================================="
echo "ENTRO-AI Reports Generator"
echo "Time: $(date)"
echo "========================================="

# توليد التقرير اليومي
python reports/daily_report.py

# تجميع التقارير الأسبوعية (كل يوم جمعة)
if [ "$(date +%u)" -eq 5 ]; then
    echo "Generating weekly report..."
    python -c "
from reports.daily_report import WeeklyReportGenerator
gen = WeeklyReportGenerator()
gen.generate([], 'Perplexity_AI')
"
fi

# تجميع التقارير الشهرية (آخر يوم من الشهر)
if [ "$(date +%d)" -eq 1 ]; then
    echo "Generating monthly report..."
    python -c "
from reports.daily_report import MonthlyReportGenerator
gen = MonthlyReportGenerator()
gen.generate([], 'Perplexity_AI')
"
fi

echo "========================================="
echo "Reports generated successfully"
echo "========================================="
