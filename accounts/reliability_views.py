from django.shortcuts import (
    redirect,
    render,
)

from .models import (
    MealMateUser,
)

from .reliability_service import (
    get_reliability_summary,
)


def get_current_user(request):

    user_id = request.session.get(
        "user_id"
    )


    if not user_id:
        return None


    return MealMateUser.objects.filter(
        id=user_id,
        is_active=True,
    ).first()



def reliability_page(request):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    summary = (
        get_reliability_summary(
            current_user.id
        )
    )


    return render(
        request,
        "reliability.html",
        {
            "current_user":
                current_user,

            "reliability":
                summary,
        }
    )