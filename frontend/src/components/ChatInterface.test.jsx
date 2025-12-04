/**
 * Tests for ChatInterface component.
 */

import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMockConversation, renderChatInterface } from "../test/helpers";

describe("ChatInterface", () => {
  beforeAll(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  const mockOnSendMessage = vi.fn();

  beforeEach(() => {
    mockOnSendMessage.mockClear();
  });

  const mockConversation = createMockConversation();

  it("should render empty state when no conversation", () => {
    renderChatInterface({
      conversation: null,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    expect(screen.getByText("Welcome to LLM Council")).toBeInTheDocument();
    expect(screen.getByText("Create a new conversation to get started")).toBeInTheDocument();
  });

  it("should render conversation messages", () => {
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hello there!")).toBeInTheDocument();
  });

  it("should allow user to type and send message", async () => {
    const user = userEvent.setup();
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await user.type(input, "New message");
    await user.click(sendButton);

    expect(mockOnSendMessage).toHaveBeenCalledWith("New message");
  });

  it("should clear input after sending message", async () => {
    const user = userEvent.setup();
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await user.type(input, "New message");
    await user.click(sendButton);

    await waitFor(() => {
      expect(input).toHaveValue("");
    });
  });

  it("should not send empty messages", async () => {
    const user = userEvent.setup();
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await user.type(input, "   "); // Only whitespace
    await user.click(sendButton);

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it("should disable input and button when loading", () => {
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: true,
    });

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it("should submit on Enter key (without Shift)", async () => {
    const user = userEvent.setup();
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    const input = screen.getByPlaceholderText(/ask your question/i);

    await user.type(input, "Test message{Enter}");

    expect(mockOnSendMessage).toHaveBeenCalledWith("Test message");
  });

  it("should not submit on Shift+Enter", async () => {
    const user = userEvent.setup();
    renderChatInterface({
      conversation: mockConversation,
      onSendMessage: mockOnSendMessage,
      isLoading: false,
    });

    const input = screen.getByPlaceholderText(/ask your question/i);

    await user.type(input, "Test message");
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });
});
