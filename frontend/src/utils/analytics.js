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

  // Pre-check for reachability in dev mode to avoid 404 console errors
  // This is optional but nice for developer experience
  if (import.meta.env.DEV) {
    // If the domain is known to be down or invalid, we can skip
    // For now, we'll just suppress the noise via onerror
  }

  // Create and inject script
  const script = document.createElement('script');
  script.defer = true;
  script.setAttribute('data-domain', analyticsDomain);
  script.src = scriptUrl;

  // Robust error handling to prevent loud console errors if analytics is blocked or down
  script.onerror = (e) => {
    // In dev, logging a warning is fine. In prod, we might want to be quieter or just log once.
    if (import.meta.env.DEV) {
      console.warn(`[Analytics] Failed to load script from ${scriptUrl}. Check DNS or VITE_PLAUSIBLE_DOMAIN.`);
    }
    // Prevent default error handling if possible (though 404s/network errors are hard to fully suppress)
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
