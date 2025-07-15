# Admin User Setup

## Creating the First Superadmin User

To bootstrap the admin system with the first superadmin user, run:

```bash
python scripts/create_admin_user.py
```

Or if you have Python 3 specifically:

```bash
python3 scripts/create_admin_user.py
```

### What the Script Does

1. **Database Setup**: Ensures the database exists and creates admin tables if needed
2. **User Input**: Prompts for:
   - Username (3-50 characters, alphanumeric + underscore)
   - Email address (valid email format)
   - Password (with strength validation)
3. **Password Validation**: Enforces:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one digit
   - At least one special character
4. **User Creation**: Creates a superadmin user with full privileges
5. **Success Message**: Shows login instructions

### Prerequisites

- MySQL database running and accessible
- Database credentials configured in `config.py`
- Python dependencies installed (`requirements.txt`)

### Security Notes

- The script validates password strength to ensure secure accounts
- Passwords are hashed using bcrypt before storage
- The script checks for existing admin users and warns before creating additional superadmins
- Email addresses are normalized to lowercase for consistency

### After Creation

Once you've created the first superadmin user, you can:

1. Log into the admin panel at `/admin` or `/admin/login`
2. Create additional admin users with different role levels:
   - `superadmin`: Full access to all features
   - `admin`: Standard administrative access
   - `viewer`: Read-only access
3. Manage application data and view audit logs

### Troubleshooting

If you encounter issues:

1. **Database Connection Error**: Check your database credentials in `config.py`
2. **Import Errors**: Ensure you're running from the project root directory
3. **Table Creation Errors**: Check database permissions for the configured user
4. **Duplicate User Error**: The username or email already exists in the database