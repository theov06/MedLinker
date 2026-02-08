"""Dataset loading and processing utilities."""

import csv
import json
from typing import List, Optional, Any

from medlinker_ai.models import FacilityDocInput


def safe_parse_json_list(value: str) -> List[str]:
    """Safely parse a JSON list string.
    
    Args:
        value: String that might be a JSON list
        
    Returns:
        List of strings, or empty list if parsing fails
    """
    if not value or value.strip() == "":
        return []
    
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return [str(parsed)]
    except (json.JSONDecodeError, ValueError):
        # Try splitting by comma as fallback
        return [item.strip() for item in value.split(",") if item.strip()]


def build_source_text(row: dict) -> str:
    """Build source text from CSV row fields.
    
    Args:
        row: Dictionary of CSV row data
        
    Returns:
        Concatenated source text
    """
    parts = []
    
    # Add name
    if row.get("name"):
        parts.append(f"Facility: {row['name']}")
    
    # Add location
    if row.get("location"):
        parts.append(f"Location: {row['location']}")
    
    # Add specialties
    specialties = safe_parse_json_list(row.get("specialties", ""))
    if specialties:
        parts.append(f"Specialties: {', '.join(specialties)}")
    
    # Add procedures
    procedures = safe_parse_json_list(row.get("procedure", ""))
    if procedures:
        parts.append(f"Procedures: {', '.join(procedures)}")
    
    # Add equipment
    equipment = safe_parse_json_list(row.get("equipment", ""))
    if equipment:
        parts.append(f"Equipment: {', '.join(equipment)}")
    
    # Add capabilities
    capabilities = safe_parse_json_list(row.get("capability", ""))
    if capabilities:
        parts.append(f"Capabilities: {', '.join(capabilities)}")
    
    # Add description
    if row.get("description"):
        parts.append(f"Description: {row['description']}")
    
    return "\n\n".join(parts)


def load_facility_docs_from_csv(
    csv_path: str,
    limit: Optional[int] = None
) -> List[FacilityDocInput]:
    """Load facility documents from CSV file.
    
    Args:
        csv_path: Path to CSV file
        limit: Optional limit on number of rows to load
        
    Returns:
        List of FacilityDocInput objects
    """
    facilities = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            
            # Extract required fields
            facility_id = row.get("id", f"FACILITY-{i+1:04d}")
            facility_name = row.get("name", "Unknown Facility")
            
            # Extract location (try to parse country/region)
            location = row.get("location", "")
            country = row.get("country", "Ghana")  # Default to Ghana
            region = row.get("region", location.split(",")[0] if location else "Unknown")
            
            # Build source text
            source_text = build_source_text(row)
            
            # Create FacilityDocInput
            doc = FacilityDocInput(
                facility_id=facility_id,
                facility_name=facility_name,
                country=country,
                region=region,
                source_id=f"csv_row_{i+1}",
                source_type="dataset_row",
                source_text=source_text,
                source_url=None,
                timestamp=None
            )
            
            facilities.append(doc)
    
    return facilities
