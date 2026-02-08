"""Dataset loading and processing utilities."""

import csv
import json
from typing import List, Optional, Any, Dict

from medlinker_ai.models import FacilityDocInput


def load_coordinates_map(coords_csv_path: str = "Updated_long_and_lat_on_VF_Gh.csv") -> Dict[str, tuple]:
    """Load facility coordinates from CSV file.
    
    Args:
        coords_csv_path: Path to coordinates CSV file
        
    Returns:
        Dictionary mapping facility_name to (latitude, longitude)
    """
    coords_map = {}
    
    try:
        with open(coords_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                facility_name = row.get("facility_name", "").strip()
                latitude = row.get("latitude", "").strip()
                longitude = row.get("longitude", "").strip()
                
                if facility_name and latitude and longitude:
                    try:
                        coords_map[facility_name] = (float(latitude), float(longitude))
                    except ValueError:
                        continue
    except FileNotFoundError:
        print(f"Warning: Coordinates file {coords_csv_path} not found. Facilities will not have GPS coordinates.")
    
    return coords_map


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
    limit: Optional[int] = None,
    coords_csv_path: str = "Updated_long_and_lat_on_VF_Gh.csv"
) -> List[FacilityDocInput]:
    """Load facility documents from CSV file.
    
    Args:
        csv_path: Path to CSV file
        limit: Optional limit on number of rows to load
        coords_csv_path: Path to coordinates CSV file
        
    Returns:
        List of FacilityDocInput objects
    """
    # Load coordinates map
    coords_map = load_coordinates_map(coords_csv_path)
    
    facilities = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            
            # Extract facility name (column B in CSV)
            facility_name = row.get("name", "").strip()
            if not facility_name:
                facility_name = f"Facility {i+1}"
            
            # Extract facility ID
            facility_id = row.get("pk_unique_id", "").strip()
            if not facility_id:
                facility_id = f"FACILITY-{i+1:04d}"
            
            # Extract location information
            # Try multiple location fields
            address_city = row.get("address_city", "").strip()
            address_region = row.get("address_stateOrRegion", "").strip()
            address_country = row.get("address_country", "").strip()
            
            # Handle "null" string values
            if address_city.lower() == "null":
                address_city = ""
            if address_region.lower() == "null":
                address_region = ""
            if address_country.lower() == "null":
                address_country = ""
            
            # Build region and country
            region = address_region or address_city or "Unknown Region"
            country = address_country or "Ghana"  # Default to Ghana
            
            # Get coordinates from coords map
            latitude, longitude = coords_map.get(facility_name, (None, None))
            
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
                source_url=row.get("source_url"),
                timestamp=None,
                latitude=latitude,
                longitude=longitude
            )
            
            facilities.append(doc)
    
    return facilities
