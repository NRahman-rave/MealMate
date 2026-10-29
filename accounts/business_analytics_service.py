from collections import Counter

from django.utils import timezone

from .models import (
    FoodPost,
    Reservation,
    RescueRequest,
)


def pickup_period(dt):

    hour = timezone.localtime(
        dt
    ).hour

    if hour < 12:
        return "Morning"

    if hour < 17:
        return "Afternoon"

    return "Evening"


def get_business_analytics(
    business_id
):

    now = timezone.now()


    food_posts = list(
        FoodPost.objects.filter(
            business_id=business_id
        ).order_by(
            "-created_at"
        )
    )


    food_ids = [
        food.id
        for food in food_posts
    ]


    reservations = list(
        Reservation.objects.filter(
            food_post_id__in=food_ids
        )
    )


    rescue_requests = list(
        RescueRequest.objects.filter(
            food_post_id__in=food_ids
        )
    )


    total_posts = len(
        food_posts
    )


    active_posts = sum(
        1
        for food in food_posts
        if (
            food.status == "available"
            and food.quantity > 0
            and food.pickup_end >= now
        )
    )


    successful_collections = sum(
        1
        for reservation in reservations
        if reservation.status == "collected"
    )


    missed_collections = sum(
        1
        for reservation in reservations
        if reservation.status == "missed"
    )


    active_reservations = sum(
        1
        for reservation in reservations
        if reservation.status == "reserved"
    )


    cancelled_reservations = sum(
        1
        for reservation in reservations
        if reservation.status == "cancelled"
    )


    accepted_rescues = sum(
        1
        for rescue in rescue_requests
        if rescue.status == "accepted"
    )


    expired_rescues = sum(
        1
        for rescue in rescue_requests
        if rescue.status == "expired"
    )


    cancelled_rescues = sum(
        1
        for rescue in rescue_requests
        if rescue.status == "cancelled"
    )


    total_finished_collections = (
        successful_collections
        +
        missed_collections
    )


    if total_finished_collections:

        collection_success_rate = round(
            (
                successful_collections
                /
                total_finished_collections
            )
            *
            100,
            1
        )

    else:

        collection_success_rate = 0


    completed_rescue_attempts = (
        accepted_rescues
        +
        expired_rescues
        +
        cancelled_rescues
    )


    if completed_rescue_attempts:

        rescue_success_rate = round(
            (
                accepted_rescues
                /
                completed_rescue_attempts
            )
            *
            100,
            1
        )

    else:

        rescue_success_rate = 0


    # =====================================================
    # FOOD PERFORMANCE
    # =====================================================

    food_lookup = {
        food.id: food
        for food in food_posts
    }


    collection_counter = Counter()


    for reservation in reservations:

        if reservation.status == "collected":

            collection_counter[
                reservation.food_post_id
            ] += 1


    food_performance = []


    for food in food_posts:

        collected = (
            collection_counter.get(
                food.id,
                0
            )
        )


        food_performance.append(
            {
                "name":
                    food.food_name,

                "collected":
                    collected,

                "remaining":
                    food.quantity,
            }
        )


    food_performance.sort(
        key=lambda item: (
            item["collected"],
            item["name"]
        ),
        reverse=True,
    )


    top_food = (
        food_performance[0]
        if food_performance
        else None
    )


    # =====================================================
    # PICKUP PERIOD
    # =====================================================

    pickup_counter = Counter()


    for reservation in reservations:

        food = food_lookup.get(
            reservation.food_post_id
        )

        if not food:
            continue


        pickup_counter[
            pickup_period(
                food.pickup_start
            )
        ] += 1


    pickup_periods = [
        "Morning",
        "Afternoon",
        "Evening",
    ]


    pickup_values = [
        pickup_counter.get(
            period,
            0
        )
        for period in pickup_periods
    ]


    busiest_pickup_period = (
        max(
            pickup_periods,
            key=lambda period:
                pickup_counter.get(
                    period,
                    0
                )
        )
        if reservations
        else "No data yet"
    )


    # =====================================================
    # CHART DATA
    # =====================================================

    collection_chart = {

        "labels": [
            "Collected",
            "Missed",
            "Active",
            "Cancelled",
        ],

        "values": [
            successful_collections,
            missed_collections,
            active_reservations,
            cancelled_reservations,
        ],
    }


    rescue_chart = {

        "labels": [
            "Accepted",
            "Expired",
            "Cancelled",
        ],

        "values": [
            accepted_rescues,
            expired_rescues,
            cancelled_rescues,
        ],
    }


    top_food_chart = {

        "labels": [
            item["name"]
            for item
            in food_performance[:6]
        ],

        "values": [
            item["collected"]
            for item
            in food_performance[:6]
        ],
    }


    pickup_chart = {

        "labels":
            pickup_periods,

        "values":
            pickup_values,
    }


    return {

        "total_posts":
            total_posts,

        "active_posts":
            active_posts,

        "successful_collections":
            successful_collections,

        "missed_collections":
            missed_collections,

        "active_reservations":
            active_reservations,

        "accepted_rescues":
            accepted_rescues,

        "collection_success_rate":
            collection_success_rate,

        "rescue_success_rate":
            rescue_success_rate,

        "top_food":
            top_food,

        "busiest_pickup_period":
            busiest_pickup_period,

        "food_performance":
            food_performance[:8],

        "collection_chart":
            collection_chart,

        "rescue_chart":
            rescue_chart,

        "top_food_chart":
            top_food_chart,

        "pickup_chart":
            pickup_chart,
    }