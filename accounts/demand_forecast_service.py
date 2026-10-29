from datetime import timedelta

from django.utils import timezone

from .models import (
    FoodInterest,
    FoodPost,
    Reservation,
    RescueRequest,
    UserActivity,
)


# =========================================================
# CONFIGURATION
# =========================================================

FORECAST_DAYS = 30


# =========================================================
# FOOD TAXONOMY
# =========================================================

FOOD_TYPE_KEYWORDS = {

    "sandwich": [
        "sandwich",
        "baguette",
        "toastie",
        "panini",
        "melt",
    ],

    "pasta": [
        "pasta",
        "penne",
        "alfredo",
        "mac and cheese",
    ],

    "salad": [
        "salad",
        "fruit pot",
    ],

    "wrap": [
        "wrap",
        "burrito",
        "roll",
    ],

    "rice": [
        "rice",
        "biryani",
        "curry",
        "katsu",
    ],

    "bakery": [
        "cake",
        "muffin",
        "cookie",
        "croissant",
        "brownie",
        "doughnut",
        "cupcake",
        "cinnamon",
        "crumble",
        "loaf",
        "twist",
        "jamun",
    ],

    "hot_food": [
        "burger",
        "chicken",
        "wings",
        "grill",
        "soup",
        "fries",
        "pasty",
        "patty",
    ],
}


FOOD_TYPE_LABELS = {

    "sandwich":
        "Sandwich",

    "pasta":
        "Pasta",

    "salad":
        "Salad",

    "wrap":
        "Wrap",

    "rice":
        "Rice Meals",

    "bakery":
        "Bakery",

    "hot_food":
        "Hot Food",
}


# =========================================================
# FOOD TYPE
# =========================================================

def detect_food_type(
    food
):

    combined = (
        f"{food.food_name} "
        f"{food.description or ''}"
    ).lower()


    for (
        food_type,
        keywords
    ) in FOOD_TYPE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in combined:

                return food_type


    return "other"


# =========================================================
# AREA
# =========================================================

def detect_area(
    food
):

    address = (
        food.pickup_address or ""
    )


    parts = [

        part.strip()

        for part
        in address.split(",")

        if part.strip()
    ]


    if len(parts) >= 2:

        return parts[1]


    if parts:

        return parts[0]


    return "Unknown"


# =========================================================
# PICKUP PERIOD
# =========================================================

def detect_pickup_period(
    food
):

    hour = (
        timezone.localtime(
            food.pickup_start
        ).hour
    )


    if hour < 12:

        return "morning"


    if hour < 17:

        return "afternoon"


    return "evening"


# =========================================================
# DEMAND LEVEL
# =========================================================

def demand_level(
    score
):

    if score >= 75:

        return {
            "level":
                "HIGH",

            "class":
                "high",

            "message":
                "Strong user demand detected.",
        }


    if score >= 45:

        return {
            "level":
                "MEDIUM",

            "class":
                "medium",

            "message":
                "Moderate demand detected.",
        }


    return {
        "level":
            "LOW",

        "class":
            "low",

        "message":
            "Limited recent demand detected.",
    }


# =========================================================
# FORECAST ONE FOOD POST
# =========================================================

