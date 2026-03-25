from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user import User
from datetime import datetime, timedelta, timezone

def get_nearby_users(db: Session, current_user: User) -> list[dict]:
    online_threshold = datetime.now(timezone.utc) - timedelta(seconds=60)

    query = text("""
        SELECT * FROM (
            SELECT
                id,
                name,
                bio,
                avatar_url,
                last_seen,
                (
                    6371 * acos(
                        LEAST(1.0, (
                            cos(radians(:lat)) *
                            cos(radians(latitude)) *
                            cos(radians(longitude) - radians(:lng)) +
                            sin(radians(:lat)) *
                            sin(radians(latitude))
                        ))
                    )
                ) AS distance_km
            FROM users
            WHERE
                id != :user_id
                AND is_discoverable = true
                AND is_active = true
                AND last_seen > :online_threshold
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
        ) AS nearby
        WHERE distance_km <= :radius_km
        ORDER BY distance_km ASC
    """)

    result = db.execute(query, {
        "lat": current_user.latitude,
        "lng": current_user.longitude,
        "user_id": current_user.id,
        "online_threshold": online_threshold,
        "radius_km": current_user.discovery_radius_km
    })

    rows = result.fetchall()

    return [
        {
            "id": row.id,
            "name": row.name,
            "bio": row.bio,
            "avatar_url": row.avatar_url,
            "distance_km": round(row.distance_km, 1),
            "is_online": True
        }
        for row in rows
    ]