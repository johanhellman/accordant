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
  setToken(token) {
    authToken = token;
  },

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

  async listModels() {
    const response = await fetch(`${API_BASE}/api/models`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to list models");
    return response.json();
  },

  async listPersonalities() {
    const response = await fetch(`${API_BASE}/api/personalities`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to list personalities");
    return response.json();
  },

  async createPersonality(personality) {
    const response = await fetch(`${API_BASE}/api/personalities`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(personality),
    });
    if (!response.ok) throw new Error("Failed to create personality");
    return response.json();
  },

  async updatePersonality(id, personality) {
    const response = await fetch(`${API_BASE}/api/personalities/${id}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(personality),
    });
    if (!response.ok) throw new Error("Failed to update personality");
    return response.json();
  },

  async deletePersonality(id) {
    const response = await fetch(`${API_BASE}/api/personalities/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to delete personality");
    return response.json();
  },

  async getSystemPrompts() {
    const response = await fetch(`${API_BASE}/api/system-prompts`, {
      headers: getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to get system prompts");
    return response.json();
  },

  async updateSystemPrompts(config) {
    const response = await fetch(`${API_BASE}/api/system-prompts`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error("Failed to update system prompts");
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
};
