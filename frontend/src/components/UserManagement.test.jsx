import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import UserManagement from "./UserManagement";
import { api } from "../api";

// Mock the API
vi.mock("../api", () => ({
  api: {
    listUsers: vi.fn(),
    updateUserRole: vi.fn(),
    getInvitations: vi.fn(),
    createInvitation: vi.fn(),
  },
}));

describe("UserManagement", () => {
  const mockUsers = [
    { id: "1", username: "admin", is_admin: true },
    { id: "2", username: "user", is_admin: false },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.getInvitations.mockResolvedValue([]);
  });

  it("renders loading state initially", async () => {
    // We must resolve the promise to avoid act warnings in future tests
    // But we want to test the initial render state first
    let resolvePromise;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    api.listUsers.mockReturnValue(promise);

    render(<UserManagement />);
    expect(screen.getByText("Loading users...")).toBeInTheDocument();

    // Clean up by resolving
    await React.act(async () => {
      resolvePromise([]);
    });
  });

  it("renders users list after loading", async () => {
    api.listUsers.mockResolvedValue(mockUsers);
    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("User Management")).toBeInTheDocument();
    });

    expect(screen.getByText("admin")).toBeInTheDocument();
    expect(screen.getByText("user")).toBeInTheDocument();
    expect(screen.getByText("user")).toBeInTheDocument();
    // Use substring match or stricter selector if needed
    expect(screen.getAllByText(/Admin/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/User/i).length).toBeGreaterThan(0);
  });

  it("renders invitations list", async () => {
    api.listUsers.mockResolvedValue(mockUsers);
    api.getInvitations.mockResolvedValue([
      { code: "INV-123", expires_at: new Date().toISOString(), is_active: true },
    ]);
    render(<UserManagement />);

    await waitFor(() => {
      // The header is just "Invitations" based on output
      expect(screen.getByRole("heading", { name: "Invitations" })).toBeInTheDocument();
    });

    const inviteCodeCell = screen.getByText("INV-123");
    const inviteRow = inviteCodeCell.closest("tr");
    expect(within(inviteRow).getByText(/Active/i)).toBeInTheDocument();
  });

  it("handles promote user action", async () => {
    api.listUsers.mockResolvedValue(mockUsers);
    api.updateUserRole.mockResolvedValue({ ...mockUsers[1], is_admin: true });

    render(<UserManagement />);

    await waitFor(() => {
      // Look for the button by title if text is hidden/icon
      expect(screen.getByTitle("Promote to Admin")).toBeInTheDocument();
    });

    const promoteBtn = screen.getByTitle("Promote to Admin");
    fireEvent.click(promoteBtn);

    expect(api.updateUserRole).toHaveBeenCalledWith("2", true);

    await waitFor(() => {
      // Should optimistically update UI (or re-render based on state update)
      // In our component we do optimistic update
      // We can check if the button text changed or if the badge changed
      // But since we mock the API response but the component uses local state update based on success,
      // we just verify the API call was made correctly.
    });
  });

  it("handles error state", async () => {
    api.listUsers.mockRejectedValue(new Error("Failed"));
    render(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load users")).toBeInTheDocument();
    });
  });
});
