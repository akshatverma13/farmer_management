# Farmer Management System

## Overview
The Farmer Management System is a Django-based web application designed to manage farmer records across different geographical blocks. It provides role-based access control, allowing different types of users (admin, supervisor, surveyor) to perform specific actions based on their permissions. The system also includes asynchronous task processing using Celery for generating reports, with media and report files stored in the repository for easy setup.

## Features
- **User Authentication and Role Management**:
  - Custom user model with roles: Admin, Supervisor, and Surveyor.
  - Role-based access control to ensure secure and appropriate access to features.
  - API-based authentication using Django REST Framework's token authentication.

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
  - Uses Celery for asynchronous task processing (e.g., generating reports).
  - Reports are stored in the `reports/` folder.

## Project Structure
- **Models**:
  - `Block`: Represents geographical or administrative units.
  - `User`: Custom user model extending Django's AbstractUser with role-based permissions.
  - `Farmer`: Represents individual farmers with personal details and documents.
  - `UserProfile`: Stores additional user information (e.g., associated block).

- **Views**:
  - Authentication views for login and logout.
  - CRUD operations for blocks and farmers.
  - Profile management views.
  - Legacy views for backward compatibility (e.g., `api_farmers`).

- **Templates**:
  - Base templates for consistent styling.
  - Role-specific dashboards and forms for managing blocks and farmers.

- **Static Files**:
  - CSS for styling and layout.
  - JavaScript for interactive features.

- **Media Files**:
  - `media/`: Stores user and farmer documents.
  - `reports/`: Stores generated reports (e.g., monthly reports).

## Installation

### Clone the repository
Clone the repository to your local machine:
```bash
git clone https://github.com/yourusername/farmer-management-system.git
cd farmer-management-system
