"""Seed monitored_sources with RSS feeds and VC firm press pages.

Revision ID: 006
Revises: 005
"""

import uuid

import sqlalchemy as sa

from alembic import op

revision = "006"
down_revision = "005"

SOURCES = [
    # RSS Feeds
    ("TechCrunch", "https://techcrunch.com/feed/", "rss"),
    ("Crunchbase News", "https://news.crunchbase.com/feed/", "rss"),
    ("VentureBeat", "https://venturebeat.com/feed/", "rss"),
    ("The Information", "https://www.theinformation.com/feed", "rss"),
    ("PitchBook News", "https://pitchbook.com/news/rss", "rss"),
    ("Fortune Venture", "https://fortune.com/section/venture/feed/", "rss"),
    ("Axios Pro Rata", "https://www.axios.com/pro/pro-rata/feed", "rss"),
    ("SaaStr Blog", "https://www.saastr.com/feed/", "rss"),
    # VC Firm Press/Portfolio Pages
    ("Andreessen Horowitz", "https://a16z.com/announcements/", "webpage"),
    ("Sequoia Capital", "https://www.sequoiacap.com/build/", "webpage"),
    ("Accel", "https://www.accel.com/noteworthy", "webpage"),
    ("Benchmark", "https://www.benchmark.com/", "webpage"),
    ("Lightspeed Venture Partners", "https://lsvp.com/news/", "webpage"),
    ("Greylock Partners", "https://greylock.com/portfolio/", "webpage"),
    ("Founders Fund", "https://foundersfund.com/the-fund/#portfolio", "webpage"),
    ("Index Ventures", "https://www.indexventures.com/newsroom/", "webpage"),
    ("General Catalyst", "https://www.generalcatalyst.com/perspectives", "webpage"),
    ("Bessemer Venture Partners", "https://www.bvp.com/news", "webpage"),
    ("Insight Partners", "https://www.insightpartners.com/newsroom/", "webpage"),
    ("Tiger Global Management", "https://www.tigerglobal.com/", "webpage"),
    ("Kleiner Perkins", "https://www.kleinerperkins.com/perspectives/", "webpage"),
    ("NEA", "https://www.nea.com/news", "webpage"),
    ("Khosla Ventures", "https://www.khoslaventures.com/news", "webpage"),
    ("GV", "https://www.gv.com/portfolio/", "webpage"),
    ("Ribbit Capital", "https://ribbitcap.com/", "webpage"),
    ("Thrive Capital", "https://www.thrivecap.com/", "webpage"),
    ("Coatue Management", "https://www.coatue.com/ventures", "webpage"),
    ("Lux Capital", "https://www.luxcapital.com/news", "webpage"),
]


def upgrade():
    table = sa.table(
        "monitored_sources",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.Text),
        sa.column("url", sa.Text),
        sa.column("source_type", sa.Text),
        sa.column("active", sa.Boolean),
    )
    op.bulk_insert(
        table,
        [
            {
                "id": str(uuid.uuid4()),
                "name": name,
                "url": url,
                "source_type": source_type,
                "active": True,
            }
            for name, url, source_type in SOURCES
        ],
    )


def downgrade():
    urls = [url for _, url, _ in SOURCES]
    op.execute(
        sa.text("DELETE FROM monitored_sources WHERE url = ANY(:urls)").bindparams(
            urls=urls,
        )
    )
