from django.core.management.base import BaseCommand
import redis
import json
import os
from datetime import datetime

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
            'users': {},
            'blocks': {},
            'total': 0
        }
        report_lines = [f'Monthly Farmer Addition Report for {month_str}']
        total_farmers = 0

        # Use Redis SCAN to find users with counts
        user_ids = set()
        cursor = '0'
        while True:
            cursor, keys = r.scan(cursor=cursor, match=f'user:*:monthly_farmer_count:{month_str}')
            for key in keys:
                user_id = key.decode().split(':')[1]  # Extract user_id from key
                user_ids.add(user_id)
            if cursor == 0:
                break

        # Use Redis pipeline to fetch monthly counts for users
        pipe = r.pipeline()
        for user_id in user_ids:
            pipe.get(f'user:{user_id}:monthly_farmer_count:{month_str}')
        user_counts = pipe.execute()

        # Process user counts
        for user_id, count in zip(user_ids, user_counts):
            count = int(count) if count else 0
            report_data['users'][user_id] = count
            report_lines.append(f'User {user_id}: {count} farmers in {month_str}')
            total_farmers += count
            self.stdout.write(self.style.SUCCESS(f"User {user_id}: {count} farmers in {month_str}"))

        # Use Redis SCAN to find blocks with counts
        block_ids = set()
        cursor = '0'
        while True:
            cursor, keys = r.scan(cursor=cursor, match=f'block:*:monthly_farmer_count:{month_str}')
            for key in keys:
                block_id = key.decode().split(':')[1]  # Extract block_id from key
                block_ids.add(block_id)
            if cursor == 0:
                break

        # Use Redis pipeline to fetch monthly counts for blocks
        pipe = r.pipeline()
        for block_id in block_ids:
            pipe.get(f'block:{block_id}:monthly_farmer_count:{month_str}')
        block_counts = pipe.execute()

        # Process block counts
        for block_id, count in zip(block_ids, block_counts):
            count = int(count) if count else 0
            report_data['blocks'][block_id] = count
            report_lines.append(f'Block {block_id}: {count} farmers in {month_str}')
            self.stdout.write(self.style.SUCCESS(f"Block {block_id}: {count} farmers in {month_str}"))

        report_data['total'] = total_farmers
        report_lines.append(f'Total Farmers: {total_farmers}')

        # Store the report in Redis as JSON
        report_json = json.dumps(report_data)
        r.set(f'report:monthly:{month_str}', report_json)
        self.stdout.write(self.style.SUCCESS(f"Report stored in Redis: report:monthly:{month_str}"))

        # Write the report to a text file
        base_dir = r'C:\Users\DELL\OneDrive\Desktop\project_new\farmer_management'
        filename = os.path.join(base_dir, f'monthly_farmer_report_{month_str}.txt')
        try:
            os.makedirs(base_dir, exist_ok=True)
            with open(filename, 'w') as f:
                f.write('\n'.join(report_lines))
            self.stdout.write(self.style.SUCCESS(f'Report generated: {filename}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to write report file {filename}: {e}"))
            raise