"""Prompt templates for LLM extraction."""

GEMINI_EXTRACT_PROMPT = """You are an Intelligent Document Parsing system specialized in healthcare facility data extraction.

CRITICAL RULES:
1. Return ONLY valid JSON. NO markdown, NO code blocks, NO explanations, NO extra text.
2. Your output will be parsed by json.loads(). If parsing fails, your output is REJECTED.
3. Extract ONLY facts explicitly stated in SOURCE TEXT. Do NOT infer, guess, or hallucinate.
4. Every citation snippet MUST be verbatim text copied from SOURCE TEXT (max 500 chars).
5. If information is missing, use: null for strings, [] for lists, "UNKNOWN" for enums.
6. All enum values must match exactly: referral_capacity in ["NONE","BASIC","ADVANCED","UNKNOWN"], emergency_capability in ["YES","NO","UNKNOWN"].

REQUIRED JSON SCHEMA:
{{
  "extracted_capabilities": {{
    "services": ["string"],
    "equipment": ["string"],
    "staffing": ["string"],
    "hours": "string or null",
    "referral_capacity": "NONE|BASIC|ADVANCED|UNKNOWN",
    "emergency_capability": "YES|NO|UNKNOWN"
  }},
  "citations": [
    {{
      "source_id": "string",
      "source_url": "string or null",
      "snippet": "verbatim text from SOURCE TEXT (1-500 chars)",
      "field": "services|equipment|staffing|hours|referral_capacity|emergency_capability",
      "start_char": integer or null,
      "end_char": integer or null
    }}
  ]
}}

CITATION REQUIREMENTS:
- Every extracted fact MUST have at least one supporting citation
- snippet MUST be copied verbatim from SOURCE TEXT (not paraphrased)
- snippet length: 1-500 characters
- field MUST be one of: services, equipment, staffing, hours, referral_capacity, emergency_capability
- If you extract capabilities but provide no citations, output is REJECTED

SOURCE METADATA:
Facility ID: {facility_id}
Facility Name: {facility_name}
Location: {region}, {country}
Source ID: {source_id}
Source URL: {source_url}

SOURCE TEXT:
{source_text}

EXTRACTION TASK:
Extract structured capability data and provide evidence citations.

OUTPUT FORMAT:
Return ONLY the JSON object. No markdown. No code blocks. No explanations.
"""


def build_gemini_prompt(
    facility_id: str,
    facility_name: str,
    country: str,
    region: str,
    source_id: str,
    source_url: str,
    source_text: str
) -> str:
    """Build Gemini extraction prompt with strict JSON requirements.
    
    Args:
        facility_id: Facility identifier
        facility_name: Name of facility
        country: Country location
        region: Region/state location
        source_id: Source document ID
        source_url: Source URL (or empty string)
        source_text: Raw text to extract from
        
    Returns:
        Formatted prompt string
    """
    return GEMINI_EXTRACT_PROMPT.format(
        facility_id=facility_id,
        facility_name=facility_name,
        country=country,
        region=region,
        source_id=source_id,
        source_url=source_url or "null",
        source_text=source_text
    )


GEMINI_RETRY_PROMPT = """Your previous output was INVALID and REJECTED.

ERRORS DETECTED:
{error_details}

CRITICAL: Return ONLY valid JSON matching this exact schema:
{{
  "extracted_capabilities": {{
    "services": ["string"],
    "equipment": ["string"],
    "staffing": ["string"],
    "hours": "string or null",
    "referral_capacity": "NONE|BASIC|ADVANCED|UNKNOWN",
    "emergency_capability": "YES|NO|UNKNOWN"
  }},
  "citations": [
    {{
      "source_id": "{source_id}",
      "source_url": "{source_url}",
      "snippet": "verbatim text from source (1-500 chars)",
      "field": "services|equipment|staffing|hours|referral_capacity|emergency_capability",
      "start_char": integer or null,
      "end_char": integer or null
    }}
  ]
}}

NO markdown. NO code blocks. NO explanations. ONLY the JSON object.
"""


def build_retry_prompt(error_details: str, source_id: str, source_url: str) -> str:
    """Build retry prompt for JSON repair.
    
    Args:
        error_details: Description of validation errors
        source_id: Source document ID
        source_url: Source URL
        
    Returns:
        Formatted retry prompt
    """
    return GEMINI_RETRY_PROMPT.format(
        error_details=error_details,
        source_id=source_id,
        source_url=source_url or "null"
    )
