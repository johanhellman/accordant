# CSS Architecture & Scoping Models

## Overview

To maintain a scalable and conflict-free frontend, Accordant follows strict CSS scoping rules. The application mixes a marketing site (Landing Page) and a complex web application (Council Dashboard). It is critical that styles from one context do not leak into the other.

## Core Rules

### 1. Component Scoping

**Rule:** Every component's CSS file MUST scope its styles to a unique top-level class for that component.

**❌ Bad:**

```css
/* In MyComponent.css */
/* Generic class name at root level */
.form-group {
    max-width: 500px;
}

button {
    background: blue;
}
```

**✅ Good:**

```css
/* In MyComponent.css */
/* Scoped to the component's container */
.my-component .form-group {
    max-width: 500px;
}

.my-component button {
    background: blue;
}
```

### 2. Global vs. Local Styles

* **Global Styles (`index.css`, `App.css`)**: Only for design tokens (variables), resets, and truly universal utility classes.
* **Local Styles (`Component.css`)**: All layout and decoration specific to a component.

### 3. Naming Conventions

* **Hyphen-delimited**: use `.kebab-case`.
* **Prefixing**: If a component is part of a larger subsystem (e.g., Landing Page), prefix its classes or wrap them in a namespace class.

### 4. Landing Page Isolation

The Landing Page frequently uses distinct layout rules (e.g., centered containers, different max-widths) that conflict with the Dashboard's full-width application layout.

**Rule:** All Landing Page specific styles MUST be scoped under `.accordant-landing` or use specific class names like `.landing-form-group` instead of generic ones like `.form-group`.

**Example:**

```css
/* AccordantLanding.css */
.accordant-landing .form-group {
    /* Safe: won't affect the dashboard */
    max-width: 500px;
    margin: 0 auto;
}
```

## Common Pitfalls

* **Generic Class Names**: Avoid defining properties on `.card`, `.sidebar`, `.header`, `.form-group` at the root level of a CSS file unless intended to apply *everywhere*.
* **Leaking Margins**: Setting `margin: 0 auto` on a generic class will center-align that element globally, breaking full-width layouts in other parts of the app.
