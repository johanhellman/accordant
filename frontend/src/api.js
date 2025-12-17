/**
 * API client for the LLM Council backend.
 *
 * API_BASE uses relative URLs by default (empty string), which works for both:
 * - Production: Frontend and backend served from same origin (accordant.eu)
 * - Development: Can be overridden via VITE_API_BASE environment variable
 */
const API_BASE = import.meta.env.VITE_API_BASE || "";

let authToken = null;

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

const request = async (endpoint, options = {}) => {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config);
    if (!response.ok) {
      let errorMessage = "Request failed";
      let errorData = null;
      try {
        errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = `${response.status} ${response.statusText}`;
      }
      throw new ApiError(errorMessage, response.status, errorData);
    }
    if (response.status === 204) return null;
    return response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new ApiError(
        "Unable to connect to server. Please check your network connection and ensure the backend is running.",
        0,
        null
      );
    }
    throw new ApiError(error.message, 500, null);
  }
};

export const api = {
  /**
   * Set the authentication token for API requests.
   * @param {string} token - JWT authentication token
   */
  setToken(token) {
    authToken = token;
  },

  /**
   * Authenticate user and retrieve access token.
   * @param {string} username - User username
   * @param {string} password - User password
   * @returns {Promise<{access_token: string, token_type: string}>}
   * @throws {Error} If authentication fails
   */
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    return request("/api/auth/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });
  },

  /**
   * Register a new user account (Atomic with Organization).
   * @param {string} username - Desired username
   * @param {string} password - User password
   * @param {string} mode - 'create_org' or 'join_org'
   * @param {string} orgName - Organization name (create mode)
   * @param {string} inviteCode - Invite code (join mode)
   * @returns {Promise<{access_token: string, token_type: string}>}
   * @throws {Error} If registration fails
   */
  async register(username, password, mode = "create_org", orgName = null, inviteCode = null) {
    const payload = {
      username,
      password,
      mode,
      org_name: orgName,
      invite_code: inviteCode,
    };

    return request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Get the currently authenticated user's information.
   * @returns {Promise<{id: string, username: string, org_id: string, is_admin: boolean}>}
   * @throws {Error} If user is not authenticated or request fails
   */
  async getCurrentUser() {
    return request("/api/auth/me");
  },

  async changePassword(currentPassword, newPassword) {
    return request("/api/auth/password", {
      method: "PUT",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  },

  /**
   * List all conversations.
   */
  async listConversations() {
    return request("/api/conversations");
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    return request("/api/conversations", {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    return request(`/api/conversations/${conversationId}`);
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    return request(`/api/conversations/${conversationId}/message`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, consensusEnabled, onEvent) {
    const headers = {
      "Content-Type": "application/json",
    };
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/message/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({ content, consensus_enabled: consensusEnabled }),
    });

    if (!response.ok) {
      let errorMessage = "Failed to send message";
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = `${response.status} ${response.statusText}`;
      }
      throw new ApiError(errorMessage, response.status, null);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      const lines = buffer.split("\n");
      // Keep the last line in the buffer as it might be incomplete
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim() === "") continue;

        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error("Failed to parse SSE event:", e);
          }
        }
      }
    }

    // Process any remaining data in the buffer
    if (buffer && buffer.startsWith("data: ")) {
      const data = buffer.slice(6);
      try {
        const event = JSON.parse(data);
        onEvent(event.type, event);
      } catch (e) {
        console.error("Failed to parse final SSE event:", e);
      }
    }
  },

  // --- Admin API ---

  /**
   * List all available LLM models from the configured provider.
   * @returns {Promise<Array<{id: string, name: string, provider: string}>>}
   * @throws {Error} If API key is invalid or request fails
   */
  async listModels() {
    return request("/api/models");
  },

  /**
   * List all configured personalities for the current organization.
   * @returns {Promise<Array<{id: string, name: string, description: string, model: string, enabled: boolean}>>}
   * @throws {Error} If request fails
   */
  async listPersonalities() {
    return request("/api/personalities");
  },

  /**
   * Create a new personality configuration.
   * @param {Object} personality - Personality configuration object
   * @param {string} personality.id - Unique personality identifier
   * @param {string} personality.name - Display name
   * @param {string} personality.description - Description text
   * @param {string} personality.model - LLM model ID to use
   * @param {string} personality.personality_prompt - Custom system prompt
   * @param {number} [personality.temperature] - Optional temperature setting
   * @param {boolean} [personality.enabled] - Whether personality is enabled
   * @returns {Promise<Object>} Created personality object
   * @throws {Error} If personality ID already exists or request fails
   */
  async createPersonality(personality) {
    return request("/api/personalities", {
      method: "POST",
      body: JSON.stringify(personality),
    });
  },

  /**
   * Update an existing personality configuration.
   * @param {string} id - Personality ID to update
   * @param {Object} personality - Updated personality configuration
   * @returns {Promise<Object>} Updated personality object
   * @throws {Error} If personality not found or request fails
   */
  async updatePersonality(id, personality) {
    return request(`/api/personalities/${id}`, {
      method: "PUT",
      body: JSON.stringify(personality),
    });
  },

  /**
   * Delete a personality configuration.
   * @param {string} id - Personality ID to delete
   * @returns {Promise<{status: string, message: string}>}
   * @throws {Error} If personality not found or request fails
   */
  async deletePersonality(id) {
    return request(`/api/personalities/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * Get system prompts configuration for the current organization.
   * @returns {Promise<{base_system_prompt: string, ranking: Object, chairman: Object, title_generation: Object}>}
   * @throws {Error} If request fails
   */
  async getSystemPrompts() {
    return request("/api/system-prompts");
  },

  /**
   * Update system prompts configuration.
   * @param {Object} config - System prompts configuration
   * @param {string} config.base_system_prompt - Base system prompt for all personalities
   * @param {Object} config.ranking - Ranking prompt configuration
   * @param {Object} config.chairman - Chairman prompt configuration
   * @param {Object} config.title_generation - Title generation prompt configuration
   * @returns {Promise<Object>} Updated configuration with effective models
   * @throws {Error} If validation fails (missing required tags) or request fails
   */
  async updateSystemPrompts(config) {
    return request("/api/system-prompts", {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  /**
   * Get global default system prompts configuration (Instance Admin only).
   */
  async getDefaultSystemPrompts() {
    return request("/api/defaults/system-prompts");
  },

  /**
   * Update global default system prompts configuration (Instance Admin only).
   */
  async updateDefaultSystemPrompts(config) {
    return request("/api/defaults/system-prompts", {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  async listUsers() {
    return request("/api/admin/users");
  },

  async updateUserRole(userId, isAdmin) {
    return request(`/api/admin/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify({ is_admin: isAdmin }),
    });
  },

  async deleteUser(userId) {
    return request(`/api/admin/users/${userId}`, {
      method: "DELETE",
    });
  },

  async getAdminStats() {
    return request("/api/admin/stats");
  },

  async getConsensusStats() {
    return request("/api/admin/stats/consensus");
  },

  async getVotingHistory() {
    return request("/api/votes");
  },

  async getOrgSettings() {
    return request("/api/settings");
  },

  async updateOrgSettings(settings) {
    return request("/api/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  },

  // --- Multi-Org API ---

  async createOrg(name, ownerEmail) {
    return request("/api/organizations/", {
      method: "POST",
      body: JSON.stringify({ name, owner_email: ownerEmail }),
    });
  },

  async joinOrg(inviteCode) {
    return request("/api/organizations/join", {
      method: "POST",
      body: JSON.stringify({ invite_code: inviteCode }),
    });
  },

  async createInvitation() {
    return request("/api/organizations/invitations", {
      method: "POST",
    });
  },

  async deleteOrganization(orgId) {
    return request(`/api/admin/organizations/${orgId}`, {
      method: "DELETE",
    });
  },

  async updateOrganization(orgId, updates) {
    return request(`/api/admin/organizations/${orgId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  },

  async getInvitations() {
    return request("/api/organizations/invitations");
  },

  async listOrganizations() {
    return request("/api/organizations/list");
  },
  // --- Instance Admin API (Defaults) ---

  async listDefaultPersonalities() {
    return request("/api/defaults/personalities");
  },

  async createDefaultPersonality(personality) {
    return request("/api/defaults/personalities", {
      method: "POST",
      body: JSON.stringify(personality),
    });
  },

  async updateDefaultPersonality(id, personality) {
    return request(`/api/defaults/personalities/${id}`, {
      method: "PUT",
      body: JSON.stringify(personality),
    });
  },

  async deleteDefaultPersonality(id) {
    return request(`/api/defaults/personalities/${id}`, {
      method: "DELETE",
    });
  },

  // --- League Table & Evolution API ---

  async getLeagueTable() {
    return request("/api/league-table");
  },

  async getInstanceLeagueTable() {
    return request("/api/instance-league-table");
  },

  async getPersonalityFeedback(id) {
    return request(`/api/personalities/${id}/feedback`);
  },

  async combinePersonalities(data) {
    return request("/api/evolution/combine", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async deactivatePersonality(id) {
    return request(`/api/evolution/deactivate/${id}`, {
      method: "POST",
    });
  },

  /**
   * Fetch public documentation content (markdown).
   * @param {string} docId - 'privacy', 'terms', 'faq', 'manual'
   */
  async getDocumentation(docId) {
    return request(`/api/docs/${docId}`);
  },

  /**
   * Delete a conversation.
   * @param {string} id - Conversation ID
   */
  async deleteConversation(id) {
    return request(`/api/conversations/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * Delete the current user's account and all data.
   */
  async deleteAccount() {
    return request("/api/users/me", {
      method: "DELETE",
    });
  },

  /**
   * trigger download of user data export.
   */
  async exportUserData() {
    const headers = {
      "Content-Type": "application/json",
    };
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE}/api/users/me/export`, {
      headers,
    });
    if (!response.ok) throw new Error("Failed to export data");

    // Trigger download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    // Try to get filename from content-disposition
    const disposition = response.headers.get("Content-Disposition");
    let filename = "accordant_export.json";
    if (disposition && disposition.indexOf("filename=") !== -1) {
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
      if (matches != null && matches[1]) {
        filename = matches[1].replace(/['"]/g, "");
      }
    }
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
