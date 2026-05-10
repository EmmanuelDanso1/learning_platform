# AGENTS.md

## Purpose
This file provides guidance for AI coding agents working on the learning platform project. It outlines key conventions, architecture, and workflows to ensure productivity and adherence to project standards.

---

## Project Overview
- **Framework**: Flask
- **Database**: SQLAlchemy ORM
- **Authentication**: Dual system (Admin/User)
- **File Storage**: UUID-based naming in `static/uploads/`
- **Rate Limiting**: Flask-Limiter (200/day, 50/hour)
- **Payment Integration**: Paystack

---

## Key Conventions

### Naming Patterns
| **Component** | **Pattern** |
|---------------|-------------|
| Blueprints    | `*_bp`      |
| Routes        | Snake-case URLs |
| Classes       | PascalCase  |

### Authentication
- **Admin**: `admin_id` foreign key
- **User**: `user_id` foreign key
- OTP verification for login

### File Uploads
- **Storage**: `static/uploads/{resource_type}/`
- **Naming**: UUID + secure filenames

### Error Handling
- **Logging**: RotatingFileHandler to `logs/fliers.log`
- **API Responses**: JSON format

---

## Build & Test Commands

| **Task**          | **Command**              |
|-------------------|--------------------------|
| Start server      | `python run.py`          |
| DB migrations     | `flask db migrate` → `flask db upgrade` |
| Install deps      | `pip install -r requirements.txt` |

---

## Development Workflows

### Adding a New Route
1. Create a new file in `learning_app/realmind/routes/`.
2. Define the route using the appropriate blueprint.
3. Register the blueprint in `create_app()`.

### Database Migrations
1. Modify models in `learning_app/realmind/models/`.
2. Run `flask db migrate -m "Migration message"`.
3. Apply changes with `flask db upgrade`.

### File Upload Handling
1. Validate file type using `allowed_file()` in `utils.py`.
2. Save files to `static/uploads/{resource_type}/`.
3. Use UUIDs for filenames.

---

## Topics for Further Documentation
- API Token Authentication
- Swagger/OpenAPI Integration
- Example `.env` file
- Unit Testing with Pytest

---

## Contact
For questions or issues, refer to the project lead or consult the `logs/` directory for debugging information.