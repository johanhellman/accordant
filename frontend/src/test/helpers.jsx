/**
 * Test helpers for ChatInterface component tests.
 * Reduces duplication by providing common test utilities.
 */

import { vi } from "vitest";
import { render } from "@testing-library/react";
import ChatInterface from "../components/ChatInterface";

/**
 * Creates a mock conversation object for testing.
 * @param {Object} overrides - Optional overrides for default conversation values
 * @returns {Object} Mock conversation object
 */
export function createMockConversation(overrides = {}) {
  return {
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
    ...overrides,
  };
}

/**
 * Renders ChatInterface with common props.
 * @param {Object} props - Props to pass to ChatInterface
 * @returns {Object} Render result from @testing-library/react
 */
export function renderChatInterface(props = {}) {
  const defaultProps = {
    conversation: null,
    onSendMessage: vi.fn(),
    isLoading: false,
  };

  return render(<ChatInterface {...defaultProps} {...props} />);
}
