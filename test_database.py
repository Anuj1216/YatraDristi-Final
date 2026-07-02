from src.database.travel_plan_repository import *

trip_id = save_travel_plan(
    "Biratnagar",
    "Urlabari",
    "2026-07-15",
    "09:00 - 12:00",
    "Car",
)

print("Saved Trip ID:", trip_id)

print()

plans = get_all_travel_plans()

for plan in plans:
    print(plan)