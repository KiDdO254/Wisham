# Rental Management System

A Django-based rental management system tailored for the Kenyan market.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js and npm (for TailwindCSS compilation)

### Installation

1. **Activate virtual environment:**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install TailwindCSS dependencies (requires Node.js):**
   ```bash
   python manage.py tailwind install
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server:**
   ```bash
   python manage.py runserver
   ```

7. **In another terminal, start TailwindCSS compilation (requires Node.js):**
   ```bash
   python manage.py tailwind start
   ```

## Project Structure

- `properties/` - Property and rental unit management
- `users/` - Custom user model and authentication
- `payments/` - Paystack payment integration
- `maintenance/` - Maintenance request management
- `reports/` - Reporting and analytics
- `theme/` - TailwindCSS theme configuration
- `static/` - Static files (CSS, JS, images)

## Environment Variables

Copy `.env` file and update the following variables:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `PAYSTACK_PUBLIC_KEY` - Paystack public key
- `PAYSTACK_SECRET_KEY` - Paystack secret key

## Features

- Role-based access control (Admin, Property Manager, Landlord, Tenant)
- Property and rental unit management
- Paystack payment integration (M-Pesa and card payments)
- Maintenance request tracking
- Reporting and analytics
- Mobile-responsive design with TailwindCSS
- Enhanced admin interface with Django Unfold

## Technology Stack

- **Backend:** Django 5.2+
- **Database:** SQLite (development)
- **Frontend:** TailwindCSS v4 with shadcn design principles
- **Admin:** Django Unfold
- **Payments:** Paystack API
- **Authentication:** Django built-in with custom roles
