"""Normalization and synonym mapping for capability terms."""

import re


# Synonym mappings (conservative)
SYNONYM_MAP = {
    # C-section variations
    "cesarean": "c-section",
    "caesarean": "c-section",
    "c section": "c-section",
    "c-section": "c-section",
    
    # Emergency variations
    "accident & emergency": "emergency",
    "accident and emergency": "emergency",
    "a&e": "emergency",
    "er": "emergency",
    "emergency": "emergency",
    
    # X-ray variations
    "xray": "x-ray",
    "x ray": "x-ray",
    "x-ray": "x-ray",
    
    # Ultrasound variations
    "ultra sound": "ultrasound",
    "ultrasound": "ultrasound",
    
    # Laboratory variations
    "lab": "laboratory",
    "laboratory": "laboratory",
    "lab services": "laboratory",
    
    # Midwife variations
    "midwives": "midwife",
    "midwife": "midwife",
    
    # Doctor variations
    "doctors": "doctor",
    "doctor": "doctor",
    "physician": "doctor",
    "physicians": "doctor"
}


def normalize_term(text: str) -> str:
    """Normalize a capability term.
    
    Args:
        text: Raw capability term
        
    Returns:
        Normalized term (lowercase, stripped, collapsed spaces)
    """
    if not text:
        return ""
    
    # Lowercase
    normalized = text.lower()
    
    # Strip whitespace
    normalized = normalized.strip()
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def map_synonym(term: str) -> str:
    """Map a term to its canonical form using synonym map.
    
    Args:
        term: Normalized term
        
    Returns:
        Canonical term or original if no mapping exists
    """
    normalized = normalize_term(term)
    return SYNONYM_MAP.get(normalized, normalized)


def normalize_and_map(term: str) -> str:
    """Normalize and map a term in one step.
    
    Args:
        term: Raw capability term
        
    Returns:
        Canonical normalized term
    """
    return map_synonym(normalize_term(term))
