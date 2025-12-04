# Admin Guide

This guide is for administrators managing the LLM Council application.

## Roles

There are two types of administrators:

1.  **Instance Admin**: Has full control over the entire deployment, including all organizations and users.
2.  **Organization Admin**: Has control over a specific organization, its users, and its settings.

## Instance Admin Tasks

Instance Admins have access to all Organization Admin features (see below) plus system-wide management capabilities.

### Accessing Admin Features
1. Log in to the application.
2. Click on "Settings" in the sidebar (under the Admin section).
3. Instance Admins will see the "Instance Admin" badge next to their username.

### Managing Organizations
Currently, organization management is done via the API or directly in the database (`data/organizations.json`).
- **Create Org**: Use the `POST /api/organizations` endpoint.
- **List Orgs**: Use the `GET /api/organizations` endpoint (Admin only).

### Managing Users
- **Promote to Instance Admin**: Edit `data/users.json` and set `is_instance_admin: true` for the user.
- **Move User**: Use the `update_user_org` function in `backend/users.py` (via script) or the API if available.

## Organization Admin Tasks

### Accessing Settings
1.  Log in to the application.
2.  Click on "Settings" in the sidebar (under the Admin section).

### Configuring API Keys
**Critical**: Each organization must configure its own LLM API keys to function.
1.  Go to **Settings**.
2.  Enter your **OpenRouter API Key**.
3.  (Optional) Update the **Base URL** if using a different provider compatible with the OpenAI API format.
4.  Click **Save Settings**.

*Note: The API key is encrypted before storage and is never shown in plain text in the UI.*

### Managing Invitations
To add new users to your organization:
1.  Go to **Settings**.
2.  Scroll to the **Invitations** section.
3.  Click **Generate New Invite Code**.
4.  Share the generated code with the user.
5.  The user can use this code during registration by selecting "Join Existing" and entering the code.

### Managing Personalities
Organization Admins (and Instance Admins) can customize the personalities available to their users.
1.  Go to **Personalities** in the sidebar.
2.  Enable/Disable specific personalities.
3.  Edit system prompts for specific personalities to tailor them to your organization's needs.

**Note**: When a new organization is created, all default personalities from `data/personalities/` are automatically copied to the organization's personalities directory.

## Troubleshooting

### "LLM API Key not configured"
If users see this error, it means the Organization Admin has not yet configured the API key in the Settings page.

### "Invitation code invalid"
- Check if the code has already been used (codes are single-use).
- Check if the code has expired (default expiry is 7 days).
- Generate a new code if necessary.
