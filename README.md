Farmer Management System
Overview
The Farmer Management System is a Django-based web application designed to manage farmer records across different geographical blocks. It provides role-based access control, allowing different types of users (admin, supervisor, surveyor) to perform specific actions based on their permissions. The system also includes asynchronous task processing using Celery for generating reports, with media and report files stored in the repository for easy setup.

Features
User Authentication and Role Management:

Custom user model with roles: Admin, Supervisor, and Surveyor.

Role-based access control to ensure secure and appropriate access to features.

API-based authentication using Django REST Framework's token authentication.

Block Management:

Admins can add, edit, and delete blocks.

Supervisors and Surveyors can view blocks they are assigned to.

Farmer Management:

Add, edit, and delete farmer records.

Store farmer details including name, Aadhar ID, and associated documents.

Track which user added each farmer.

Dashboard and Profile Management:

Role-specific dashboards for quick access to relevant information.

Users can view and edit their profiles and change passwords.

Asynchronous Tasks:

Uses Celery for asynchronous task processing (e.g., generating reports).

Reports are stored in the reports/ folder.

Project Structure
Models:

Block: Represents geographical or administrative units.

User: Custom user model extending Django's AbstractUser with role-based permissions.

Farmer: Represents individual farmers with personal details and documents.

UserProfile: Stores additional user information (e.g., associated block).

Views:

Authentication views for login and logout.

CRUD operations for blocks and farmers.

Profile management views.

Legacy views for backward compatibility (e.g., api_farmers).

Templates:

Base templates for consistent styling.

Role-specific dashboards and forms for managing blocks and farmers.

Static Files:

CSS for styling and layout.

JavaScript for interactive features.

Media Files:

media/: Stores user and farmer documents.

reports/: Stores generated reports (e.g., monthly reports).

Installation
Follow the steps below to set up the project locally:

1. Clone the Repository:
bash
Copy
git clone https://github.com/yourusername/farmer-management-system.git
cd farmer-management-system
2. Install Dependencies:
bash
Copy
pip install -r requirements.txt
3. Run Migrations:
bash
Copy
python manage.py migrate
4. Create a Superuser (Admin User):
bash
Copy
python manage.py createsuperuser
Example: Username: admin, Password: admin@12345.

5. Create Groups for Role-based Access:
bash
Copy
python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.create(name='Surveyors'); Group.objects.create(name='Supervisors')"
6. Create Initial Blocks:
bash
Copy
python manage.py shell -c "from farmers.models import Block; Block.objects.create(name='Block A'); Block.objects.create(name='Block B')"
7. Start Redis Server (Required for Celery):
Make sure Redis is installed on your system.

On Linux/macOS:

bash
Copy
redis-server
On Windows, you can either install Redis or use Docker:

bash
Copy
docker run -d -p 6379:6379 redis
The default Redis URL is redis://localhost:6379/0.

8. Start Celery Worker:
Open a new terminal window in the project directory and run:

bash
Copy
celery -A farmer_management worker --loglevel=info
9. Start the Development Server:
In the original terminal window, run:

bash
Copy
python manage.py runserver
10. Access the Application:
Open your browser and go to http://127.0.0.1:8000/.

Final Remarks:
Redis: If Redis is not installed or running, Celery won't be able to process asynchronous tasks.

Celery Worker: Celery must be running to handle background tasks like report generation. You can stop it later by pressing Ctrl+C in the terminal where it's running.

This README.md is now properly structured for GitHub, with clearly defined steps. Copy-pasting this into your GitHub repository's README.md file will make it easier for users to understand and follow the setup instructions.
