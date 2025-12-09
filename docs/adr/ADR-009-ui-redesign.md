# ADR-009: UI Redesign and Theme Overhaul

## Status

Accepted

## Context

The initial UI for the LLM Council was functional but lacked visual appeal and usability. The dark theme was described as "horrendous," and the layout for managing personalities was inefficient, with excessive whitespace and hidden controls. Users found it difficult to toggle personality status and navigate the settings.

## Decision

We decided to overhaul the UI with the following changes:

1. **Light Theme**: Switch to a "light, friendly, and premium" color scheme.
    - **Backgrounds**: Off-white (`#f8f9fa`) and white (`#ffffff`).
    - **Accents**: Soft blue (`#2563eb`) for primary actions.
    - **Typography**: Dark gray (`#1f2937`) for text to reduce harsh contrast.

2. **Personality Manager Layout**:
    - **Grid View**: Replace the vertical list with a responsive grid layout to better utilize screen real estate.
    - **Direct Actions**: Expose "Enable/Disable" toggles directly on the personality cards, removing the need to enter "Edit" mode for common actions.
    - **Compact Design**: Reduce padding and whitespace to fit more content on the screen.

3. **System Prompts Editor Layout**:
    - **Grouping**: Group "Model Selection" and "Prompt Editing" together for specific roles (Chairman, Title Generation) to improve logical flow.
    - **Ordering**: Place the Base System Prompt at the top as it applies globally.

4. **Full Width**:
    - Remove fixed `max-width` constraints on settings screens to allow them to fill the available viewport width (`100%`).

## Consequences

### Positive

- **Improved Usability**: Common actions (toggling personalities) are faster and more intuitive.
- **Better Aesthetics**: The application looks more modern and professional.
- **Efficient Space Usage**: The grid layout and full-width design make better use of large screens.

### Negative

- **Migration**: Existing users accustomed to the dark theme might need time to adjust (though feedback suggests the dark theme was disliked).
- **Maintenance**: New CSS variables and component structures need to be maintained.

## Compliance

- All new components must use the CSS variables defined in `index.css` to ensure theme consistency.
- Future UI additions should follow the established design patterns (cards, grids, soft shadows).
