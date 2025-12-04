/**
 * Tests for ChatInterface component.
 */

import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInterface from "./ChatInterface";

describe("ChatInterface", () => {
  beforeAll(() => {
    Element.prototype.scrollIntoView = vi.fn();
  });

  const mockOnSendMessage = vi.fn();

  beforeEach(() => {
    mockOnSendMessage.mockClear();
  });

  const mockConversation = {
    id: "test-id",
    title: "Test Conversation",
    messages: [
      {
        role: "user",
        content: "Hello",
      },
      {
        role: "assistant",
        stage1: [],
        stage2: [],
        stage3: {
          model: "test-model",
          response: "PART 2: FINAL ANSWER\n\nHello there!",
        },
      },
    ],
  };

  it("should render empty state when no conversation", () => {
    render(
      <ChatInterface conversation={null} onSendMessage={mockOnSendMessage} isLoading={false} />
    );

    expect(screen.getByText("Welcome to LLM Council")).toBeInTheDocument();
    expect(screen.getByText("Create a new conversation to get started")).toBeInTheDocument();
  });

  it("should render conversation messages", () => {
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hello there!")).toBeInTheDocument();
  });

  it("should allow user to type and send message", async () => {
    const user = userEvent.setup();
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await user.type(input, "New message");
    await user.click(sendButton);

    expect(mockOnSendMessage).toHaveBeenCalledWith("New message");
  });

  it("should clear input after sending message", async () => {
    const user = userEvent.setup();
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

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
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await user.type(input, "   "); // Only whitespace
    await user.click(sendButton);

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it("should disable input and button when loading", () => {
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={true}
      />
    );

    const input = screen.getByPlaceholderText(/ask your question/i);
    const sendButton = screen.getByRole("button", { name: /send/i });

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it("should submit on Enter key (without Shift)", async () => {
    const user = userEvent.setup();
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText(/ask your question/i);

    await user.type(input, "Test message{Enter}");

    expect(mockOnSendMessage).toHaveBeenCalledWith("Test message");
  });

  it("should not submit on Shift+Enter", async () => {
    const user = userEvent.setup();
    render(
      <ChatInterface
        conversation={mockConversation}
        onSendMessage={mockOnSendMessage}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText(/ask your question/i);

    await user.type(input, "Test message");
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });
});
