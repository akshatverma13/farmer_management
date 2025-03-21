# from celery import shared_task
# from django.core.management import call_command
# import redis
# from datetime import datetime

# r = redis.Redis(host='localhost', port=6379, db=0)

# @shared_task
# def update_daily_farmer_counts(user_id, date_str):
#     key = f'user:{user_id}:daily_farmer_count:{date_str}'
#     r.incr(key)  # Increment the count by 1
#     return f"Incremented daily farmer count for user {user_id} on {date_str}"

# @shared_task
# def increment_block_farmer_count(block_id, date_str):
#     key = f'block:{block_id}:farmer_count:{date_str}'
#     r.incr(key)  # Increment the count by 1
#     return f"Incremented block farmer count for block {block_id} on {date_str}"

# @shared_task
# def generate_monthly_report_task(year=None, month=None):
#     if year is None:
#         year = datetime.now().year
#     if month is None:
#         month = datetime.now().month
#     call_command('generate_monthly_report', year=year, month=month)
#     return f"Monthly farmer report generated for {year}-{month:02d}"


from celery import shared_task
from django.core.management import call_command
import redis
from datetime import datetime, timedelta

r = redis.Redis(host='localhost', port=6379, db=0)

@shared_task
def update_daily_farmer_counts(user_id, date_str, month_str):
    pipe = r.pipeline()
    daily_key = f'user:{user_id}:daily_farmer_count:{date_str}' #user:3:daily_farmer_count:2025-03-20
    monthly_key = f'user:{user_id}:monthly_farmer_count:{month_str}' #user:3:monthly_farmer_count:2025-03
    pipe.incr(daily_key)  # Increment daily count #single network request
    pipe.incr(monthly_key)  # Increment monthly count
    pipe.execute()
    return f"Incremented counts for user {user_id} on {date_str} and {month_str}"

@shared_task
def increment_block_farmer_count(block_id, date_str, month_str):
    pipe = r.pipeline()
    daily_key = f'block:{block_id}:farmer_count:{date_str}'
    monthly_key = f'block:{block_id}:monthly_farmer_count:{month_str}'
    pipe.incr(daily_key)  # Increment daily count #block:1:farmer_count:2025-03-20.
    pipe.incr(monthly_key)  # Increment monthly count # block:1:monthly_farmer_count:2025-03
    pipe.execute()
    return f"Incremented counts for block {block_id} on {date_str} and {month_str}"

@shared_task
def run_monthly_farmer_report(year=None, month=None):
    # If year and month are not provided, use the previous month
    if year is None or month is None:
        today = datetime.now()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        year = last_day_of_previous_month.year
        month = last_day_of_previous_month.month
    call_command('generate_monthly_report', year=year, month=month)
    return f"Monthly farmer report generated for {year}-{month:02d}"