def forecast_food_post(
    food
):

    now = timezone.now()

    recent_cutoff = (
        now
        -
        timedelta(
            days=FORECAST_DAYS
        )
    )


    food_type = (
        detect_food_type(
            food
        )
    )


    area = detect_area(
        food
    )


    pickup_period = (
        detect_pickup_period(
            food
        )
    )


    food_text = (
        f"{food.food_name} "
        f"{food.description or ''}"
    ).lower()


    # =====================================================
    # EXACT SAVED INTERESTS
    # =====================================================

    saved_interests = (
        FoodInterest.objects.filter(
            food_post_id=food.id,
        ).count()
    )


    saved_points = min(
        saved_interests * 10,
        30
    )


    # =====================================================
    # RECENT FOOD VIEWS
    # =====================================================

    recent_views = (
        UserActivity.objects.filter(
            food_post_id=food.id,
            activity_type="view_food",
            created_at__gte=recent_cutoff,
        ).count()
    )


    view_points = min(
        recent_views * 3,
        20
    )


    # =====================================================
    # SEARCH DEMAND
    # =====================================================

    recent_searches = (
        UserActivity.objects.filter(
            activity_type="search",
            created_at__gte=recent_cutoff,
        )
        .exclude(
            value__isnull=True
        )
        .values_list(
            "value",
            flat=True,
        )
    )


    matching_searches = 0


    for value in recent_searches:

        search = (
            value or ""
        ).strip().lower()


        if (
            search
            and
            (
                search in food_text
                or
                any(
                    word in search
                    for word
                    in food.food_name.lower().split()
                    if len(word) >= 4
                )
            )
        ):

            matching_searches += 1


    search_points = min(
        matching_searches * 3,
        15
    )


    # =====================================================
    # FOOD TYPE DEMAND
    # =====================================================

    food_type_filters = 0


    if food_type != "other":

        food_type_filters = (
            UserActivity.objects.filter(
                activity_type="filter_food_type",
                value__iexact=food_type,
                created_at__gte=recent_cutoff,
            ).count()
        )


    food_type_points = min(
        food_type_filters * 2,
        10
    )


    # =====================================================
    # AREA DEMAND
    # =====================================================

    area_filters = (
        UserActivity.objects.filter(
            activity_type="filter_area",
            value__iexact=area,
            created_at__gte=recent_cutoff,
        ).count()
    )


    area_points = min(
        area_filters * 2,
        10
    )


    # =====================================================
    # PICKUP PERIOD DEMAND
    # =====================================================

    pickup_filters = (
        UserActivity.objects.filter(
            activity_type="filter_pickup",
            value__iexact=pickup_period,
            created_at__gte=recent_cutoff,
        ).count()
    )


    pickup_points = min(
        pickup_filters,
        5
    )


    # =====================================================
    # RESERVATION SIGNAL
    # =====================================================

    reservations = (
        Reservation.objects.filter(
            food_post_id=food.id
        ).count()
    )


    reservation_points = min(
        reservations * 5,
        10
    )


    # =====================================================
    # SCORE
    #
    # Maximum:
    #
    # interests       30
    # views           20
    # searches        15
    # food type       10
    # area            10
    # pickup period    5
    # reservations    10
    #
    # TOTAL          100
    # =====================================================

    score = (

        saved_points
        +
        view_points
        +
        search_points
        +
        food_type_points
        +
        area_points
        +
        pickup_points
        +
        reservation_points
    )


    score = min(
        score,
        100
    )


    level_info = (
        demand_level(
            score
        )
    )


    # =====================================================
    # EXPLANATION SIGNALS
    # =====================================================

    signals = []


    if saved_interests:

        signals.append(
            (
                f"{saved_interests} "
                f"saved interest"
                f"{'s' if saved_interests != 1 else ''}"
            )
        )


    if recent_views:

        signals.append(
            (
                f"{recent_views} recent "
                f"food view"
                f"{'s' if recent_views != 1 else ''}"
            )
        )


    if matching_searches:

        signals.append(
            (
                f"{matching_searches} "
                f"matching search"
                f"{'es' if matching_searches != 1 else ''}"
            )
        )


    if food_type_filters:

        food_label = (
            FOOD_TYPE_LABELS.get(
                food_type,
                food_type.replace(
                    "_",
                    " "
                ).title()
            )
        )


        signals.append(
            (
                f"Interest in "
                f"{food_label}"
            )
        )


    if area_filters:

        signals.append(
            (
                f"Active demand around "
                f"{area}"
            )
        )


    if pickup_filters:

        signals.append(
            (
                f"{pickup_period.title()} "
                f"pickup preference"
            )
        )


    if reservations:

        signals.append(
            (
                f"{reservations} existing "
                f"reservation"
                f"{'s' if reservations != 1 else ''}"
            )
        )


    if not signals:

        signals.append(
            "Not enough behavioural data yet"
        )


    return {

        "food_id":
            food.id,

        "food_name":
            food.food_name,

        "score":
            score,

        "level":
            level_info["level"],

        "level_class":
            level_info["class"],

        "message":
            level_info["message"],

        "food_type":
            FOOD_TYPE_LABELS.get(
                food_type,
                food_type.replace(
                    "_",
                    " "
                ).title()
            ),

        "area":
            area,

        "pickup_period":
            pickup_period.title(),

        "saved_interests":
            saved_interests,

        "recent_views":
            recent_views,

        "matching_searches":
            matching_searches,

        "area_filters":
            area_filters,

        "food_type_filters":
            food_type_filters,

        "pickup_filters":
            pickup_filters,

        "reservations":
            reservations,

        "signals":
            signals,
    }


# =========================================================
# BUSINESS FORECAST
# =========================================================

def get_business_demand_forecast(
    business_id
):

    now = timezone.now()


    foods = list(
        FoodPost.objects.filter(
            business_id=business_id,
            status="available",
            pickup_end__gte=now,
        ).order_by(
            "pickup_end"
        )
    )


    forecasts = [

        forecast_food_post(
            food
        )

        for food
        in foods
    ]


    forecasts.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )


    # =====================================================
    # OVERALL BUSINESS DEMAND
    # =====================================================

    if forecasts:

        average_score = round(
            sum(
                item["score"]
                for item
                in forecasts
            )
            /
            len(
                forecasts
            )
        )

    else:

        average_score = 0


    overall = (
        demand_level(
            average_score
        )
    )


    highest_demand = (
        forecasts[0]
        if forecasts
        else None
    )


    # =====================================================
    # FOOD TYPE DEMAND
    # =====================================================

    food_type_totals = {}


    for forecast in forecasts:

        food_type = (
            forecast["food_type"]
        )


        if food_type not in food_type_totals:

            food_type_totals[
                food_type
            ] = {
                "total":
                    0,

                "count":
                    0,
            }


        food_type_totals[
            food_type
        ]["total"] += (
            forecast["score"]
        )


        food_type_totals[
            food_type
        ]["count"] += 1


    food_type_forecasts = []


    for (
        food_type,
        data
    ) in food_type_totals.items():

        average = round(
            data["total"]
            /
            data["count"]
        )


        level = (
            demand_level(
                average
            )
        )


        food_type_forecasts.append(
            {
                "name":
                    food_type,

                "score":
                    average,

                "level":
                    level["level"],

                "level_class":
                    level["class"],
            }
        )


    food_type_forecasts.sort(
        key=lambda item:
            item["score"],
        reverse=True,
    )


    return {

        "forecast_days":
            FORECAST_DAYS,

        "overall_score":
            average_score,

        "overall_level":
            overall["level"],

        "overall_class":
            overall["class"],

        "highest_demand":
            highest_demand,

        "forecasts":
            forecasts[:8],

        "food_type_forecasts":
            food_type_forecasts[:6],
    }