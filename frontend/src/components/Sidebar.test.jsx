import { render, screen } from "@testing-library/react";
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
    expect(screen.getByText("LLM Council")).toBeInTheDocument();
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

    // Check for Admin header
    expect(screen.getByRole("heading", { name: "Admin" })).toBeInTheDocument();

    // Check for Admin items
    expect(screen.getByText("Personalities")).toBeInTheDocument();
    expect(screen.getByText("System Prompts")).toBeInTheDocument();
    expect(screen.getByText("User Management")).toBeInTheDocument();
    expect(screen.getByText("Voting History")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();

    // Should NOT show Instance Admin section
    expect(screen.queryByRole("heading", { name: "Instance Admin" })).not.toBeInTheDocument();
    expect(screen.queryByText("Organizations")).not.toBeInTheDocument();
  });

  it("shows Instance Admin section for instance admins", () => {
    const instanceAdminProps = {
      ...defaultProps,
      user: { username: "superadmin", is_admin: true, is_instance_admin: true },
    };
    render(<Sidebar {...instanceAdminProps} />);

    // Check for Instance Admin header and items
    expect(screen.getByRole("heading", { name: "Instance Admin" })).toBeInTheDocument();
    expect(screen.getByText("Organizations")).toBeInTheDocument();

    // Check for Admin header and items (instance admin sees both)
    expect(screen.getByRole("heading", { name: "Admin" })).toBeInTheDocument();
    expect(screen.getByText("Personalities")).toBeInTheDocument();
  });

  it('does not show "Settings" for non-admin users', () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });
});
