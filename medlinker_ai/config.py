"""Configuration for critical capabilities and thresholds."""

# Critical services that should be available in every region
CRITICAL_SERVICES = [
    "c-section",
    "emergency",
    "ultrasound",
    "x-ray",
    "laboratory"
]

# Critical equipment that should be available in every region
CRITICAL_EQUIPMENT = [
    "ultrasound",
    "x-ray"
]

# Critical staffing that should be available in every region
CRITICAL_STAFFING = [
    "midwife",
    "doctor"
]

# Desert score weights (points per missing critical item)
DESERT_SCORE_WEIGHTS = {
    "service": 20,      # Max 60 points (3 services * 20)
    "equipment": 15,    # Max 30 points (2 equipment * 15)
    "staffing": 10      # Max 20 points (2 staffing * 10)
}

# Maximum desert score
MAX_DESERT_SCORE = 100
