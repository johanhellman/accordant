/**
 * API client for the LLM Council backend.
 */

const API_BASE = "http://localhost:8001";

let authToken = null;

const getHeaders = () => {
  const headers = {
    "Content-Type": "application/json",
  };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
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

    const response = await fetch(`${API_BASE}/api/auth/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Login failed");
    }
    return response.json();
  },

  /**
   * Register a new user account.
   * @param {string} username - Desired username
   * @param {string} password - User password
   * @returns {Promise<{id: string, username: string}>}
   * @throws {Error} If registration fails (e.g., username already exists)
   */
  async register(username, password) {
    const response = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed");
    }
    return response.json();
  },

  /**
   * Get the currently authenticated user's information.
   * @returns {Promise<{id: string, username: string, org_id: string, is_admin: boolean}>}
   * @throws {Error} If user is not authenticated or request fails
   */
  async getCurrentUser() {
    const response = await fetch(`${API_BASE}/api/auth/me`, {
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to get current user");
    }
    return response.json();
  },

  /**
   * List all conversations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to list conversations");
    }
    return response.json();
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error("Failed to create conversation");
    }
    return response.json();
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to get conversation");
    }
    return response.json();
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/message`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      throw new Error("Failed to send message");
    }
    return response.json();
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent) {
    const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/message/stream`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      throw new Error("Failed to send message");
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
    const response = await fetch(`${API_BASE}/api/models`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to list models");
    return response.json();
  },

  /**
   * List all configured personalities for the current organization.
   * @returns {Promise<Array<{id: string, name: string, description: string, model: string, enabled: boolean}>>}
   * @throws {Error} If request fails
   */
  async listPersonalities() {
    const response = await fetch(`${API_BASE}/api/personalities`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to list personalities");
    return response.json();
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
    const response = await fetch(`${API_BASE}/api/personalities`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(personality),
    });
    if (!response.ok) throw new Error("Failed to create personality");
    return response.json();
  },

  /**
   * Update an existing personality configuration.
   * @param {string} id - Personality ID to update
   * @param {Object} personality - Updated personality configuration
   * @returns {Promise<Object>} Updated personality object
   * @throws {Error} If personality not found or request fails
   */
  async updatePersonality(id, personality) {
    const response = await fetch(`${API_BASE}/api/personalities/${id}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(personality),
    });
    if (!response.ok) throw new Error("Failed to update personality");
    return response.json();
  },

  /**
   * Delete a personality configuration.
   * @param {string} id - Personality ID to delete
   * @returns {Promise<{status: string, message: string}>}
   * @throws {Error} If personality not found or request fails
   */
  async deletePersonality(id) {
    const response = await fetch(`${API_BASE}/api/personalities/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to delete personality");
    return response.json();
  },

  /**
   * Get system prompts configuration for the current organization.
   * @returns {Promise<{base_system_prompt: string, ranking: Object, chairman: Object, title_generation: Object}>}
   * @throws {Error} If request fails
   */
  async getSystemPrompts() {
    const response = await fetch(`${API_BASE}/api/system-prompts`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get system prompts");
    return response.json();
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
    const response = await fetch(`${API_BASE}/api/system-prompts`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error("Failed to update system prompts");
    return response.json();
  },

  /**
   * Get global default system prompts configuration (Instance Admin only).
   */
  async getDefaultSystemPrompts() {
    const response = await fetch(`${API_BASE}/api/defaults/system-prompts`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get default system prompts");
    return response.json();
  },

  /**
   * Update global default system prompts configuration (Instance Admin only).
   */
  async updateDefaultSystemPrompts(config) {
    const response = await fetch(`${API_BASE}/api/defaults/system-prompts`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error("Failed to update default system prompts");
    return response.json();
  },

  async listUsers() {
    const response = await fetch(`${API_BASE}/api/admin/users`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to list users");
    return response.json();
  },

  async updateUserRole(userId, isAdmin) {
    const response = await fetch(`${API_BASE}/api/admin/users/${userId}/role`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify({ is_admin: isAdmin }),
    });
    if (!response.ok) throw new Error("Failed to update user role");
    return response.json();
  },

  async getVotingHistory() {
    const response = await fetch(`${API_BASE}/api/votes`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get voting history");
    return response.json();
  },

  async getOrgSettings() {
    const response = await fetch(`${API_BASE}/api/settings`, {
      headers: getHeaders(),
    });
    if (!response.ok) {
      const error = new Error(
        response.status === 401
          ? "Unauthorized: Authentication required"
          : `Failed to get organization settings (${response.status})`
      );
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  async updateOrgSettings(settings) {
    const response = await fetch(`${API_BASE}/api/settings`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(settings),
    });
    if (!response.ok) {
      const error = new Error(
        response.status === 401
          ? "Unauthorized: Authentication required"
          : `Failed to update organization settings (${response.status})`
      );
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  // --- Multi-Org API ---

  async createOrg(name, ownerEmail) {
    const response = await fetch(`${API_BASE}/api/organizations/`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ name, owner_email: ownerEmail }),
    });
    if (!response.ok) throw new Error("Failed to create organization");
    return response.json();
  },

  async joinOrg(inviteCode) {
    const response = await fetch(`${API_BASE}/api/organizations/join`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ invite_code: inviteCode }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Failed to join organization");
    }
    return response.json();
  },

  async createInvitation() {
    const response = await fetch(`${API_BASE}/api/organizations/invitations`, {
      method: "POST",
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to create invitation");
    return response.json();
  },

  async getInvitations() {
    const response = await fetch(`${API_BASE}/api/organizations/invitations`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get invitations");
    return response.json();
  },

  async listOrganizations() {
    const response = await fetch(`${API_BASE}/api/organizations/list`, {
      headers: getHeaders(),
      method: "GET",
    });
    if (!response.ok) {
      const error = new Error(
        response.status === 401
          ? "Unauthorized: Authentication required"
          : response.status === 403
            ? "Forbidden: Instance admin access required"
            : response.status === 405
              ? "Method not allowed: Route configuration issue"
              : `Failed to list organizations (${response.status})`
      );
      error.status = response.status;
      throw error;
    }
    return response.json();
  },
  // --- Instance Admin API (Defaults) ---

  async listDefaultPersonalities() {
    const response = await fetch(`${API_BASE}/api/defaults/personalities`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to list default personalities");
    return response.json();
  },

  async createDefaultPersonality(personality) {
    const response = await fetch(`${API_BASE}/api/defaults/personalities`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(personality),
    });
    if (!response.ok) throw new Error("Failed to create default personality");
    return response.json();
  },

  async updateDefaultPersonality(id, personality) {
    const response = await fetch(`${API_BASE}/api/defaults/personalities/${id}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(personality),
    });
    if (!response.ok) throw new Error("Failed to update default personality");
    return response.json();
  },

  async deleteDefaultPersonality(id) {
    const response = await fetch(`${API_BASE}/api/defaults/personalities/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to delete default personality");
    return response.json();
  },

  // --- League Table & Evolution API ---

  async getLeagueTable() {
    const response = await fetch(`${API_BASE}/api/league-table`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get league table");
    return response.json();
  },

  async getInstanceLeagueTable() {
    const response = await fetch(`${API_BASE}/api/instance-league-table`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get instance league table");
    return response.json();
  },

  async getPersonalityFeedback(id) {
    const response = await fetch(`${API_BASE}/api/personalities/${id}/feedback`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get personality feedback");
    return response.json();
  },

  async combinePersonalities(data) {
    const response = await fetch(`${API_BASE}/api/evolution/combine`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Failed to combine personalities");
    }
    return response.json();
  },

  async deactivatePersonality(id) {
    const response = await fetch(`${API_BASE}/api/evolution/deactivate`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ personality_id: id }),
    });
    if (!response.ok) throw new Error("Failed to deactivate personality");
    return response.json();
  },
};
