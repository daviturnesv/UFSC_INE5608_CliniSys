# CliniSys-Escola Copilot Instructions

This is a desktop clinic management system for educational use (UFSC INE5608 coursework). The system manages users with different profiles (admin, professor, aluno, recepcionista), patients, clinics, and queues in a healthcare educational environment.

## Architecture Overview

- **Desktop Application**: Tkinter-based GUI with async backend integration
- **Database**: SQLite with SQLAlchemy async ORM and Alembic migrations
- **Authentication**: JWT tokens with bcrypt password hashing
- **Pattern**: MVC architecture with async/await throughout

## Essential Code Patterns

### Async Database Sessions
```python
from src.backend.db.database import AsyncSessionLocal

# Always use async context manager
async with AsyncSessionLocal() as session:
    # Database operations here
    result = await session.execute(select(...))
    await session.commit()
```

### Model Structure
- All models inherit from `Base` in `src.backend.db.database`
- Users have role-based profiles (1:1 relationships with role-specific data)
- Timestamps use `server_default=func.now()` and `onupdate=func.now()`
- Foreign keys follow pattern: `"table_name.id"` with proper CASCADE settings

### User Profiles System
```python
# Core user in UsuarioSistema with PerfilUsuario enum
class PerfilUsuario(enum.Enum):
    admin = "admin"
    professor = "professor" 
    aluno = "aluno"
    recepcionista = "recepcionista"

# Role-specific data in separate tables (PerfilProfessor, PerfilRecepcionista, etc.)
```

### Tkinter Async Integration
```python
import asyncio
from tkinter import ttk

class MyWidget(ttk.Frame):
    def async_action_handler(self):
        """Handle async operations from Tkinter"""
        asyncio.create_task(self._async_operation())
    
    async def _async_operation(self):
        # Async database/backend calls here
        pass
```

## Project Structure Guide

### Backend (`src/backend/`)
- **`models/`**: SQLAlchemy models with async patterns
- **`controllers/`**: Business logic and database operations  
- **`db/database.py`**: Database configuration and session management
- **`core/config.py`**: Settings using Pydantic BaseSettings
- **`main.py`**: FastAPI application (if needed)

### Desktop Client (`src/client_desktop/`)
- **`clinisys_main.py`**: Main application entry point
- **`login_tk.py`**: Authentication dialog
- **User management modules**: Each functional area has dedicated UI module

### Database
- **Migrations**: Alembic in `alembic/versions/`
- **Demo Data**: `scripts/populate_demo_data.py` for test data
- **Connection**: Async SQLite via `settings.database_url`

## Configuration

Settings are centralized in `src.backend.core.config.Settings`:
```python
DATABASE_URL = "sqlite+aiosqlite:///./clinisys.db"
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

## Common Operations

### Running the Application
```bash
# Main desktop app
python -m src.client_desktop

# Populate demo data
python scripts/populate_demo_data.py

# Run tests
pytest

# Database migrations
alembic upgrade head
```

### Creating New Models
1. Add to `src/backend/models/`
2. Import in `models/__init__.py`
3. Create migration: `alembic revision --autogenerate -m "description"`
4. Apply: `alembic upgrade head`

### Adding UI Components
- Use async-aware event handlers for database operations
- Follow existing patterns in `login_tk.py` and `clinisys_main.py`
- Use `AsyncSessionLocal()` context manager for database access

## Authentication Flow
1. Login via `LoginDialog` in `login_tk.py`
2. Authenticate through `authenticate_user()` service
3. Store user session data for profile-based menu access
4. Different UI based on `PerfilUsuario` enum

## Testing Patterns
- Tests in `tests/` directory using pytest
- `conftest.py` provides database fixtures
- Async test functions with `pytest-asyncio`
- Separate test files by functionality

## Key Dependencies
- **GUI**: tkinter (built-in)
- **Database**: SQLAlchemy async, aiosqlite, alembic
- **Auth**: python-jose[cryptography], passlib[bcrypt]
- **Config**: pydantic-settings
- **Testing**: pytest, pytest-asyncio

## Development Workflow
1. Create/modify models in `backend/models/`
2. Generate migrations with Alembic
3. Update controllers/services as needed
4. Modify/create UI components in `client_desktop/`
5. Add tests for new functionality
6. Use demo data script for testing

## Important Notes
- All database operations must be async
- Use proper async context managers for sessions
- Profile-based access control throughout UI
- Educational context - designed for learning healthcare IT
- SQLite database for simplicity in academic environment