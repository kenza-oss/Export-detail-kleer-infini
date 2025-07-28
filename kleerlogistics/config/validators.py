"""
Custom validators and sanitization functions for KleerLogistics.
"""

import re
import html
from typing import Any, Dict, List, Optional
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.conf import settings
import bleach
from phonenumber_field.validators import validate_international_phonenumber


class SecurityValidator:
    """Base class for security validators."""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content to prevent XSS attacks."""
        if not text:
            return text
            
        # Allowed HTML tags and attributes
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        
        allowed_attributes = {
            '*': ['class', 'id'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title'],
        }
        
        return bleach.clean(
            text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        if not filename:
            return filename
            
        # Remove path traversal characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove multiple dots
        filename = re.sub(r'\.{2,}', '.', filename)
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        return filename
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
        """Validate file size."""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file type based on extension."""
        if not filename:
            return False
            
        file_extension = filename.lower().split('.')[-1]
        return file_extension in allowed_extensions


class PhoneNumberValidator:
    """Custom phone number validator for Algeria."""
    
    @staticmethod
    def validate_algerian_phone(value: str) -> None:
        """Validate Algerian phone number format."""
        # Algerian phone number patterns
        patterns = [
            r'^\+213[567][0-9]{8}$',  # International format
            r'^0[567][0-9]{8}$',      # National format
        ]
        
        for pattern in patterns:
            if re.match(pattern, value):
                return
        
        raise ValidationError(_('Please enter a valid Algerian phone number.'))
    
    @staticmethod
    def normalize_phone_number(value: str) -> str:
        """Normalize phone number to international format."""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', value)
        
        # If starts with 0, replace with +213
        if cleaned.startswith('0'):
            cleaned = '+213' + cleaned[1:]
        
        # If doesn't start with +, add +213
        if not cleaned.startswith('+'):
            cleaned = '+213' + cleaned
            
        return cleaned


class AddressValidator:
    """Address validation and sanitization."""
    
    @staticmethod
    def validate_postal_code(value: str) -> None:
        """Validate Algerian postal code."""
        if not re.match(r'^\d{5}$', value):
            raise ValidationError(_('Please enter a valid 5-digit postal code.'))
    
    @staticmethod
    def sanitize_address(address: str) -> str:
        """Sanitize address input."""
        if not address:
            return address
            
        # Remove potentially dangerous characters
        address = re.sub(r'[<>"\']', '', address)
        # Normalize whitespace
        address = ' '.join(address.split())
        
        return address[:200]  # Limit length


class PaymentValidator:
    """Payment-related validation."""
    
    @staticmethod
    def validate_amount(amount: float) -> None:
        """Validate payment amount."""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than 0.'))
        
        if amount > 1000000:  # 1 million DZD limit
            raise ValidationError(_('Amount exceeds maximum limit.'))
    
    @staticmethod
    def validate_currency(currency: str) -> None:
        """Validate currency code."""
        allowed_currencies = ['DZD', 'EUR', 'USD']
        if currency not in allowed_currencies:
            raise ValidationError(_('Invalid currency code.'))
    
    @staticmethod
    def sanitize_card_number(card_number: str) -> str:
        """Sanitize card number (remove spaces, dashes)."""
        if not card_number:
            return card_number
            
        return re.sub(r'[\s\-]', '', card_number)


class ShipmentValidator:
    """Shipment-related validation."""
    
    @staticmethod
    def validate_dimensions(length: float, width: float, height: float) -> None:
        """Validate package dimensions."""
        max_dimension = 200  # cm
        
        for dimension, name in [(length, 'length'), (width, 'width'), (height, 'height')]:
            if dimension <= 0:
                raise ValidationError(_(f'{name.title()} must be greater than 0.'))
            if dimension > max_dimension:
                raise ValidationError(_(f'{name.title()} exceeds maximum limit of {max_dimension}cm.'))
    
    @staticmethod
    def validate_weight(weight: float) -> None:
        """Validate package weight."""
        if weight <= 0:
            raise ValidationError(_('Weight must be greater than 0.'))
        
        if weight > 50:  # 50kg limit
            raise ValidationError(_('Weight exceeds maximum limit of 50kg.'))
    
    @staticmethod
    def validate_package_content(description: str) -> str:
        """Validate and sanitize package content description."""
        if not description:
            return description
            
        # Remove potentially dangerous content
        description = SecurityValidator.sanitize_html(description)
        
        # Check for prohibited items
        prohibited_items = [
            'weapon', 'drug', 'explosive', 'flammable', 'toxic', 'radioactive',
            'weapon', 'arme', 'drogue', 'explosif', 'inflammable', 'toxique'
        ]
        
        description_lower = description.lower()
        for item in prohibited_items:
            if item in description_lower:
                raise ValidationError(_('This item is not allowed for shipment.'))
        
        return description[:500]  # Limit length


class UserDataValidator:
    """User data validation and sanitization."""
    
    @staticmethod
    def validate_username(username: str) -> None:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            raise ValidationError(_('Username must be 3-30 characters long and contain only letters, numbers, and underscores.'))
    
    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Validate password strength."""
        if len(password) < 8:
            raise ValidationError(_('Password must be at least 8 characters long.'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter.'))
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter.'))
        
        if not re.search(r'\d', password):
            raise ValidationError(_('Password must contain at least one digit.'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('Password must contain at least one special character.'))
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize person name."""
        if not name:
            return name
            
        # Remove potentially dangerous characters
        name = re.sub(r'[<>"\']', '', name)
        # Normalize whitespace
        name = ' '.join(name.split())
        # Capitalize properly
        name = name.title()
        
        return name[:100]  # Limit length
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_('Please enter a valid email address.'))


# Custom regex validators
algerian_phone_regex = RegexValidator(
    regex=r'^(\+213|0)[567][0-9]{8}$',
    message=_('Enter a valid Algerian phone number.')
)

postal_code_regex = RegexValidator(
    regex=r'^\d{5}$',
    message=_('Enter a valid 5-digit postal code.')
)

username_regex = RegexValidator(
    regex=r'^[a-zA-Z0-9_]{3,30}$',
    message=_('Username must be 3-30 characters long and contain only letters, numbers, and underscores.')
)


def validate_file_upload(file, max_size_mb=10, allowed_extensions=None):
    """Comprehensive file upload validation."""
    if allowed_extensions is None:
        allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
    
    # Check file size
    if not SecurityValidator.validate_file_size(file.size, max_size_mb):
        raise ValidationError(_(f'File size must not exceed {max_size_mb}MB.'))
    
    # Check file type
    if not SecurityValidator.validate_file_type(file.name, allowed_extensions):
        raise ValidationError(_(f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'))
    
    # Sanitize filename
    file.name = SecurityValidator.sanitize_filename(file.name)
    
    return file


def sanitize_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize user input data."""
    sanitized_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Sanitize string values
            sanitized_data[key] = SecurityValidator.sanitize_html(value)
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized_data[key] = sanitize_user_input(value)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized_data[key] = [
                SecurityValidator.sanitize_html(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            # Keep other types as is
            sanitized_data[key] = value
    
    return sanitized_data 