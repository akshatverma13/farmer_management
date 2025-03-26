# Farmer Management System

## Overview
The **Farmer Management System** is a Django-based web application designed to manage farmer records across blocks. It provides role-based access control, allowing different types of users (admin, supervisor, surveyor) to perform specific actions based on their permissions. The system also includes asynchronous task processing using **Celery** for generating monthly reports, with media and report files stored in the repository.

## Features
- **User Authentication and Role Management**:
  - Custom user model with roles: **Admin**, **Supervisor**, and **Surveyor**.
  - Role-based access control to ensure secure and appropriate access to features.
  - API-based authentication using **Django REST Framework's** token authentication.

- **Block Management**:
  - Admins can add, edit, and delete blocks.
  - Supervisors and Surveyors can view blocks they are assigned to.

- **Farmer Management**:
  - Add, edit, and delete farmer records.
  - Store farmer details including name, Aadhar ID, and associated documents.
  - Track which user added each farmer.

- **Dashboard and Profile Management**:
  - Role-specific dashboards for quick access to relevant information.
  - Users can view and edit their profiles and change passwords.

- **Asynchronous Tasks**:
  - Uses **Celery** for asynchronous task processing (e.g., generating reports).
  - Reports are stored in the `reports/` folder.

## Installation

### Clone the repository
Clone the repository to your local machine:
```bash
git clone https://github.com/yourusername/farmer-management-system.git
cd farmer-management-system
```

### Install dependencies
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Run migrations
Apply the necessary database migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create a superuser (admin user)
Create an admin user to access the admin dashboard:
```bash
python manage.py createsuperuser
```
Example: Username: `admin`, Password: `admin@12345`.

### Create groups
Create the required groups for users (e.g., **Surveyors**, **Supervisors**):
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import Group
Group.objects.create(name='Surveyors')
Group.objects.create(name='Supervisors')
exit()
```

### Start the Redis server (for Celery purpose)
Ensure Redis is installed and running.

- On Linux/macOS:
```bash
redis-server
```
The default Redis URL is `redis://localhost:6379/0`.

### Start the Celery worker
In a new terminal, start the Celery worker:
```bash
celery -A farmer_management worker --loglevel=info -P eventlet
celery -A farmer_management beat --loglevel=info
```

### Start the development server
Back in the original terminal, start the Django development server:
```bash
python manage.py runserver
```

### Access the application
Open your web browser and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
