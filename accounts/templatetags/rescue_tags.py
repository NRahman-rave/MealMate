from django import template

from accounts.models import (
    FoodInterest,
    MealMateUser,
    UserActivity,
)

from accounts.reliability_service import (
    get_reliability_summary,
)


register = template.Library()


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
        "mac and cheese",
        "alfredo",
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
        "sandwiches",

    "pasta":
        "pasta",

    "salad":
        "salads",

    "wrap":
        "wraps and rolls",

    "rice":
        "rice meals",

    "bakery":
        "bakery food",

    "hot_food":
        "hot food",
}


def detect_food_type(food):

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


    return None


def detect_area(food):

    address = (
        food.pickup_address or ""
    )


    parts = [

        item.strip()

        for item
        in address.split(",")

        if item.strip()
    ]


    if len(parts) >= 2:
        return parts[1]


    if parts:
        return parts[0]


    return ""


def detect_pickup_period(food):

    hour = (
        food.pickup_start.hour
    )


    if hour < 12:
        return "morning"


    if hour < 17:
        return "afternoon"


    return "evening"


def build_match_reasons(
    user,
    food,
):

    reasons = []


    # =====================================================
    # SAVED FOOD
    # =====================================================

    if FoodInterest.objects.filter(
        user_id=user.id,
        food_post_id=food.id,
    ).exists():

        reasons.append(
            {
                "icon":
                    "fa-heart",

                "text":
                    "You saved this food",

                "points":
                    40,
            }
        )


    # =====================================================
    # VIEWED FOOD
    # =====================================================

    if UserActivity.objects.filter(
        user_id=user.id,
        activity_type="view_food",
        food_post_id=food.id,
    ).exists():

        reasons.append(
            {
                "icon":
                    "fa-eye",

                "text":
                    "You viewed this food before",

                "points":
                    20,
            }
        )


    # =====================================================
    # SEARCH MATCH
    # =====================================================

    food_text = (
        f"{food.food_name} "
        f"{food.description or ''}"
    ).lower()


    searches = (
        UserActivity.objects.filter(
            user_id=user.id,
            activity_type="search",
        )
        .exclude(
            value__isnull=True
        )
        .values_list(
            "value",
            flat=True,
        )
    )


    for value in searches:

        search = (
            value or ""
        ).strip().lower()


        if (
            search
            and
            search in food_text
        ):

            reasons.append(
                {
                    "icon":
                        "fa-magnifying-glass",

                    "text":
                        (
                            f'You searched for '
                            f'"{value}"'
                        ),

                    "points":
                        15,
                }
            )

            break


    # =====================================================
    # FOOD TYPE
    # =====================================================

    food_type = (
        detect_food_type(
            food
        )
    )


    if food_type:

        if UserActivity.objects.filter(
            user_id=user.id,
            activity_type="filter_food_type",
            value__iexact=food_type,
        ).exists():

            reasons.append(
                {
                    "icon":
                        "fa-bowl-food",

                    "text":
                        (
                            "You often explore "
                            f"{FOOD_TYPE_LABELS.get(food_type, food_type)}"
                        ),

                    "points":
                        15,
                }
            )


    # =====================================================
    # AREA
    # =====================================================

    area = detect_area(
        food
    )


    if (
        area
        and
        UserActivity.objects.filter(
            user_id=user.id,
            activity_type="filter_area",
            value__iexact=area,
        ).exists()
    ):

        reasons.append(
            {
                "icon":
                    "fa-location-dot",

                "text":
                    (
                        f"You prefer food around "
                        f"{area}"
                    ),

                "points":
                    15,
            }
        )


    # =====================================================
    # BUSINESS
    # =====================================================

    if UserActivity.objects.filter(
        user_id=user.id,
        activity_type="filter_business",
        value=str(food.business_id),
    ).exists():

        business = (
            MealMateUser.objects.filter(
                id=food.business_id
            ).first()
        )


        business_name = (
            business.full_name
            if business
            else
            "this business"
        )


        reasons.append(
            {
                "icon":
                    "fa-store",

                "text":
                    (
                        f"You have explored "
                        f"{business_name}"
                    ),

                "points":
                    10,
            }
        )


    # =====================================================
    # PICKUP TIME
    # =====================================================

    pickup_period = (
        detect_pickup_period(
            food
        )
    )


    if UserActivity.objects.filter(
        user_id=user.id,
        activity_type="filter_pickup",
        value__iexact=pickup_period,
    ).exists():

        reasons.append(
            {
                "icon":
                    "fa-clock",

                "text":
                    (
                        f"You prefer "
                        f"{pickup_period} pickups"
                    ),

                "points":
                    10,
            }
        )


    return reasons


@register.inclusion_tag(
    "rescue_match_details.html"
)
def rescue_match_details(
    user,
    food,
    match_score,
):

    reliability = (
        get_reliability_summary(
            user.id
        )
    )


    reasons = (
        build_match_reasons(
            user,
            food,
        )
    )


    reliability_points = (
        round(
            reliability["score"]
            /
            5
        )
    )


    return {

        "match_score":
            match_score,

        "reasons":
            reasons,

        "reliability":
            reliability,

        "reliability_points":
            reliability_points,
    }