"""The canonical metric glossary - the single source of truth this agent compares
submitted SQL against. In a real company this would live in a shared repo/wiki that
teams reference; here it's just a Python dict for the demo.

Each metric also ships one deliberately "broken" example submission with a real,
subtle mismatch - the kind that actually happens when two teams build the same
metric independently without checking with each other first.
"""

GLOSSARY = {
    "Active User": {
        "description": "A user who has logged in within the last 30 days, excluding trial accounts.",
        "canonical_sql": (
            "SELECT COUNT(DISTINCT user_id) FROM sessions\n"
            "WHERE last_login >= CURRENT_DATE - INTERVAL '30 days'\n"
            "  AND is_trial = FALSE"
        ),
        "example_submission": (
            "SELECT COUNT(DISTINCT user_id) FROM sessions\n"
            "WHERE last_login >= CURRENT_DATE - INTERVAL '30 days'"
        ),
    },
    "Churn Rate": {
        "description": (
            "Percentage of customers who cancelled during the period, out of customers "
            "who were already active at the START of the period."
        ),
        "canonical_sql": (
            "SELECT\n"
            "  COUNT(CASE WHEN cancelled_at BETWEEN :period_start AND :period_end THEN 1 END) * 100.0\n"
            "  / COUNT(CASE WHEN created_at < :period_start THEN 1 END)\n"
            "FROM customers"
        ),
        "example_submission": (
            "SELECT\n"
            "  COUNT(CASE WHEN cancelled_at BETWEEN :period_start AND :period_end THEN 1 END) * 100.0\n"
            "  / COUNT(CASE WHEN created_at < :period_end THEN 1 END)\n"
            "FROM customers"
        ),
    },
    "Monthly Recurring Revenue": {
        "description": "Sum of monthly subscription value for all currently active (non-cancelled, non-trialing) subscriptions.",
        "canonical_sql": (
            "SELECT SUM(monthly_value) FROM subscriptions\n"
            "WHERE status = 'active'"
        ),
        "example_submission": (
            "SELECT SUM(monthly_value) FROM subscriptions\n"
            "WHERE status IN ('active', 'trialing')"
        ),
    },
}
