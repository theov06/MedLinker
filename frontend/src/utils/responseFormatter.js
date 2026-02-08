// Response formatter to make backend responses more user-friendly

export function formatAnswer(answer, facilities, regions) {
  let formatted = answer;

  // Replace technical facility IDs with friendly names
  formatted = formatted.replace(/FACILITY-(\d+)/g, (match, num) => {
    return `Facility #${num}`;
  });

  // Replace region codes with friendly names
  formatted = formatted.replace(/TEST-R(\d+)/g, (match, num) => {
    return `Region ${num}`;
  });

  // Make desert scores more readable
  formatted = formatted.replace(/desert[_\s]score[:\s]+(\d+)/gi, (match, score) => {
    const severity = getSeverityLabel(parseInt(score));
    return `desert score of ${score} (${severity})`;
  });

  // Format missing services more clearly
  formatted = formatted.replace(/service:([a-z-]+)/gi, (match, service) => {
    return formatServiceName(service);
  });

  // Add friendly headers
  if (formatted.includes('Top') && formatted.includes('regions')) {
    formatted = '🏥 ' + formatted;
  }

  if (formatted.includes('facilities analyzed')) {
    formatted = '📊 ' + formatted;
  }

  // Make lists more readable
  formatted = formatted.replace(/(\d+)\.\s+([A-Z-]+\d+):/g, (match, num, id) => {
    return `\n${num}. Facility #${id.replace('FACILITY-', '')}:`;
  });

  return formatted.trim();
}

function getSeverityLabel(score) {
  if (score >= 80) return '🔴 Critical';
  if (score >= 60) return '🟠 High';
  if (score >= 40) return '🟡 Moderate';
  if (score >= 20) return '🟢 Low';
  return '✅ Minimal';
}

function formatServiceName(service) {
  const serviceMap = {
    'c-section': 'C-Section Surgery',
    'emergency': 'Emergency Services',
    'ultrasound': 'Ultrasound',
    'laboratory': 'Laboratory Services',
    'surgery': 'Surgery',
    'maternity': 'Maternity Care',
    'pharmacy': 'Pharmacy',
    'x-ray': 'X-Ray',
    'icu': 'Intensive Care Unit (ICU)',
    'ambulance': 'Ambulance Services'
  };

  return serviceMap[service.toLowerCase()] || service.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

export function formatCitations(citations) {
  if (!citations || citations.length === 0) return [];

  return citations.map(citation => {
    let snippet = citation.snippet;

    // Format facility IDs
    snippet = snippet.replace(/FACILITY-(\d+)/g, 'Facility #$1');

    // Format region names
    snippet = snippet.replace(/TEST-R(\d+)/g, 'Region $1');

    // Format service names
    snippet = snippet.replace(/service:([a-z-]+)/gi, (match, service) => {
      return formatServiceName(service);
    });

    // Format desert scores
    snippet = snippet.replace(/desert_score:\s*(\d+)/gi, (match, score) => {
      const severity = getSeverityLabel(parseInt(score));
      return `Desert Score: ${score} (${severity})`;
    });

    return {
      ...citation,
      snippet: snippet
    };
  });
}

export function enhanceAnswer(answer, citations, facilities, regions) {
  // Add context if answer is too technical
  let enhanced = answer;

  // Add helpful context for desert score queries
  if (answer.includes('desert score') || answer.includes('Desert score')) {
    enhanced += '\n\n💡 Desert scores range from 0-100, where higher scores indicate more critical healthcare gaps.';
  }

  // Add context for missing services
  if (answer.includes('Missing:') || answer.includes('missing')) {
    enhanced += '\n\n💡 Missing services indicate critical healthcare capabilities not available in this region.';
  }

  // Add data summary if answer is very short
  if (answer.length < 100 && facilities && regions) {
    enhanced += `\n\n📊 Current data: ${facilities.length} facilities across ${regions.length} regions analyzed.`;
  }

  return enhanced;
}
