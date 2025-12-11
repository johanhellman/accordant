/**
 * Analytics integration utility
 * 
 * Supports flexible analytics configuration via environment variables.
 * Compatible with Accordant's deployment flexibility pattern.
 * 
 * Configuration:
 * - VITE_ANALYTICS_PROVIDER: Analytics provider ('umami' or 'plausible', empty to disable)
 * - VITE_ANALYTICS_DOMAIN: Analytics server domain (e.g., "analytics.accordant.eu")
 *   If not set, analytics will be disabled
 * - VITE_ANALYTICS_WEBSITE_ID: Website ID for Umami (required if provider is 'umami')
 * - VITE_PLAUSIBLE_DOMAIN: Legacy Plausible domain (for backward compatibility)
 *   Defaults to VITE_ANALYTICS_DOMAIN if not set
 */

/**
 * Initialize analytics tracking if configured
 * Should be called once when the app loads
 */
export function initAnalytics() {
  // Determine provider (default to 'umami' if ANALYTICS_DOMAIN is set, otherwise check legacy PLAUSIBLE_DOMAIN)
  const analyticsProvider = import.meta.env.VITE_ANALYTICS_PROVIDER || 
    (import.meta.env.VITE_ANALYTICS_DOMAIN ? 'umami' : 
     (import.meta.env.VITE_PLAUSIBLE_DOMAIN ? 'plausible' : null));
  
  const analyticsDomain = import.meta.env.VITE_ANALYTICS_DOMAIN || import.meta.env.VITE_PLAUSIBLE_DOMAIN;
  const websiteId = import.meta.env.VITE_ANALYTICS_WEBSITE_ID;

  // Skip if analytics not configured
  if (!analyticsProvider || !analyticsDomain) {
    if (import.meta.env.DEV) {
      console.log('[Analytics] Disabled - Analytics domain not configured');
    }
    return;
  }

  if (analyticsProvider === 'umami') {
    initUmami(analyticsDomain, websiteId);
  } else if (analyticsProvider === 'plausible') {
    initPlausible(analyticsDomain);
  }
}

/**
 * Initialize Umami Analytics
 */
function initUmami(domain, websiteId) {
  if (!websiteId) {
    if (import.meta.env.DEV) {
      console.warn('[Analytics] Umami website ID not set - analytics will not work');
      console.warn('[Analytics] Set UMAMI_WEBSITE_ID in .env and rebuild Accordant');
    }
    return;
  }

  const scriptUrl = `https://${domain}/script.js`;

  // Check if script already loaded
  if (document.querySelector(`script[src="${scriptUrl}"]`)) {
    return;
  }

  // Create and inject Umami script
  const script = document.createElement('script');
  script.defer = true;
  script.setAttribute('data-website-id', websiteId);
  script.src = scriptUrl;

  // Robust error handling to prevent loud console errors if analytics is blocked or down
  script.onerror = (e) => {
    // In dev, logging a warning is fine. In prod, we might want to be quieter or just log once.
    if (import.meta.env.DEV) {
      console.warn(`[Analytics] Failed to load Umami script from ${scriptUrl}. Check DNS or VITE_ANALYTICS_DOMAIN.`);
    }
    // Prevent default error handling if possible (though 404s/network errors are hard to fully suppress)
  };

  // Insert before closing head tag or at end of head
  const head = document.head || document.getElementsByTagName('head')[0];
  head.appendChild(script);

  if (import.meta.env.DEV) {
    console.log(`[Analytics] Initialized Umami - Domain: ${domain}, Website ID: ${websiteId}`);
  }
}

/**
 * Initialize Plausible Analytics (legacy support)
 */
function initPlausible(domain) {
  const analyticsDomain = import.meta.env.VITE_ANALYTICS_DOMAIN || window.location.hostname;
  const scriptUrl = `https://${domain}/js/script.js`;

  // Check if script already loaded
  if (document.querySelector(`script[src="${scriptUrl}"]`)) {
    return;
  }

  // Create and inject Plausible script
  const script = document.createElement('script');
  script.defer = true;
  script.setAttribute('data-domain', analyticsDomain);
  script.src = scriptUrl;
  script.onerror = () => {
    console.warn(`[Analytics] Failed to load Plausible script from ${scriptUrl}`);
  };

  // Insert before closing head tag or at end of head
  const head = document.head || document.getElementsByTagName('head')[0];
  head.appendChild(script);

  if (import.meta.env.DEV) {
    console.log(`[Analytics] Initialized Plausible - Domain: ${analyticsDomain}, Script: ${scriptUrl}`);
  }
}

/**
 * Track a custom event (if analytics is enabled)
 * @param {string} eventName - Event name
 * @param {Object} props - Optional event properties
 */
export function trackEvent(eventName, props = {}) {
  // Support both Umami and Plausible
  if (window.umami && typeof window.umami.track === 'function') {
    // Umami tracking
    window.umami.track(eventName, props);
  } else if (window.plausible) {
    // Plausible tracking (legacy)
    window.plausible(eventName, { props });
  }
}
