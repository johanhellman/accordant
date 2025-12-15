import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Sidebar from "./Sidebar";

describe("Sidebar", () => {
  const defaultProps = {
    conversations: [],
    currentConversationId: null,
    onSelectConversation: vi.fn(),
    onNewConversation: vi.fn(),
    currentView: "chat",
    onViewChange: vi.fn(),
    user: { username: "testuser", is_admin: false },
    onLogout: vi.fn(),
  };

  it("renders without crashing", () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByText("Accordant")).toBeInTheDocument();
  });

  it("does not show Admin section for non-admin users", () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
    expect(screen.queryByText("Personalities")).not.toBeInTheDocument();
    expect(screen.queryByText("System Prompts")).not.toBeInTheDocument();
    expect(screen.queryByText("User Management")).not.toBeInTheDocument();
    expect(screen.queryByText("Voting History")).not.toBeInTheDocument();
  });

  it("shows Admin section for admin users", () => {
    const adminProps = {
      ...defaultProps,
      user: { username: "admin", is_admin: true },
    };
    render(<Sidebar {...adminProps} />);

    // Check for Admin header existence
    expect(screen.getByText("Council Setup")).toBeInTheDocument();

    // Expand Council Setup
    fireEvent.click(screen.getByText("Council Setup"));
    expect(screen.getByText("Personalities")).toBeInTheDocument();

    // Expand Organization
    fireEvent.click(screen.getByText("Organization"));
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("shows Instance Admin section for instance admins", () => {
    const instanceAdminProps = {
      ...defaultProps,
      user: { username: "superadmin", is_admin: true, is_instance_admin: true },
    };
    render(<Sidebar {...instanceAdminProps} />);

    // Expand Organization (Instance Admin sees Dashboard and Organizations here)
    fireEvent.click(screen.getByText("Organization"));
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Organizations")).toBeInTheDocument();

    // Also sees regular admin items
    fireEvent.click(screen.getByText("Council Setup"));
    expect(screen.getByText("Personalities")).toBeInTheDocument();
  });

  it('does not show "Settings" for non-admin users', () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });
});
