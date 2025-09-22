# FastAPI Timesheet Backend

A production-ready FastAPI backend implementation using raw SQL (no ORM) with MySQL, JWT authentication, and comprehensive timesheet management API endpoints based on the provided DDL schema.

## Features

- **Raw SQL Implementation**: No ORM dependencies, using `databases` with `aiomysql` for async MySQL operations
- **UUID-based Schema**: Full implementation of the provided DDL with UUID primary keys
- **JWT Authentication**: Secure access/refresh token system with bcrypt password hashing
- **Role-based Access Control**: Admin, Manager, and Employee roles with JSON permissions
- **Multi-tenant Architecture**: Organisation and account-based data separation
- **Comprehensive Timesheet Management**: Weekly timesheet entries with approval workflow
- **Leave Management**: Leave requests with approval system
- **Project Management**: Projects with bill codes and user assignments
- **Production Ready**: Structured logging, rate limiting, error handling, and Docker support
- **OpenAPI Documentation**: Auto-generated API docs with security schemes
- **Testing**: Pytest examples with async support

## Database Schema Overview

The system implements a comprehensive timesheet management schema with:

### Core Tables
- **organisation**: Multi-tenant organization management
- **accounts**: Account separation within organizations
- **users**: User management with UUID IDs
- **roles**: Role-based permissions with JSON storage
- **user_roles**: User-role assignments

### Project Management
- **projects**: Project definitions with client information
- **project_bill_code**: Billable codes for project work
- **project_assignments**: User assignments to projects

### Timesheet System
- **timesheet**: Weekly timesheet entries (Mon-Sun)
- **leave_types**: Different types of leave (Annual, Sick, etc.)
- **leave_requests**: Leave request management

### Authentication
- **refresh_tokens**: JWT refresh token management

## Quick Start

### 1. Environment Setup

Create a `.env` file:

```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=timesheet_db

# JWT (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Application
DEBUG=true
```

### 2. Using Docker (Recommended)

Start all services:

```bash
make docker-up
```

This will start:
- MySQL database on port 3306 with the complete schema
- FastAPI application on port 8000

### 3. Manual Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Start MySQL and run migrations:

```bash
make migrate
```

Start the development server:

```bash
make dev
```

## Default Data

After running migrations, the system includes:

### Default Admin User
- **Email**: admin@example.com
- **Username**: admin
- **Password**: admin123

### Default Roles
- **Admin**: Full system access
- **Manager**: Project and timesheet management
- **Employee**: Basic user access

### Sample Data
- Default organization and account
- Leave types (Annual, Sick, Maternity, Emergency, Unpaid)
- Project bill codes (DEV001, DEV002, TEST001, etc.)

**⚠️ Change the admin password immediately in production!**

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (get tokens)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (revoke refresh token)
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/change-password` - Change password

### Users (Planned)
- `GET /api/v1/users/` - List users with roles
- `POST /api/v1/users/` - Create user (admin only)
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Deactivate user

### Projects (Planned)
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `POST /api/v1/projects/{id}/assign` - Assign users to project

### Timesheets (Planned)
- `GET /api/v1/timesheets/` - List timesheet entries
- `POST /api/v1/timesheets/` - Create timesheet entry
- `GET /api/v1/timesheets/{id}` - Get timesheet details
- `PUT /api/v1/timesheets/{id}` - Update timesheet
- `POST /api/v1/timesheets/{id}/submit` - Submit for approval
- `POST /api/v1/timesheets/{id}/approve` - Approve timesheet (admin/manager)

### Leave Management (Planned)
- `GET /api/v1/leave-requests/` - List leave requests
- `POST /api/v1/leave-requests/` - Create leave request
- `GET /api/v1/leave-requests/{id}` - Get leave request details
- `PUT /api/v1/leave-requests/{id}` - Update leave request
- `POST /api/v1/leave-requests/{id}/approve` - Approve leave (admin/manager)

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Example Usage

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Database Schema Details

### Key Design Decisions

1. **UUID Primary Keys**: All main entities use CHAR(36) UUIDs for better distributed system support
2. **Multi-tenancy**: Organisation and account separation for SaaS deployment
3. **Role-based Permissions**: JSON-stored permissions for flexible access control
4. **Weekly Timesheets**: Monday-Sunday columns for traditional timesheet entry
5. **Audit Trail**: created_at/updated_at timestamps on all main tables

### Relationships

```
Organisation (1) -> (N) Accounts
Accounts (1) -> (N) Projects
Users (N) <-> (N) Roles (via user_roles)
Users (N) <-> (N) Projects (via project_assignments)
Project_assignments (1) -> (N) Timesheet
Users (1) -> (N) Leave_requests
```

## Development

### Running Tests

```bash
make test
```

### Code Formatting

```bash
make format
```

### Linting

```bash
make lint
```

### Database Operations

```bash
# Run migrations
make migrate

# Backup database
make backup-db

# Restore database
make restore-db BACKUP_FILE=backup_20240115_120000.sql
```

## Security Features

- **Password Hashing**: bcrypt with configurable rounds
- **JWT Tokens**: Signed with secret key, configurable expiration
- **Parameterized Queries**: All SQL uses parameterized queries to prevent injection
- **Rate Limiting**: Built-in rate limiting with slowapi
- **Input Validation**: Pydantic models for request/response validation
- **Role-based Access**: JSON-based permission system
- **CORS**: Configurable CORS settings
- **Refresh Token Management**: Secure refresh token storage and revocation

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MYSQL_HOST` | MySQL host | localhost |
| `MYSQL_PORT` | MySQL port | 3306 |
| `MYSQL_USER` | MySQL username | root |
| `MYSQL_PASSWORD` | MySQL password | password |
| `MYSQL_DATABASE` | Database name | timesheet_db |
| `JWT_SECRET_KEY` | JWT signing key | (change in production!) |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | 7 |
| `DEBUG` | Debug mode | false |
| `CORS_ORIGINS` | Allowed CORS origins | ["*"] |

## Production Deployment

1. **Change Security Settings**:
   - Generate a strong `JWT_SECRET_KEY`
   - Set `DEBUG=false`
   - Update `CORS_ORIGINS` to specific domains
   - Change default admin password

2. **Database Security**:
   - Use strong MySQL passwords
   - Enable SSL connections
   - Regular backups
   - Monitor for unusual activity

3. **Infrastructure**:
   - Use reverse proxy (nginx/Apache)
   - Enable HTTPS
   - Set up monitoring and logging
   - Configure rate limiting at proxy level

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Pydantic settings configuration
│   ├── db.py                  # Database connection and raw SQL utilities
│   ├── auth/
│   │   ├── router.py          # Authentication endpoints
│   │   ├── service.py         # Authentication business logic
│   │   ├── schemas.py         # Auth Pydantic models
│   │   └── jwt.py             # JWT token utilities
│   ├── routers/               # API route handlers
│   ├── services/              # Business logic layer
│   ├── schemas/               # Pydantic models
│   ├── utils/                 # Utility functions
│   └── tests/                 # Test files
├── schema.sql                 # Complete database schema
├── migrate.sh                 # Migration script
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker services
├── Dockerfile                 # Application container
├── Makefile                   # Common tasks
└── README.md                  # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and linting
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the database schema in `schema.sql`
- Check the logs for error details
- Open an issue for bugs or feature requests