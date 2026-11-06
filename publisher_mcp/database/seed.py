"""Seed default site profile specialized in Tech, AI, IT, and Computing."""

from publisher_mcp.database import db


def seed_default_tech_site(db_path: str = None) -> int:
    db.init_db(db_path)
    existing = db.get_site_profile("tech-core", db_path=db_path)
    if existing:
        return existing["id"]

    site_id = db.create_site(
        slug="tech-core",
        name="CoreTech Digest",
        url="https://techcore.local",
        niche="Information Technology, Artificial Intelligence, Software Engineering, and Computing Systems",
        language="en",
        editorial_rules={
            "min_word_count": 300,
            "max_posts_per_day": 2,
            "sections": [
                "Artificial Intelligence",
                "Cloud & DevOps",
                "Software Engineering",
                "Hardware & Systems",
            ],
            "forbidden_keywords": [
                "financial advice",
                "stock pick",
                "medical diagnosis",
                "election poll",
                "crypto giveaway",
            ],
        },
        db_path=db_path,
    )
    return site_id


if __name__ == "__main__":
    sid = seed_default_tech_site()
    print(f"Default tech site seeded with ID: {sid}")
