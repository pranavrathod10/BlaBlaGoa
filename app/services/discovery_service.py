from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user import User
from datetime import datetime, timedelta, timezone


def get_nearby_users(db: Session, current_user: User) -> list[dict]:
    """
    Finds all users within current_user's discovery_radius_km.

    Uses the Haversine formula — the standard way to calculate
    distance between two GPS coordinates on Earth's surface.

    6371 = Earth's radius in kilometres.
    The formula accounts for Earth's curvature so distances
    are accurate even over long distances.
    """

    # Anyone not seen in the last 60 seconds is considered offline
    online_threshold = datetime.now(timezone.utc) - timedelta(seconds=60)

    query = text("""
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
        ORDER BY distance_km ASC
        HAVING distance_km <= :radius_km
    """)

    # Note: HAVING works on computed columns in PostgreSQL
    # We use LEAST(1.0, ...) to prevent acos from getting
    # values slightly above 1.0 due to floating point errors
    # which would cause a math domain error

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
            "is_online": True  # already filtered to online only
        }
        for row in rows
    ]