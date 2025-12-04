# LLM Council Frontend

This is the React-based frontend for the LLM Council application. It provides a user interface for interacting with the "Council" of LLMs, managing personalities, and configuring system prompts.

## Features

- **Chat Interface**: Multi-turn chat with the LLM Council.
  - **Stage 1**: View individual responses from each council member.
  - **Stage 2**: View peer reviews and rankings.
  - **Stage 3**: View the final synthesized response from the Chairman.
- **Personality Manager**: Create, edit, enable/disable, and delete LLM personalities.
  - **Grid View**: Responsive grid layout for managing personalities.
  - **Direct Toggles**: Enable/disable personalities directly from the card.
- **System Prompts Editor**: Configure global system prompts and specific roles.
  - **Chairman Configuration**: Select the model and prompt for the final synthesis.
  - **Title Generation**: Select the model and prompt for conversation titles.
- **Voting History**: View and analyze past voting sessions.
  - **History View**: Scrollable list of past votes with detailed breakdown.
  - **Statistics View**: Heatmap visualization of "Personality vs Personality" voting trends.
  - **Filtering**: Filter history and statistics by User, Date Range, and Enabled Personalities.
  - **Sorting**: Heatmap columns sorted by performance (Average Rank Received), rows sorted alphabetically.
  - **Management**: Manually delete voting history via API/CLI.
- **Light Theme**: A clean, friendly, and premium UI design.

## Project Structure

```
src/
├── components/
│   ├── ChatInterface.jsx       # Main chat view
│   ├── PersonalityManager.jsx  # Personality management UI
│   ├── SystemPromptsEditor.jsx # System prompts configuration UI
│   ├── Sidebar.jsx             # Navigation sidebar
│   ├── Stage1.jsx              # Individual responses view
│   ├── Stage2.jsx              # Peer review view
│   ├── Stage3.jsx              # Final response view
│   └── ... (CSS files)
├── api.js                      # API client for backend communication
├── App.jsx                     # Main application component & routing
├── main.jsx                    # Entry point
└── index.css                   # Global styles and theme variables
```

## Theme

The application uses a light theme defined in `src/index.css` using CSS variables. Key variables include:

- `--bg-primary`: Main background color (off-white)
- `--bg-secondary`: Surface color (white)
- `--primary-color`: Primary accent color (soft blue)
- `--text-primary`: Main text color (dark gray)

## Development

### Install Dependencies

```bash
npm install
```

### Run Dev Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

### Linting

```bash
npm run lint
```
