// src/utils/dataTransformers.js

// Real GPS coordinates from Ghana facilities
const GHANA_COORDINATES = [
  { lat: 5.5868921, lng: -0.1850474 },  // 37 Military Hospital
  { lat: 5.5693943, lng: -0.1864212 },  // Accra Medical Centre
  { lat: 5.6133632, lng: -0.2153329 },  // Accra Physiotherapy & Sports Injury Clinic
  { lat: 5.5633229, lng: -0.2045791 },  // Accra Psychiatric Hospital
  { lat: 5.6298307, lng: -0.2171964 },  // Achimota Hospital
  { lat: 5.7060649, lng: -0.1681089 },  // Adenta Clinic
  { lat: 6.7965698, lng: -1.0855078 },  // Agogo Presbyterian Hospital
  { lat: 6.5383038, lng: -0.7672659 },  // Agyakwa Hospital
];

// Transform API facility data to frontend format
export function transformFacility(apiFacility) {
  const {
    facility_id,
    facility_name,
    location,
    region,
    country,
    latitude,
    longitude,
    extracted_capabilities,
    status,
    confidence,
    citations = []
  } = apiFacility;

  // Extract services and equipment
  const services = extracted_capabilities?.services || [];
  const equipment = extracted_capabilities?.equipment || [];
  const staffing = extracted_capabilities?.staffing || [];
  
  // Use real facility name from backend
  const name = facility_name || facility_id;
  
  // Map status values
  const statusMap = {
    'VERIFIED': 'optimal',
    'INCOMPLETE': 'moderate',
    'SUSPICIOUS': 'critical'
  };

  const frontendStatus = statusMap[status] || 'moderate';
  
  // Generate random but consistent values for visualization
  const seed = parseInt(facility_id.toString().replace(/\D/g, '').slice(0, 3)) || 100;
  
  // Use real coordinates from backend if available, otherwise pick from Ghana coordinates pool
  let facilityLat, facilityLng;
  if (latitude && longitude) {
    facilityLat = latitude;
    facilityLng = longitude;
  } else {
    // Use seed to consistently pick a coordinate from the pool
    const coordIndex = seed % GHANA_COORDINATES.length;
    facilityLat = GHANA_COORDINATES[coordIndex].lat;
    facilityLng = GHANA_COORDINATES[coordIndex].lng;
  }
  
  return {
    id: facility_id,
    name,
    location: location || `${region}, ${country}`,
    specialty: services[0] || 'General Healthcare',
    rating: confidence === 'HIGH' ? 4.5 + (seed % 50) / 100 : 
            confidence === 'MEDIUM' ? 3.5 + (seed % 50) / 100 : 
            2.5 + (seed % 50) / 100,
    distance: `${1 + (seed % 20)}.${seed % 10} mi`,
    status: frontendStatus,
    doctors: staffing.length > 0 ? 10 + (seed % 100) : 0,
    patientCapacity: 50 + (seed % 300),
    waitTime: `${15 + (seed % 60)} min`,
    lat: facilityLat,
    lng: facilityLng,
    equipment: equipment.slice(0, 5),
    specialties: services.slice(0, 3),
    lastUpdated: 'Just now',
    // Original API data for details
    apiData: apiFacility,
    confidence,
    citationsCount: citations.length,
    region,
    country
  };
}

// Transform API region data to frontend format
export function transformRegion(apiRegion) {
  const {
    country,
    region,
    total_facilities,
    facilities_analyzed,
    status_counts = {},
    coverage = {},
    desert_score,
    supporting_facility_ids = [],
    missing_critical = []
  } = apiRegion;

  return {
    id: `${country}-${region}`,
    name: region,
    country,
    totalFacilities: total_facilities,
    facilitiesAnalyzed: facilities_analyzed,
    statusCounts: status_counts,
    coverage: {
      emergency: coverage.services?.emergency || 0,
      surgery: coverage.services?.surgery || 0,
      cSection: coverage.services?.['c-section'] || 0,
      ultrasound: coverage.equipment?.ultrasound || 0,
      xray: coverage.equipment?.['x-ray'] || 0
    },
    desertScore: desert_score,
    desertLevel: desert_score <= 30 ? 'Low' : 
                 desert_score <= 60 ? 'Moderate' : 
                 'High',
    missingCritical: missing_critical,
    supportingFacilities: supporting_facility_ids
  };
}

// Group facilities by region for the map
export function groupFacilitiesByRegion(facilities, regions) {
  const regionsMap = {};
  
  regions.forEach(region => {
    regionsMap[region.id] = {
      ...region,
      facilities: []
    };
  });

  facilities.forEach(facility => {
    // Extract region from facility_id (format: GH-ACC-001)
    const parts = facility.id.split('-');
    if (parts.length >= 2) {
      const regionKey = `${parts[0]}-${parts[1]}`;
      if (regionsMap[regionKey]) {
        regionsMap[regionKey].facilities.push(facility);
      }
    }
  });

  return Object.values(regionsMap);
}