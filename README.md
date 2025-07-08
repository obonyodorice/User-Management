# Django User Management System

A complete user management system with registration, verification, profile management, and admin features.

live link: https://20d-django-project-production.up.railway.app/


## Features

- User registration with email verification
![Registration Page](images/screenshot2.png)

![Login Page](images/screenshot3.png)

- Profile management (view/edit profile, change password)
![User Profile](images/screenshot1.png)

- Admin panel for user management
- User types (Regular/Admin)
- Responsive Bootstrap UI

## Installation

### 1. Clone and Setup
bash
git clone https://github.com/obonyodorice/20D-Django-project.git
cd user_management_system
python -m venv venv


### 2. Activate Virtual Environment
bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate


### 3. Install Dependencies
bash
pip install -r requirements.txt


### 4. Configure Database
bash
python manage.py makemigrations
python manage.py migrate


### 5. Create Superuser
bash
python manage.py createsuperuser


### 6. Run Server
bash
python manage.py runserver


## Usage

### Access Points
- *Home/Profile*: http://localhost:8000/
- *Register*: http://localhost:8000/register/
- *Login*: http://localhost:8000/login/
- *Admin Panel*: http://localhost:8000/admin/user/ (Admin users only)

### User Types
- *Regular Users*: Can view/edit their own profile

- *Admin Users*: Can manage all users + regular user features

## Default Accounts

After creating superuser, you can:
1. Login with superuser credentials
2. Register new users through the registration form
3. Admin users can access the admin panel to manage all users

## File Structure

user_management/
├── accounts/          # Main app
├── static/           # CSS/JS files
├── media/            # Uploaded files
├── templates/        # HTML templates
└── manage.py


## Tech Stack
- Django 4.2.7
- Bootstrap 5
- Crispy Forms
- SQLite (default)

