from datetime import datetime, time, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import FoodPost, MealMateUser


BUSINESSES = [
    {
        "name": "Green Spoon Café",
        "email": "greenspoon@mealmate-demo.com",
        "phone": "07111111111",
        "address": "12 The Grove, Stratford, London E15 1NS",
        "foods": [
            ("Chicken Sandwich", "Freshly made chicken sandwich with salad.", 5),
            ("Tuna Pasta Box", "Cold tuna pasta prepared for lunchtime collection.", 4),
            ("Veggie Wrap", "Grilled vegetable wrap with hummus.", 6),
            ("Fruit Pot", "Mixed fruit pot with grapes, melon and berries.", 7),
            ("Croissant Pack", "Butter croissants packed at the end of breakfast.", 8),
        ],
    },
    {
        "name": "Docklands Lunch Hub",
        "email": "docklands@mealmate-demo.com",
        "phone": "07222222222",
        "address": "25 Bank Street, Canary Wharf, London E14 5JP",
        "foods": [
            ("Chicken Caesar Salad", "Ready-made salad bowls from lunch service.", 5),
            ("Beef Panini", "Toasted beef panini ready for collection.", 3),
            ("Tomato Soup Cup", "Fresh tomato soup portions.", 6),
            ("Pesto Pasta", "Basil pesto pasta with cherry tomatoes.", 5),
            ("Blueberry Muffin", "Bakery muffins left after breakfast trade.", 9),
        ],
    },
    {
        "name": "East End Bakery",
        "email": "eastendbakery@mealmate-demo.com",
        "phone": "07333333333",
        "address": "81 Whitechapel Road, Whitechapel, London E1 1DU",
        "foods": [
            ("Cheese Twist", "Fresh bakery cheese twists.", 10),
            ("Chocolate Doughnut", "Soft doughnuts filled with chocolate.", 8),
            ("Chicken Pasty", "Warm chicken pasties ready to collect.", 5),
            ("Cinnamon Roll", "Sweet cinnamon rolls from the afternoon batch.", 7),
            ("Ham & Cheese Baguette", "Baguettes prepared for takeaway customers.", 4),
        ],
    },
    {
        "name": "Campus Bites Kitchen",
        "email": "campusbites@mealmate-demo.com",
        "phone": "07444444444",
        "address": "44 Mile End Road, Mile End, London E1 4PE",
        "foods": [
            ("Penne Arrabbiata", "Ready-made spicy penne pasta boxes.", 6),
            ("Chicken Rice Box", "Grilled chicken with rice and vegetables.", 5),
            ("Falafel Box", "Falafel with couscous and mixed salad.", 7),
            ("Egg Mayo Sandwich", "Freshly packed sandwiches.", 5),
            ("Banana Loaf Slice", "Slices of banana loaf.", 8),
        ],
    },
    {
        "name": "Ilford Family Grill",
        "email": "ilfordgrill@mealmate-demo.com",
        "phone": "07555555555",
        "address": "102 High Road, Ilford, Essex IG1 1BY",
        "foods": [
            ("Chicken Burger Meal", "Burger meals prepared for takeaway rush.", 4),
            ("Lamb Wrap", "Grilled lamb wrap with sauce.", 5),
            ("Peri Peri Wings", "Portions of spicy wings.", 6),
            ("Fries Box", "Fresh fries portions ready before closing.", 8),
            ("Mixed Grill Rice", "Rice box with mixed grilled meat.", 3),
        ],
    },
    {
        "name": "Barking Fresh Foods",
        "email": "barkingfresh@mealmate-demo.com",
        "phone": "07666666666",
        "address": "55 Ripple Road, Barking, Essex IG11 7NP",
        "foods": [
            ("Chicken Tikka Wrap", "Chicken tikka wrap from evening service.", 5),
            ("Pasta Salad", "Cold pasta salad bowls.", 6),
            ("Vegetable Curry Box", "Homestyle veg curry with rice.", 4),
            ("Naan Pack", "Fresh naan breads packed for quick collection.", 8),
            ("Brownie Slice", "Chocolate brownie slices.", 7),
        ],
    },
    {
        "name": "Romford Roast House",
        "email": "romfordroast@mealmate-demo.com",
        "phone": "07777777777",
        "address": "17 South Street, Romford, Essex RM1 1NJ",
        "foods": [
            ("Roast Chicken Box", "Roast chicken with potatoes and veg.", 5),
            ("Mac and Cheese", "Hot mac and cheese portions.", 6),
            ("Turkey Sandwich", "Turkey sandwich packs.", 4),
            ("Stuffing Roll", "Soft rolls with stuffing.", 6),
            ("Apple Crumble Cup", "Dessert cups from today's service.", 5),
        ],
    },
    {
        "name": "Camden Vegan Table",
        "email": "camdenvegan@mealmate-demo.com",
        "phone": "07888888888",
        "address": "33 Camden High Street, Camden, London NW1 7JE",
        "foods": [
            ("Vegan Burrito", "Plant-based burritos with beans and rice.", 5),
            ("Tofu Noodle Box", "Tofu noodles with vegetables.", 6),
            ("Chickpea Salad", "Protein salad bowls.", 7),
            ("Vegan Cookie Pack", "Fresh vegan cookies.", 10),
            ("Mushroom Wrap", "Mushroom wrap with vegan mayo.", 5),
        ],
    },
    {
        "name": "Wembley Spice Corner",
        "email": "wembleyspice@mealmate-demo.com",
        "phone": "07999999999",
        "address": "61 Ealing Road, Wembley, Middlesex HA0 4BA",
        "foods": [
            ("Chicken Biryani Box", "Single biryani portions.", 6),
            ("Paneer Roll", "Paneer rolls packed for takeaway.", 5),
            ("Samosa Pack", "Crispy samosas in portions of two.", 9),
            ("Daal Rice Box", "Lentil daal with rice.", 5),
            ("Gulab Jamun Cup", "Dessert cups ready for collection.", 7),
        ],
    },
    {
        "name": "Croydon Daily Kitchen",
        "email": "croydonkitchen@mealmate-demo.com",
        "phone": "07000000001",
        "address": "89 North End, Croydon, London CR0 1TN",
        "foods": [
            ("Chicken Alfredo Pasta", "Creamy pasta portions left after lunch.", 5),
            ("Ham Toastie", "Grilled ham toasties.", 6),
            ("Soup & Bread", "Soup cups with bread rolls.", 4),
            ("Tuna Melt", "Tuna melt sandwiches.", 5),
            ("Vanilla Cupcake", "Cupcakes from today's bakery shelf.", 8),
        ],
    },
    {
        "name": "Ealing Food Bar",
        "email": "ealingfoodbar@mealmate-demo.com",
        "phone": "07000000002",
        "address": "21 Broadway, Ealing, London W5 2NH",
        "foods": [
            ("Chicken Katsu Box", "Katsu chicken with rice.", 4),
            ("Avocado Sandwich", "Fresh avocado sandwich packs.", 6),
            ("Pasta Bake", "Oven-baked pasta portions.", 5),
            ("Greek Salad", "Mixed Greek-style salad bowls.", 6),
            ("Lemon Drizzle Slice", "Cake slices from the bakery counter.", 8),
        ],
    },
    {
        "name": "Brixton Market Kitchen",
        "email": "brixtonkitchen@mealmate-demo.com",
        "phone": "07000000003",
        "address": "8 Electric Avenue, Brixton, London SW9 8JX",
        "foods": [
            ("Jerk Chicken Rice", "Caribbean-style rice boxes.", 5),
            ("Veggie Rice Bowl", "Rice bowl with beans and vegetables.", 6),
            ("Chicken Patty", "Fresh patties from the hot counter.", 8),
            ("Pasta Pot", "Hot pasta pots prepared for quick collection.", 5),
            ("Coconut Cake Slice", "Sweet coconut cake slices.", 7),
        ],
    },
]


