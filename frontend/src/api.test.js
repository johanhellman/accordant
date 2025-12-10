/**
 * Tests for API client (api.js).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock import.meta.env before importing api
vi.stubGlobal("import.meta", {
  env: {
    VITE_API_BASE: "http://localhost:8001",
  },
});

import { api } from "./api";

describe("API Client", () => {
  const originalFetch = global.fetch;
  const mockFetch = vi.fn();

  beforeEach(() => {
    global.fetch = mockFetch;
  });

  afterEach(() => {
    vi.clearAllMocks();
    global.fetch = originalFetch;
  });

  describe("getCurrentUser", () => {
    it("should fetch current user details", async () => {
      const mockUser = { id: "1", username: "test", is_admin: false };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      const result = await api.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(mockFetch).toHaveBeenCalledWith("http://localhost:8001/api/auth/me", {
        headers: {
          "Content-Type": "application/json",
        },
      });
    });

    it("should throw error on failed request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      await expect(api.getCurrentUser()).rejects.toThrow("Failed to get current user");
    });
  });

  describe("listConversations", () => {
    it("should fetch and return conversations list", async () => {
      const mockConversations = [
        { id: "1", title: "Test 1", message_count: 2 },
        { id: "2", title: "Test 2", message_count: 1 },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConversations,
      });

      const result = await api.listConversations();

      expect(result).toEqual(mockConversations);
      expect(mockFetch).toHaveBeenCalledWith("http://localhost:8001/api/conversations", {
        headers: {
          "Content-Type": "application/json",
        },
      });
    });

    it("should throw error on failed request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(api.listConversations()).rejects.toThrow("Failed to list conversations");
    });
  });

  describe("createConversation", () => {
    it("should create a new conversation", async () => {
      const mockConversation = {
        id: "new-id",
        title: "New Conversation",
        messages: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConversation,
      });

      const result = await api.createConversation();

      expect(result).toEqual(mockConversation);
      expect(mockFetch).toHaveBeenCalledWith("http://localhost:8001/api/conversations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
    });

    it("should throw error on failed request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(api.createConversation()).rejects.toThrow("Failed to create conversation");
    });
  });

  describe("getConversation", () => {
    it("should fetch a specific conversation", async () => {
      const conversationId = "test-id";
      const mockConversation = {
        id: conversationId,
        title: "Test Conversation",
        messages: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConversation,
      });

      const result = await api.getConversation(conversationId);

      expect(result).toEqual(mockConversation);
      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8001/api/conversations/${conversationId}`,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
    });

    it("should throw error on failed request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(api.getConversation("non-existent")).rejects.toThrow(
        "Failed to get conversation"
      );
    });
  });

  describe("sendMessage", () => {
    it("should send a message and return response", async () => {
      const conversationId = "test-id";
      const content = "Hello, world!";
      const mockResponse = {
        stage1: [],
        stage2: [],
        stage3: { model: "test", response: "Response" },
        metadata: {},
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await api.sendMessage(conversationId, content);

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8001/api/conversations/${conversationId}/message`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ content }),
        }
      );
    });

    it("should throw error on failed request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(api.sendMessage("test-id", "Hello")).rejects.toThrow("Failed to send message");
    });
  });

  describe("sendMessageStream", () => {
    it("should stream messages and call onEvent for each event", async () => {
      const conversationId = "test-id";
      const content = "Hello, world!";
      const onEvent = vi.fn();

      // Mock ReadableStream
      const mockEvents = [
        'data: {"type":"stage1_start"}\n\n',
        'data: {"type":"stage1_complete","data":[]}\n\n',
        'data: {"type":"complete"}\n\n',
      ];

      const mockReader = {
        read: vi.fn(),
      };

      let callCount = 0;
      mockReader.read.mockImplementation(() => {
        if (callCount < mockEvents.length) {
          const value = new TextEncoder().encode(mockEvents[callCount]);
          callCount++;
          return Promise.resolve({ done: false, value });
        }
        return Promise.resolve({ done: true, value: undefined });
      });

      const mockBody = {
        getReader: () => mockReader,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: mockBody,
      });

      await api.sendMessageStream(conversationId, content, onEvent);

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8001/api/conversations/${conversationId}/message/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ content }),
        }
      );

      // Verify events were called
      expect(onEvent).toHaveBeenCalledWith("stage1_start", { type: "stage1_start" });
      expect(onEvent).toHaveBeenCalledWith("stage1_complete", {
        type: "stage1_complete",
        data: [],
      });
      expect(onEvent).toHaveBeenCalledWith("complete", { type: "complete" });
    });

    it("should throw error on failed request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(api.sendMessageStream("test-id", "Hello", vi.fn())).rejects.toThrow(
        "Failed to send message"
      );
    });
  });
});
