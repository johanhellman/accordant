/**
 * Analytics integration utility
 * 
 * Supports flexible analytics configuration via environment variables.
 * Compatible with Accordant's deployment flexibility pattern.
 * 
 * Configuration:
 * - VITE_PLAUSIBLE_DOMAIN: Analytics domain (e.g., "analytics.accordant.eu")
 *   If not set, analytics will be disabled
 * - VITE_ANALYTICS_DOMAIN: Domain to track (e.g., "accordant.eu")
 *   Defaults to window.location.hostname if not set
 */

/**
 * Initialize analytics tracking if configured
 * Should be called once when the app loads
 */
export function initAnalytics() {
  const plausibleDomain = import.meta.env.VITE_PLAUSIBLE_DOMAIN;
  const analyticsDomain = import.meta.env.VITE_ANALYTICS_DOMAIN || window.location.hostname;

  // Skip if analytics domain not configured
  if (!plausibleDomain) {
    if (import.meta.env.DEV) {
      console.log('[Analytics] Disabled - VITE_PLAUSIBLE_DOMAIN not set');
    }
    return;
  }

  // Construct script URL
  const scriptUrl = `https://${plausibleDomain}/js/script.js`;

  // Check if script already loaded
  if (document.querySelector(`script[src="${scriptUrl}"]`)) {
    return;
  }

  // Create and inject script
  const script = document.createElement('script');
  script.defer = true;
  script.setAttribute('data-domain', analyticsDomain);
  script.src = scriptUrl;
  script.onerror = () => {
    console.warn(`[Analytics] Failed to load script from ${scriptUrl}`);
  };

  // Insert before closing head tag or at end of head
  const head = document.head || document.getElementsByTagName('head')[0];
  head.appendChild(script);

  if (import.meta.env.DEV) {
    console.log(`[Analytics] Initialized - Domain: ${analyticsDomain}, Script: ${scriptUrl}`);
  }
}

/**
 * Track a custom event (if analytics is enabled)
 * @param {string} eventName - Event name
 * @param {Object} props - Optional event properties
 */
export function trackEvent(eventName, props = {}) {
  // Only track if plausible is loaded
  if (window.plausible) {
    window.plausible(eventName, { props });
  }
}