class Command(BaseCommand):
    help = "Create realistic demo business accounts and 50-60 demo food posts."

    def make_datetime(self, day_offset, hour_value, minute_value=0):
        target_date = timezone.localdate() + timedelta(days=day_offset)
        naive_value = datetime.combine(
            target_date,
            time(hour_value, minute_value)
        )
        return timezone.make_aware(
            naive_value,
            timezone.get_current_timezone()
        )

    def handle(self, *args, **options):
        target_total = 60
        created_businesses = 0
        created_posts = 0

        # -------------------------------------------------
        # Create / update demo business accounts
        # -------------------------------------------------
        business_map = {}

        for business in BUSINESSES:
            user = MealMateUser.objects.filter(
                email=business["email"]
            ).first()

            if not user:
                user = MealMateUser.objects.create(
                    full_name=business["name"],
                    email=business["email"],
                    password_hash=make_password("DemoBusiness123!"),
                    role="business",
                    phone=business["phone"],
                    is_active=True,
                )
                created_businesses += 1
            else:
                user.full_name = business["name"]
                user.role = "business"
                user.phone = business["phone"]
                user.is_active = True
                user.save(
                    update_fields=[
                        "full_name",
                        "role",
                        "phone",
                        "is_active",
                    ]
                )

            business_map[business["email"]] = user

        # -------------------------------------------------
        # Build a realistic post pool
        # -------------------------------------------------
        post_pool = []

        for business_index, business in enumerate(BUSINESSES):
            for food_index, food in enumerate(business["foods"]):
                food_name, description, quantity = food

                day_offset = (business_index + food_index) % 4

                if food_index == 0:
                    start_hour = 11
                    end_hour = 13
                elif food_index == 1:
                    start_hour = 12
                    end_hour = 14
                elif food_index == 2:
                    start_hour = 13
                    end_hour = 15
                elif food_index == 3:
                    start_hour = 17
                    end_hour = 19
                else:
                    start_hour = 18
                    end_hour = 20

                post_pool.append(
                    {
                        "business_email": business["email"],
                        "pickup_address": business["address"],
                        "food_name": food_name,
                        "description": description,
                        "quantity": quantity,
                        "pickup_start": self.make_datetime(day_offset, start_hour, 0),
                        "pickup_end": self.make_datetime(day_offset, end_hour, 0),
                        "status": "available",
                    }
                )

        # -------------------------------------------------
        # Create up to 60 total posts
        # Avoid duplicates if same business + food + address already exists
        # -------------------------------------------------
        current_total = FoodPost.objects.count()

        if current_total >= target_total:
            self.stdout.write(
                self.style.WARNING(
                    f"Food posts already exist ({current_total}). No new posts added."
                )
            )
        else:
            for item in post_pool:
                if FoodPost.objects.count() >= target_total:
                    break

                business_user = business_map[item["business_email"]]

                exists = FoodPost.objects.filter(
                    business_id=business_user.id,
                    food_name=item["food_name"],
                    pickup_address=item["pickup_address"],
                ).exists()

                if exists:
                    continue

                FoodPost.objects.create(
                    business_id=business_user.id,
                    food_name=item["food_name"],
                    description=item["description"],
                    quantity=item["quantity"],
                    pickup_address=item["pickup_address"],
                    pickup_start=item["pickup_start"],
                    pickup_end=item["pickup_end"],
                    status=item["status"],
                )

                created_posts += 1

        final_total = FoodPost.objects.count()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("MealMate demo data completed.")
        )
        self.stdout.write(f"Business accounts created: {created_businesses}")
        self.stdout.write(f"Food posts created: {created_posts}")
        self.stdout.write(f"Total food posts now: {final_total}")
        self.stdout.write("")
        self.stdout.write("Demo business login password:")
        self.stdout.write("DemoBusiness123!")
        self.stdout.write("")
        self.stdout.write("Examples you can search on the user dashboard:")
        self.stdout.write("Chicken")
        self.stdout.write("Pasta")
        self.stdout.write("Ilford")
        self.stdout.write("Stratford")
        self.stdout.write("Canary Wharf")
        self.stdout.write("Green Spoon")
        self.stdout.write("Docklands")