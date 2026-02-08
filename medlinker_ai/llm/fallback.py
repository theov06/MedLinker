"""Offline fallback extraction using heuristics."""

import re
import json
from typing import Dict, List, Any

from medlinker_ai.llm.base import LLMClient


class FallbackClient(LLMClient):
    """Offline heuristic-based extraction (no LLM required)."""
    
    # Keywords for extraction
    SERVICES_KEYWORDS = [
        "c-section", "cesarean", "surgery", "surgical", "surgeries", "ultrasound", "x-ray",
        "immunization", "vaccination", "laboratory", "lab services", "pharmacy",
        "dialysis", "emergency", "maternity", "pediatric", "outpatient",
        "inpatient", "consultation", "wound care", "family planning"
    ]
    
    EQUIPMENT_KEYWORDS = [
        "ultrasound", "x-ray", "ecg", "ekg", "ventilator", "oxygen", "ct scanner",
        "ct scan", "mri", "operating theater", "theatre", "anesthesia machine",
        "monitoring equipment", "examination tools", "vaccine refrigerator"
    ]
    
    STAFFING_KEYWORDS = [
        "ob/gyn", "obstetrician", "gynecologist", "midwife", "midwives",
        "anesthetist", "anesthesiologist", "surgeon", "radiologist", "nurse",
        "nurses", "doctor", "doctors", "physician", "specialist", "pediatrician",
        "laboratory technician", "lab technician", "radiographer"
    ]
    
    HOURS_PATTERNS = [
        r"24/7",
        r"24\s*hours",
        r"mon(?:day)?[-\s]*fri(?:day)?[:\s]+\d+(?:am|pm)?[-\s]*\d+(?:am|pm)?",
        r"\d+(?:am|pm)[-\s]*\d+(?:am|pm)",
        r"weekdays?\s+\d+(?:am|pm)?[-\s]*\d+(?:am|pm)?",
        r"emergency[:\s]+24/7"
    ]
    
    REFERRAL_KEYWORDS = {
        "ADVANCED": ["tertiary", "referral center", "accept referrals", "complex cases"],
        "BASIC": ["refer", "referral", "transfer"]
    }
    
    EMERGENCY_KEYWORDS = ["emergency", "er ", "accident & emergency", "a&e", "24/7"]
    
    def extract(self, prompt: str) -> str:
        """Extract using regex heuristics.
        
        Args:
            prompt: Contains the source text to extract from.
            
        Returns:
            JSON string with extracted_capabilities and citations.
        """
        # Extract source text from prompt (it's embedded in the prompt)
        # For simplicity, assume the entire prompt is the source text
        # In practice, we'd parse it from the structured prompt
        source_text = prompt
        
        # Extract capabilities
        services, service_citations = self._extract_list_field(
            source_text, self.SERVICES_KEYWORDS, "services"
        )
        
        equipment, equipment_citations = self._extract_list_field(
            source_text, self.EQUIPMENT_KEYWORDS, "equipment"
        )
        
        staffing, staffing_citations = self._extract_list_field(
            source_text, self.STAFFING_KEYWORDS, "staffing"
        )
        
        hours, hours_citations = self._extract_hours(source_text)
        
        referral_capacity, referral_citations = self._extract_referral_capacity(source_text)
        
        emergency_capability, emergency_citations = self._extract_emergency_capability(source_text)
        
        # Combine all citations
        all_citations = (
            service_citations + equipment_citations + staffing_citations +
            hours_citations + referral_citations + emergency_citations
        )
        
        result = {
            "extracted_capabilities": {
                "services": services,
                "equipment": equipment,
                "staffing": staffing,
                "hours": hours,
                "referral_capacity": referral_capacity,
                "emergency_capability": emergency_capability
            },
            "citations": all_citations
        }
        
        return json.dumps(result, indent=2)
    
    def _extract_list_field(
        self, text: str, keywords: List[str], field_name: str
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        """Extract list field using keyword matching."""
        found_items = []
        citations = []
        text_lower = text.lower()
        
        for keyword in keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            
            if match:
                # Capitalize first letter of each word for display
                item = keyword.title()
                if item not in found_items:
                    found_items.append(item)
                    
                    # Create citation with context window
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    snippet = text[start:end].strip()
                    
                    # Ensure snippet is <= 500 chars
                    if len(snippet) > 500:
                        snippet = snippet[:497] + "..."
                    
                    citations.append({
                        "source_id": "fallback_extraction",
                        "snippet": snippet,
                        "field": field_name,
                        "start_char": match.start(),
                        "end_char": match.end()
                    })
        
        return found_items, citations
    
    def _extract_hours(self, text: str) -> tuple[str | None, List[Dict[str, Any]]]:
        """Extract operating hours."""
        citations = []
        
        for pattern in self.HOURS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hours_text = match.group(0)
                
                # Create citation
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                snippet = text[start:end].strip()
                
                if len(snippet) > 500:
                    snippet = snippet[:497] + "..."
                
                citations.append({
                    "source_id": "fallback_extraction",
                    "snippet": snippet,
                    "field": "hours",
                    "start_char": match.start(),
                    "end_char": match.end()
                })
                
                return hours_text, citations
        
        return None, citations
    
    def _extract_referral_capacity(
        self, text: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Extract referral capacity."""
        text_lower = text.lower()
        citations = []
        
        # Check for ADVANCED first
        for keyword in self.REFERRAL_KEYWORDS["ADVANCED"]:
            if keyword in text_lower:
                match = re.search(re.escape(keyword), text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    snippet = text[start:end].strip()
                    
                    if len(snippet) > 500:
                        snippet = snippet[:497] + "..."
                    
                    citations.append({
                        "source_id": "fallback_extraction",
                        "snippet": snippet,
                        "field": "referral_capacity",
                        "start_char": match.start(),
                        "end_char": match.end()
                    })
                    
                    return "ADVANCED", citations
        
        # Check for BASIC
        for keyword in self.REFERRAL_KEYWORDS["BASIC"]:
            if keyword in text_lower:
                match = re.search(re.escape(keyword), text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    snippet = text[start:end].strip()
                    
                    if len(snippet) > 500:
                        snippet = snippet[:497] + "..."
                    
                    citations.append({
                        "source_id": "fallback_extraction",
                        "snippet": snippet,
                        "field": "referral_capacity",
                        "start_char": match.start(),
                        "end_char": match.end()
                    })
                    
                    return "BASIC", citations
        
        return "UNKNOWN", citations
    
    def _extract_emergency_capability(
        self, text: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Extract emergency capability."""
        text_lower = text.lower()
        citations = []
        
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                match = re.search(re.escape(keyword), text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    snippet = text[start:end].strip()
                    
                    if len(snippet) > 500:
                        snippet = snippet[:497] + "..."
                    
                    citations.append({
                        "source_id": "fallback_extraction",
                        "snippet": snippet,
                        "field": "emergency_capability",
                        "start_char": match.start(),
                        "end_char": match.end()
                    })
                    
                    return "YES", citations
        
        return "UNKNOWN", citations
