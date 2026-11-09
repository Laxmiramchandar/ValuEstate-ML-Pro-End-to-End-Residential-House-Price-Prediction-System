"""
Request Validation and Sanitization Module
Validates incoming web and API payloads, enforces boundaries, rejects NaN/Infinity,
and prevents malformed submissions.
"""
import math
from typing import Dict, Any, Tuple, Optional
from config.config import Config

def validate_prediction_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates dictionary payload for house price prediction.
    Enforces strict numeric range, NaN/Inf rejection, and categorical schema checking.
    
    Returns:
        (is_valid, error_message, sanitized_dict)
    """
    if not isinstance(data, dict):
        return False, "Request payload must be a JSON object or dictionary.", None

    required = ["Area", "Bedrooms", "Bathrooms", "Age", "Location", "Property_Type"]
    missing = [f for f in required if f not in data or data[f] is None or str(data[f]).strip() == ""]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}", None

    # Disallow booleans masquerading as integers (e.g. True / False)
    for num_col in ["Area", "Bedrooms", "Bathrooms", "Age"]:
        if isinstance(data[num_col], bool):
            return False, f"Invalid type for '{num_col}': Booleans are not allowed for numeric fields.", None

    # Type and Value conversions
    try:
        area = float(data["Area"])
        bedrooms = int(data["Bedrooms"])
        bathrooms = int(data["Bathrooms"])
        age = float(data["Age"])
    except (ValueError, TypeError) as e:
        return False, f"Invalid numeric input format: {str(e)}", None

    # Reject NaN and Infinity
    for val_name, val in [("Area", area), ("Bedrooms", bedrooms), ("Bathrooms", bathrooms), ("Age", age)]:
        if math.isnan(val) or math.isinf(val):
            return False, f"Invalid value for '{val_name}': NaN or Infinite values are strictly rejected.", None

    # Domain constraints
    bounds = Config.FEATURE_CONSTRAINTS
    if area < bounds["Area"]["min"] or area > bounds["Area"]["max"]:
        return False, f"Area ({area}) must be between {bounds['Area']['min']} and {bounds['Area']['max']} sq ft.", None

    if bedrooms < bounds["Bedrooms"]["min"] or bedrooms > bounds["Bedrooms"]["max"]:
        return False, f"Bedrooms ({bedrooms}) must be between {bounds['Bedrooms']['min']} and {bounds['Bedrooms']['max']}.", None

    if bathrooms < bounds["Bathrooms"]["min"] or bathrooms > bounds["Bathrooms"]["max"]:
        return False, f"Bathrooms ({bathrooms}) must be between {bounds['Bathrooms']['min']} and {bounds['Bathrooms']['max']}.", None

    if age < bounds["Age"]["min"] or age > bounds["Age"]["max"]:
        return False, f"Age ({age}) must be between {bounds['Age']['min']} and {bounds['Age']['max']} years.", None

    location = str(data["Location"]).strip()
    property_type = str(data["Property_Type"]).strip()

    if location not in bounds["Location"]:
        return False, f"Location '{location}' is invalid. Allowed options: {', '.join(bounds['Location'])}", None

    if property_type not in bounds["Property_Type"]:
        return False, f"Property Type '{property_type}' is invalid. Allowed options: {', '.join(bounds['Property_Type'])}", None

    sanitized = {
        "Area": area,
        "Bedrooms": bedrooms,
        "Bathrooms": bathrooms,
        "Age": age,
        "Location": location,
        "Property_Type": property_type
    }
    return True, None, sanitized
