from .extension_service import (
    sync_expired_reservations,
)

from .models import (
    Reservation,
    RescueRequest,
)


def get_reliability_summary(
    user_id
):

    sync_expired_reservations(
        user_id=user_id
    )


    successful_collections = (
        Reservation.objects.filter(
            user_id=user_id,
            status="collected",
        ).count()
    )


    responsible_rescue_passes = (
        RescueRequest.objects.filter(
            original_user_id=user_id,
            status="accepted",
        ).count()
    )


    missed_collections = (
        Reservation.objects.filter(
            user_id=user_id,
            status="expired",
        )
        .exclude(
            collection_intent="cant_collect"
        )
        .count()
    )


    score = 75


    score += min(
        successful_collections * 3,
        20
    )


    score += min(
        responsible_rescue_passes * 2,
        10
    )


    score -= (
        missed_collections * 20
    )


    score = max(
        0,
        min(
            score,
            100
        )
    )


    if score >= 90:

        label = (
            "Highly Reliable"
        )


    elif score >= 75:

        label = (
            "Reliable"
        )


    elif score >= 60:

        label = (
            "Developing"
        )


    else:

        label = (
            "Needs Improvement"
        )


    return {
        "score":
            score,

        "label":
            label,

        "successful_collections":
            successful_collections,

        "responsible_rescue_passes":
            responsible_rescue_passes,

        "missed_collections":
            missed_collections,
    }


def reliability_match_bonus(
    user_id
):

    summary = (
        get_reliability_summary(
            user_id
        )
    )


    return min(
        round(
            summary["score"]
            /
            5
        ),
        20
    )