import re
from email_validator import validate_email, EmailNotValidError
from app.utils.errors import ValidationError

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")

def validate_registration_payload(data: dict) -> dict:
    """
    Validates registration fields: email, username, password, full_name.
    Explicitly strips any attempted role override to prevent privilege escalation.
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object")

    email = str(data.get("email", "")).strip().lower()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    full_name = str(data.get("full_name", "")).strip()

    errors = []

    # Email validation
    if not email:
        errors.append("Email is required")
    else:
        try:
            valid = validate_email(email, check_deliverability=False)
            email = valid.normalized
        except EmailNotValidError as e:
            errors.append(f"Invalid email address: {str(e)}")

    # Username validation
    if not username:
        errors.append("Username is required")
    elif not USERNAME_REGEX.match(username):
        errors.append("Username must be 3-30 characters long and contain only letters, numbers, underscores, and hyphens")

    # Password validation
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    elif not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one letter and one number")

    # Full name validation
    if not full_name:
        errors.append("Full name is required")
    elif len(full_name) < 2 or len(full_name) > 100:
        errors.append("Full name must be between 2 and 100 characters")

    if errors:
        raise ValidationError("Validation failed", details=errors)

    # Return clean, sanitized dictionary with role strictly omitted
    return {
        "email": email,
        "username": username,
        "password": password,
        "full_name": full_name
    }


def validate_login_payload(data: dict) -> dict:
    """Validates login fields: identifier (email or username) and password."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object")

    identifier = str(data.get("identifier", "")).strip()
    password = str(data.get("password", ""))

    if not identifier:
        raise ValidationError("Email or username is required")
    if not password:
        raise ValidationError("Password is required")

    return {
        "identifier": identifier,
        "password": password
    }


def validate_change_password_payload(data: dict) -> dict:
    """Validates old and new passwords."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object")

    old_password = str(data.get("old_password", ""))
    new_password = str(data.get("new_password", ""))

    errors = []
    if not old_password:
        errors.append("Current password is required")
    if not new_password:
        errors.append("New password is required")
    elif len(new_password) < 8:
        errors.append("New password must be at least 8 characters long")
    elif not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
        errors.append("New password must contain at least one letter and one number")
    elif old_password == new_password:
        errors.append("New password must be different from current password")

    if errors:
        raise ValidationError("Password validation failed", details=errors)

    return {
        "old_password": old_password,
        "new_password": new_password
    }


from decimal import Decimal, InvalidOperation

MAX_AMOUNT_PAISE = 1_000_000_000  # 1 Crore INR (10,000,000.00 INR in paise)

def parse_amount_to_paise(data: dict, field_name: str = "amount", allow_zero: bool = False) -> int:
    """
    Parses and validates a monetary amount from the payload and converts to integer paise.
    Supports either 'amount' (decimal INR) or 'amount_paise' (exact integer).
    Uses Decimal to strictly prevent floating-point precision issues.
    """
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object")

    raw_val = None
    is_direct_paise = False

    if "amount_paise" in data and data["amount_paise"] is not None:
        raw_val = data["amount_paise"]
        is_direct_paise = True
    elif field_name in data and data[field_name] is not None:
        raw_val = data[field_name]
    else:
        raise ValidationError(f"Field '{field_name}' or 'amount_paise' is required")

    try:
        if is_direct_paise:
            if isinstance(raw_val, float):
                raise ValidationError("amount_paise must be an exact integer, not a float")
            paise = int(raw_val)
        else:
            d = Decimal(str(raw_val).strip())
            # Reject fractional paise (more than 2 decimal places in rupees)
            if d.as_tuple().exponent < -2:
                raise ValidationError("Amount cannot specify fractional paise (more than 2 decimal places in INR)")
            paise = int((d * Decimal(100)).to_integral_value())
    except (InvalidOperation, ValueError, TypeError) as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid monetary value for '{field_name}'")

    if allow_zero:
        if paise < 0:
            raise ValidationError("Amount cannot be negative")
    else:
        if paise <= 0:
            raise ValidationError("Amount must be strictly greater than zero")

    if paise > MAX_AMOUNT_PAISE:
        raise ValidationError(f"Amount exceeds maximum permitted limit of {MAX_AMOUNT_PAISE // 100} INR")

    return paise


def validate_account_creation_payload(data: dict) -> dict:
    """Validates payload for creating a new bank account."""
    if not isinstance(data, dict):
        data = {}

    account_type = str(data.get("account_type", "SAVINGS")).strip().upper()
    if account_type not in {"SAVINGS", "CHECKING"}:
        raise ValidationError("Account type must be either 'SAVINGS' or 'CHECKING'")

    initial_deposit_paise = 0
    if "initial_deposit" in data or "initial_deposit_paise" in data:
        initial_deposit_paise = parse_amount_to_paise(
            data, field_name="initial_deposit", allow_zero=True
        )

    return {
        "account_type": account_type,
        "initial_deposit_paise": initial_deposit_paise
    }


def validate_transaction_payload(data: dict) -> dict:
    """Validates deposit and withdrawal transaction payloads."""
    paise = parse_amount_to_paise(data, field_name="amount", allow_zero=False)
    description = str(data.get("description", "")).strip()
    if len(description) > 255:
        raise ValidationError("Description cannot exceed 255 characters")

    return {
        "amount_paise": paise,
        "description": description
    }


def validate_transfer_payload(data: dict) -> dict:
    """Validates account-to-account transfer payload."""
    paise = parse_amount_to_paise(data, field_name="amount", allow_zero=False)
    target_account = str(data.get("target_account", "") or data.get("target_account_number", "")).strip()
    if not target_account:
        raise ValidationError("Target account number or ID ('target_account') is required")

    description = str(data.get("description", "")).strip()
    if len(description) > 255:
        raise ValidationError("Description cannot exceed 255 characters")

    transaction_pin = str(data.get("transaction_pin", "") or data.get("pin", "")).strip()

    return {
        "amount_paise": paise,
        "target_account": target_account,
        "description": description,
        "transaction_pin": transaction_pin
    }
