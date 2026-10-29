MEALMATE - FULL DJANGO + MYSQL WEBSITE
=====================================

YOUR CURRENT LOCAL STACK
- Django: port 8000
- MySQL 8.4: 127.0.0.1:3307
- Database: mealmate
- Application DB user: mealmate_app

FIRST START
1. Copy .env.example and rename the copy to .env.
2. In .env, replace PASTE_YOUR_EXISTING_PASSWORD_HERE with the password you already use for mealmate_app.
3. Double-click start-mealmate.bat.
4. The starter automatically runs Django migrations, creates any missing MealMate tables, starts Django, and opens http://127.0.0.1:8000/

WHAT WORKS
- User sign up / login / logout
- Business sign up / login / logout
- Role-based dashboard redirect
- User food search and available-food dashboard
- Food detail page
- Clickable Google Maps directions for pickup address
- Reserve food with transaction-safe quantity reduction
- My Reservations page
- User cancellation with quantity restoration
- Business create / edit / pause / reactivate / delete food posts
- Business reservation list
- Business mark collected / cancel reservations
- Account profile editing
- Password changing
- Responsive home interface and original animation
- Django CSRF protection and password hashing

IMPORTANT
Do not put your MySQL password in files you share publicly. The .env file is ignored by .gitignore.

LOCAL URL
http://127.0.0.1:8000/

PHPMYADMIN
Your MealMate data is on the MySQL server at port 3307, not the older XAMPP database server at 3306.
