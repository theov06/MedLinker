// Facility name mapper - maps facility IDs to real names from backend data

export function createFacilityNameMap(facilities) {
  const map = new Map();
  
  facilities.forEach((facility, index) => {
    // Extract facility name from source text or use ID
    const facilityId = facility.facility_id;
    let facilityName = `Facility #${index + 1}`;
    let location = '';
    
    // Try to extract name from extracted_capabilities or other fields
    // Since backend doesn't store names, we'll use a generic approach
    
    // Check if there's any useful info in the facility object
    if (facility.extracted_capabilities) {
      const caps = facility.extracted_capabilities;
      const services = caps.services || [];
      const equipment = caps.equipment || [];
      
      if (services.length > 0 || equipment.length > 0) {
        facilityName = `Healthcare Facility #${index + 1}`;
        
        // Add service description
        if (services.length > 0) {
          facilityName += ` (${services.slice(0, 2).join(', ')})`;
        }
      }
    }
    
    map.set(facilityId, {
      name: facilityName,
      location: location,
      displayName: facilityName
    });
  });
  
  return map;
}

export function createRegionNameMap(regions) {
  const map = new Map();
  
  regions.forEach((region, index) => {
    const regionKey = `${region.country}-${region.region}`;
    const regionId = region.region;
    
    // Create friendly region name
    let regionName = region.region;
    if (regionName.startsWith('FACILITY-')) {
      regionName = `Region ${index + 1}`;
    }
    
    const displayName = `${regionName}, ${region.country}`;
    
    map.set(regionKey, {
      name: regionName,
      country: region.country,
      displayName: displayName,
      desertScore: region.desert_score,
      missingServices: region.missing_critical || []
    });
    
    // Also map by just the region name
    map.set(regionId, {
      name: regionName,
      country: region.country,
      displayName: displayName,
      desertScore: region.desert_score,
      missingServices: region.missing_critical || []
    });
  });
  
  return map;
}

export function enhanceAnswerWithNames(answer, facilityMap, regionMap) {
  let enhanced = answer;
  
  // Replace facility IDs with names
  enhanced = enhanced.replace(/FACILITY-(\d+)/g, (match, num) => {
    const facility = facilityMap.get(match);
    return facility ? facility.displayName : `Facility #${num}`;
  });
  
  // Replace region codes
  regionMap.forEach((info, key) => {
    const regex = new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
    enhanced = enhanced.replace(regex, info.displayName);
  });
  
  return enhanced;
}
