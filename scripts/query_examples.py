"""
Example database queries for learning PostgreSQL/SQLAlchemy
"""
import sys
import os
import sqlalchemy as sa

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.connection import db
from app.repositories.insight_repository import InsightRepository
from app.models.database import Insight
from sqlalchemy import desc, func
import json


def example_queries():
    """Demonstrate common database queries"""
    session = db.get_session()
    repo = InsightRepository(session)

    print("\n" + "=" * 60)
    print("POSTGRESQL + SQLALCHEMY QUERY EXAMPLES")
    print("=" * 60)

    try:
        # Example 1: Get all insights (limit 5)
        print("\n1. Get recent insights (limit 5):")
        insights = session.query(Insight).order_by(
            desc(Insight.created_at)
        ).limit(5).all()

        for insight in insights:
            print(f"  - {insight.insight_id}: {insight.user_id} @ {insight.created_at}")

        # Example 2: Count insights by severity
        print("\n2. Count insights by severity:")
        severity_counts = session.query(
            Insight.llm_output['severity'].astext.label('severity'),
            func.count(Insight.insight_id).label('count')
        ).group_by('severity').all()

        for severity, count in severity_counts:
            print(f"  - {severity}: {count}")

        # Example 3: Get insights for specific user
        print("\n3. Get insights for user 'demo':")
        user_insights = session.query(Insight).filter(
            Insight.user_id == 'demo'
        ).all()

        print(f"  Found {len(user_insights)} insights for user 'demo'")

        # Example 4: Query JSONB fields
        print("\n4. Get high-severity insights:")
        high_severity = session.query(Insight).filter(
            Insight.llm_output['severity'].astext == 'high'
        ).all()

        print(f"  Found {high_severity} high-severity insights")

        # Example 5: Using repository pattern
        print("\n5. Using InsightRepository:")
        insights_list, total = repo.get_by_user(
            user_id='demo',
            tenant_id='demo_tenant',
            limit=10,
            severity='high'
        )

        print(f"  Total high-severity insights for demo: {total}")

        # Example 6: Complex JSONB query
        print("\n6. Get insights where confidence > 0.8:")
        high_confidence = session.query(Insight).filter(
            Insight.llm_output['confidence'].astext.cast(sa.Float) > 0.8
        ).all()

        print(f"  Found {len(high_confidence)} high-confidence insights")

    finally:
        session.close()

    print("\n" + "=" * 60)
    print("Query examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    example_queries()