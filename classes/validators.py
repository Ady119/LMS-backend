# utils.py

def validate_age(age):
    if age is not None and age < 0:
        raise ValueError("Age cannot be negative.")

def validate_length(field_name, value, max_length):
    if len(value) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer.")

