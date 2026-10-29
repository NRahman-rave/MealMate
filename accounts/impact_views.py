from django.shortcuts import (
    redirect,
    render,
)

from .impact_service import (
    get_business_impact,
    get_user_impact,
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
# IMPACT DASHBOARD
# =========================================================

def impact_dashboard(
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


    if current_user.role == "business":

        impact = (
            get_business_impact(
                current_user.id
            )
        )

    else:

        impact = (
            get_user_impact(
                current_user.id
            )
        )


    return render(
        request,
        "impact.html",
        {
            "current_user":
                current_user,

            "impact":
                impact,
        }
    )