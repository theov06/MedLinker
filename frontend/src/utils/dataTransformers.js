// src/utils/dataTransformers.js

// Transform API facility data to frontend format
export function transformFacility(apiFacility) {
  const {
    facility_id,
    extracted_capabilities,
    status,
    confidence,
    citations = []
  } = apiFacility;

  // Extract services and equipment
  const services = extracted_capabilities?.services || [];
  const equipment = extracted_capabilities?.equipment || [];
  
  // Generate a readable name
  const name = facility_id.replace(/-/g, ' ').replace(/(^|\s)\S/g, l => l.toUpperCase());
  
  // Map status values
  const statusMap = {
    'VERIFIED': 'optimal',
    'INCOMPLETE': 'moderate',
    'SUSPICIOUS': 'critical'
  };

  const frontendStatus = statusMap[status] || 'moderate';
  
  // Generate random but consistent values for visualization
  // (These would ideally come from the backend)
  const seed = parseInt(facility_id.replace(/\D/g, '').slice(0, 3)) || 100;
  
  return {
    id: facility_id,
    name,
    specialty: services[0] || 'General',
    rating: confidence === 'HIGH' ? 4.5 + (seed % 50) / 100 : 
            confidence === 'MEDIUM' ? 3.5 + (seed % 50) / 100 : 
            2.5 + (seed % 50) / 100,
    distance: `${1 + (seed % 20)}.${seed % 10} mi`,
    status: frontendStatus,
    doctors: 10 + (seed % 100),
    patientCapacity: 50 + (seed % 300),
    waitTime: `${15 + (seed % 60)} min`,
    lat: 39.8283 + (seed % 1000) / 1000 - 5,
    lng: -98.5795 + (seed % 1000) / 1000 - 10,
    equipment: equipment.slice(0, 5),
    specialties: services.slice(0, 3),
    lastUpdated: 'Just now',
    // Original API data for details
    apiData: apiFacility,
    confidence,
    citationsCount: citations.length
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