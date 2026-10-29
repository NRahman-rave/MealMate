from django.utils import timezone

from .models import (
    FoodPost,
    Reservation,
    RescueRequest,
)

from .reliability_service import (
    get_reliability_summary,
)


# =========================================================
# USER IMPACT
# =========================================================

def get_user_impact(
    user_id
):

    reliability = (
        get_reliability_summary(
            user_id
        )
    )


    collected_count = (
        Reservation.objects.filter(
            user_id=user_id,
            status="collected",
        ).count()
    )


    rescued_meals = (
        RescueRequest.objects.filter(
            accepted_user_id=user_id,
            status="accepted",
        ).count()
    )


    successful_rescue_passes = (
        RescueRequest.objects.filter(
            original_user_id=user_id,
            status="accepted",
        ).count()
    )


    missed_collections = (
        Reservation.objects.filter(
            user_id=user_id,
            status="missed",
        ).count()
    )


    # One reservation currently represents
    # one reserved portion.

    portions_saved = (
        collected_count
    )


    impact_points = (

        collected_count * 10
        +
        rescued_meals * 15
        +
        successful_rescue_passes * 8

    )


    if impact_points >= 250:

        level = (
            "Community Hero"
        )


    elif impact_points >= 120:

        level = (
            "Rescue Champion"
        )


    elif impact_points >= 50:

        level = (
            "Food Saver"
        )


    else:

        level = (
            "Getting Started"
        )


    return {

        "account_type":
            "user",

        "collected_count":
            collected_count,

        "rescued_meals":
            rescued_meals,

        "successful_rescue_passes":
            successful_rescue_passes,

        "missed_collections":
            missed_collections,

        "portions_saved":
            portions_saved,

        "reliability_score":
            reliability["score"],

        "reliability_label":
            reliability["label"],

        "impact_points":
            impact_points,

        "impact_level":
            level,
    }


# =========================================================
# BUSINESS IMPACT
# =========================================================

def get_business_impact(
    business_id
):

    now = timezone.now()


    food_posts = (
        FoodPost.objects.filter(
            business_id=business_id
        )
    )


    food_ids = list(

        food_posts.values_list(
            "id",
            flat=True,
        )
    )


    total_posts = (
        food_posts.count()
    )


    active_posts = (
        food_posts.filter(
            status="available",
            quantity__gt=0,
            pickup_end__gte=now,
        ).count()
    )


    collected_reservations = (
        Reservation.objects.filter(
            food_post_id__in=food_ids,
            status="collected",
        ).count()
    )


    rescue_relays = (
        RescueRequest.objects.filter(
            food_post_id__in=food_ids,
            status="accepted",
        ).count()
    )


    missed_collections = (
        Reservation.objects.filter(
            food_post_id__in=food_ids,
            status="missed",
        ).count()
    )


    # Current MealMate model treats one
    # successful reservation as one portion
    # reaching a user.

    portions_redistributed = (
        collected_reservations
    )


    impact_points = (

        collected_reservations * 10
        +
        rescue_relays * 8

    )


    if impact_points >= 500:

        level = (
            "Community Impact Leader"
        )


    elif impact_points >= 250:

        level = (
            "Waste Reduction Champion"
        )


    elif impact_points >= 100:

        level = (
            "Active Food Saver"
        )


    else:

        level = (
            "Growing Impact"
        )


    return {

        "account_type":
            "business",

        "total_posts":
            total_posts,

        "active_posts":
            active_posts,

        "successful_collections":
            collected_reservations,

        "rescue_relays":
            rescue_relays,

        "missed_collections":
            missed_collections,

        "portions_redistributed":
            portions_redistributed,

        "impact_points":
            impact_points,

        "impact_level":
            level,
    }