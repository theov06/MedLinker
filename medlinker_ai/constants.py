"""Constants for MedLinker AI pipeline."""

from typing import Literal

# Status values
STATUS_VERIFIED: Literal["VERIFIED"] = "VERIFIED"
STATUS_INCOMPLETE: Literal["INCOMPLETE"] = "INCOMPLETE"
STATUS_SUSPICIOUS: Literal["SUSPICIOUS"] = "SUSPICIOUS"

StatusType = Literal["VERIFIED", "INCOMPLETE", "SUSPICIOUS"]

# Confidence values
CONFIDENCE_LOW: Literal["LOW"] = "LOW"
CONFIDENCE_MEDIUM: Literal["MEDIUM"] = "MEDIUM"
CONFIDENCE_HIGH: Literal["HIGH"] = "HIGH"

ConfidenceType = Literal["LOW", "MEDIUM", "HIGH"]

# Source types
SOURCE_TYPE_WEBSITE: Literal["website"] = "website"
SOURCE_TYPE_REPORT: Literal["report"] = "report"
SOURCE_TYPE_PDF: Literal["pdf"] = "pdf"
SOURCE_TYPE_DATASET_ROW: Literal["dataset_row"] = "dataset_row"

SourceType = Literal["website", "report", "pdf", "dataset_row"]

# Referral capacity values
REFERRAL_NONE: Literal["NONE"] = "NONE"
REFERRAL_BASIC: Literal["BASIC"] = "BASIC"
REFERRAL_ADVANCED: Literal["ADVANCED"] = "ADVANCED"
REFERRAL_UNKNOWN: Literal["UNKNOWN"] = "UNKNOWN"

ReferralCapacityType = Literal["NONE", "BASIC", "ADVANCED", "UNKNOWN"]

# Emergency capability values
EMERGENCY_YES: Literal["YES"] = "YES"
EMERGENCY_NO: Literal["NO"] = "NO"
EMERGENCY_UNKNOWN: Literal["UNKNOWN"] = "UNKNOWN"

EmergencyCapabilityType = Literal["YES", "NO", "UNKNOWN"]
