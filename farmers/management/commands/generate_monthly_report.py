from django.core.management.base import BaseCommand
import redis
import json
from datetime import datetime
import csv
import os
from farmers.models import MonthlyReport

r = redis.Redis(host='localhost', port=6379, db=0)

class Command(BaseCommand):
    help = 'Generate monthly farmer addition report'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, default=datetime.now().year, help='Year for the report')
        parser.add_argument('--month', type=int, default=datetime.now().month, help='Month for the report')

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        month_str = f'{year}-{month:02d}'
        
        # Initialize report data
        report_data = {
            'month': month_str,
            'users': {},
            'blocks': {},
            'total': 0
        }
        report_lines = [f'Monthly Farmer Addition Report for {month_str}']
        total_farmers = 0

        # Use Redis SCAN to find users with counts
        user_ids = set()
        cursor = '0'
        try:
            while True:
                cursor, keys = r.scan(cursor=cursor, match=f'user:*:monthly_farmer_count:{month_str}', count=1000)
                for key in keys:
                    user_id = key.decode().split(':')[1]  # Extract user_id from key
                    user_ids.add(user_id)
                if cursor == 0:
                    break
        except redis.RedisError as e:
            self.stdout.write(self.style.ERROR(f"Failed to scan user counts from Redis: {e}"))
            raise

        # Use Redis pipeline to fetch monthly counts for users
        pipe = r.pipeline()
        for user_id in user_ids:
            pipe.get(f'user:{user_id}:monthly_farmer_count:{month_str}')
        try:
            user_counts = pipe.execute()
        except redis.RedisError as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch user counts from Redis: {e}"))
            raise

        # Process user counts
        user_data = []
        for user_id, count in zip(user_ids, user_counts):
            count = int(count) if count else 0
            report_data['users'][user_id] = count
            report_lines.append(f'User {user_id}: {count} farmers in {month_str}')
            user_data.append({'user_id': user_id, 'count': count})
            total_farmers += count
            self.stdout.write(self.style.SUCCESS(f"User {user_id}: {count} farmers in {month_str}"))

        # Use Redis SCAN to find blocks with counts
        block_ids = set()
        cursor = '0'
        try:
            while True:
                cursor, keys = r.scan(cursor=cursor, match=f'block:*:monthly_farmer_count:{month_str}', count=1000)
                for key in keys:
                    block_id = key.decode().split(':')[1]  # Extract block_id from key
                    block_ids.add(block_id)
                if cursor == 0:
                    break
        except redis.RedisError as e:
            self.stdout.write(self.style.ERROR(f"Failed to scan block counts from Redis: {e}"))
            raise

        # Use Redis pipeline to fetch monthly counts for blocks
        pipe = r.pipeline()
        for block_id in block_ids:
            pipe.get(f'block:{block_id}:monthly_farmer_count:{month_str}')
        try:
            block_counts = pipe.execute()
        except redis.RedisError as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch block counts from Redis: {e}"))
            raise

        # Process block counts
        block_data = []
        for block_id, count in zip(block_ids, block_counts):
            count = int(count) if count else 0
            report_data['blocks'][block_id] = count
            report_lines.append(f'Block {block_id}: {count} farmers in {month_str}')
            block_data.append({'block_id': block_id, 'count': count})
            self.stdout.write(self.style.SUCCESS(f"Block {block_id}: {count} farmers in {month_str}"))

        report_data['total'] = total_farmers
        report_lines.append(f'Total Farmers: {total_farmers}')

        # Store the report in Redis as JSON
        report_json = json.dumps(report_data)
        pipe = r.pipeline()
        pipe.set(f'report:monthly:{month_str}:json', report_json)
        try:
            pipe.execute()
            self.stdout.write(self.style.SUCCESS(f'Report stored in Redis: report:monthly:{month_str}:json'))
        except redis.RedisError as e:
            self.stdout.write(self.style.ERROR(f"Failed to store report in Redis: {e}"))
            raise

        # Save the report as a CSV file
        report_dir = 'C:/Users/DELL/OneDrive/Desktop/project_new/farmer_management/reports/'
        os.makedirs(report_dir, exist_ok=True)
        csv_file_path = os.path.join(report_dir, f'monthly_report_{month_str}.csv')

        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Monthly Farmer Addition Report', month_str])
            writer.writerow([])  # Empty row for spacing
            writer.writerow(['User ID', 'Farmers Added'])
            for user in user_data:
                writer.writerow([user['user_id'], user['count']])
            writer.writerow([])  # Empty row for spacing
            writer.writerow(['Block ID', 'Farmers Added'])
            for block in block_data:
                writer.writerow([block['block_id'], block['count']])
            writer.writerow([])  # Empty row for spacing
            writer.writerow(['Total Farmers', total_farmers])

        self.stdout.write(self.style.SUCCESS(f'Report saved as CSV: {csv_file_path}'))

        # Save the report metadata in the database
        MonthlyReport.objects.update_or_create(
            year=year,
            month=month,
            defaults={'file_path': csv_file_path}
        )