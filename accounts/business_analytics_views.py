from django.shortcuts import (
    redirect,
    render,
)

from .business_analytics_service import (
    get_business_analytics,
)

from .demand_forecast_service import (
    get_business_demand_forecast,
)

from .models import (
    MealMateUser,
)


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user(
    request
):

    user_id = (
        request.session.get(
            "user_id"
        )
    )


    if not user_id:

        return None


    return (
        MealMateUser.objects.filter(
            id=user_id,
            is_active=True,
        ).first()
    )


# =========================================================
# BUSINESS ANALYTICS
# =========================================================

def business_analytics(
    request
):

    current_user = (
        get_current_user(
            request
        )
    )


    if not current_user:

        return redirect(
            "login"
        )


    if current_user.role != "business":

        return redirect(
            "dashboard"
        )


    analytics = (
        get_business_analytics(
            current_user.id
        )
    )


    demand_forecast = (
        get_business_demand_forecast(
            current_user.id
        )
    )


    return render(
        request,
        "business_analytics.html",
        {
            "current_user":
                current_user,

            "analytics":
                analytics,

            "demand_forecast":
                demand_forecast,
        }
    )