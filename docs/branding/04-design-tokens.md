# Design Tokens & Implementation Guide

## Overview

Design tokens are the building blocks of Accordant's design system. They provide a single source of truth for colors, typography, spacing, and other design decisions, ensuring consistency across all platforms and implementations.

---

## Token Structure

Design tokens are organized hierarchically:

```
Category (e.g., color)
  └── Subcategory (e.g., primary)
      └── Variant (e.g., base, hover)
          └── Value (e.g., #2563eb)
```

---

## Color Tokens

### Warm Intelligence Palette

Accordant uses a distinctive **Warm Intelligence** color palette that emphasizes collaboration, warmth, and sophistication. This palette moves away from conventional corporate blues toward a more inviting violet and pink combination.

### CSS Custom Properties

```css
:root {
  /* Primary - Warm, intelligent violet */
  --color-primary: #8b5cf6;
  --color-primary-dark: #7c3aed;
  --color-primary-light: #a78bfa;
  --color-primary-hover: #7c3aed;
  --color-primary-subtle: rgba(139, 92, 246, 0.1);
  --color-primary-border: rgba(139, 92, 246, 0.2);

  /* Secondary - Warm pink for collaboration */
  --color-secondary: #f472b6;
  --color-secondary-hover: #ec4899;
  --color-secondary-light: #f9a8d4;

  /* Accent - Warm orange */
  --color-accent: #fb923c;
  --color-accent-hover: #f97316;
  --color-accent-pink: #f472b6;
  --color-accent-orange: #fb923c;
  --color-accent-green: #10b981;
  --color-accent-blue: #3b82f6;

  /* Functional Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-error-hover: #dc2626;
  --color-info: #8b5cf6;

  /* Neutral Colors - Warmer grays */
  --color-bg-primary: #fafaf9;
  --color-bg-secondary: #ffffff;
  --color-bg-tertiary: #f5f5f4;

  /* Text - Warmer tones */
  --color-text-primary: #292524;
  --color-text-secondary: #78716c;
  --color-text-muted: #a8a29e;

  /* Borders - Warm */
  --color-border: #e7e5e4;
}
```

### Gradients

```css
:root {
  /* Primary Gradient - Violet to Pink */
  --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #f472b6 100%);

  /* Subtle Background Gradient */
  --gradient-subtle: linear-gradient(135deg, #faf5ff 0%, #fdf2f8 100%);

  /* Accent Gradients */
  --gradient-accent-1: linear-gradient(135deg, #f472b6 0%, #fb923c 100%);
  --gradient-accent-2: linear-gradient(135deg, #10b981 0%, #8b5cf6 100%);

  /* Text Gradient */
  --gradient-text: linear-gradient(135deg, #8b5cf6 0%, #f472b6 50%, #fb923c 100%);
}
```

### JavaScript/TypeScript Tokens

```typescript
export const colors = {
  primary: {
    base: '#8b5cf6',
    dark: '#7c3aed',
    light: '#a78bfa',
    hover: '#7c3aed',
    subtle: 'rgba(139, 92, 246, 0.1)',
    border: 'rgba(139, 92, 246, 0.2)',
  },
  secondary: {
    base: '#f472b6',
    hover: '#ec4899',
    light: '#f9a8d4',
  },
  accent: {
    base: '#fb923c',
    hover: '#f97316',
    pink: '#f472b6',
    orange: '#fb923c',
    green: '#10b981',
    blue: '#3b82f6',
  },
  functional: {
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    errorHover: '#dc2626',
    info: '#8b5cf6',
  },
  neutral: {
    bg: {
      primary: '#fafaf9',
      secondary: '#ffffff',
      tertiary: '#f5f5f4',
    },
    text: {
      primary: '#292524',
      secondary: '#78716c',
      muted: '#a8a29e',
    },
    border: '#e7e5e4',
  },
} as const;

export const gradients = {
  primary: 'linear-gradient(135deg, #8b5cf6 0%, #f472b6 100%)',
  subtle: 'linear-gradient(135deg, #faf5ff 0%, #fdf2f8 100%)',
  accent1: 'linear-gradient(135deg, #f472b6 0%, #fb923c 100%)',
  accent2: 'linear-gradient(135deg, #10b981 0%, #8b5cf6 100%)',
  text: 'linear-gradient(135deg, #8b5cf6 0%, #f472b6 50%, #fb923c 100%)',
} as const;
```

---

## Typography Tokens

### CSS Custom Properties

```css
:root {
  /* Font Family */
  --font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  
  /* Font Sizes */
  --font-size-xs: 0.75rem;    /* 12px */
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.125rem;   /* 18px */
  --font-size-xl: 1.25rem;    /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 2rem;     /* 32px */
  --font-size-4xl: 3rem;     /* 48px */
  --font-size-display: clamp(2.5rem, 5vw, 4rem); /* 40px - 64px */
  
  /* Font Weights */
  --font-weight-light: 300;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;
  --font-weight-extrabold: 800;
  
  /* Line Heights */
  --line-height-tight: 1.1;
  --line-height-snug: 1.3;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.6;
  --line-height-loose: 1.7;
  
  /* Letter Spacing */
  --letter-spacing-tight: -0.02em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.025em;
}
```

### Typography Scale (JavaScript)

```typescript
export const typography = {
  fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '2rem',      // 32px
    '4xl': '3rem',      // 48px
    display: 'clamp(2.5rem, 5vw, 4rem)', // 40px - 64px
  },
  fontWeight: {
    light: 300,
    regular: 400,
    medium: 500,
    bold: 700,
    extrabold: 800,
  },
  lineHeight: {
    tight: 1.1,
    snug: 1.3,
    normal: 1.5,
    relaxed: 1.6,
    loose: 1.7,
  },
  letterSpacing: {
    tight: '-0.02em',
    normal: '0',
    wide: '0.025em',
  },
} as const;
```

---

## Spacing Tokens

### CSS Custom Properties

```css
:root {
  --spacing-0: 0;
  --spacing-1: 0.25rem;  /* 4px */
  --spacing-2: 0.5rem;   /* 8px */
  --spacing-3: 0.75rem;  /* 12px */
  --spacing-4: 1rem;     /* 16px */
  --spacing-5: 1.25rem;  /* 20px */
  --spacing-6: 1.5rem;   /* 24px */
  --spacing-8: 2rem;     /* 32px */
  --spacing-10: 2.5rem;  /* 40px */
  --spacing-12: 3rem;    /* 48px */
  --spacing-16: 4rem;    /* 64px */
  --spacing-20: 5rem;    /* 80px */
  --spacing-24: 6rem;    /* 96px */
}
```

### JavaScript/TypeScript Spacing

```typescript
export const spacing = {
  0: '0',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
  20: '5rem',    // 80px
  24: '6rem',    // 96px
} as const;
```

---

## Border Radius Tokens

### Organic, Varied Radii

Accordant uses an **organic border radius system** that creates visual interest through variation. Rather than uniform rounded corners, we use different radii for different components to create a more sophisticated, less generic feel.

### CSS Custom Properties

```css
:root {
  /* Semantic Radii - New System */
  --radius-subtle: 0.375rem;  /* 6px - Small UI elements */
  --radius-soft: 1rem;        /* 16px - Cards, main containers */
  --radius-organic: 1.5rem;   /* 24px - Feature elements, large cards */
  --radius-pill: 100px;       /* Pills, badges */

  /* Legacy Support - Gradual Migration */
  --radius-sm: 0.375rem;   /* 6px */
  --radius-md: 0.5rem;     /* 8px */
  --radius-lg: 1rem;       /* 16px */
  --radius-xl: 1.5rem;     /* 24px */
  --radius-2xl: 2rem;      /* 32px */
  --radius-full: 9999px;
}
```

### Usage Guidelines

- **--radius-subtle (6px)**: Small buttons, inputs, badges
- **--radius-soft (16px)**: Standard cards, message boxes, tabs
- **--radius-organic (24px)**: Large feature cards, stage containers, modals
- **--radius-pill (100px)**: Pills, tags, rounded badges

### JavaScript/TypeScript

```typescript
export const radius = {
  // New organic system
  subtle: '0.375rem',  // 6px
  soft: '1rem',        // 16px
  organic: '1.5rem',   // 24px
  pill: '100px',

  // Legacy support
  sm: '0.375rem',   // 6px
  md: '0.5rem',     // 8px
  lg: '1rem',       // 16px
  xl: '1.5rem',     // 24px
  '2xl': '2rem',    // 32px
  full: '9999px',
} as const;
```

---

## Shadow Tokens

### Softer, More Sophisticated Shadows

Accordant uses **softer, more sophisticated shadows** that create depth without harshness. The shadow system emphasizes subtlety and refinement over dramatic elevation changes.

### CSS Custom Properties

```css
:root {
  /* New Semantic Shadows */
  --shadow-soft: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-medium: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-large: 0 12px 32px rgba(0, 0, 0, 0.12);
  --shadow-glow: 0 0 0 3px rgba(139, 92, 246, 0.1);  /* Focus/accent glow */

  /* Legacy Support */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.12);
  --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.15);
}
```

### Usage Guidelines

- **--shadow-soft**: Cards, message containers, subtle elevation
- **--shadow-medium**: Buttons, dropdowns, moderate elevation
- **--shadow-large**: Modals, popovers, high elevation
- **--shadow-glow**: Focus states, active accents, highlights

### JavaScript/TypeScript

```typescript
export const shadows = {
  // New semantic shadows
  soft: '0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
  medium: '0 4px 12px rgba(0, 0, 0, 0.08)',
  large: '0 12px 32px rgba(0, 0, 0, 0.12)',
  glow: '0 0 0 3px rgba(139, 92, 246, 0.1)',

  // Legacy support
  sm: '0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
  md: '0 4px 12px rgba(0, 0, 0, 0.08)',
  lg: '0 12px 32px rgba(0, 0, 0, 0.12)',
  xl: '0 20px 40px rgba(0, 0, 0, 0.15)',
} as const;
```

---

## Animation Tokens

### CSS Custom Properties

```css
:root {
  /* Durations */
  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;
  
  /* Easing */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;
}
```

### JavaScript/TypeScript

```typescript
export const animations = {
  duration: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
  },
  easing: {
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  transition: {
    fast: '150ms ease',
    base: '200ms ease',
    slow: '300ms ease',
  },
} as const;
```

---

## Icon Tokens

### CSS Custom Properties

```css
:root {
  --icon-xs: 0.75rem;  /* 12px */
  --icon-sm: 1rem;     /* 16px */
  --icon-md: 1.25rem;  /* 20px */
  --icon-lg: 1.5rem;   /* 24px */
  --icon-xl: 2rem;     /* 32px */
  --icon-2xl: 3rem;    /* 48px */
}
```

### JavaScript/TypeScript

```typescript
export const icons = {
  xs: '0.75rem',   // 12px
  sm: '1rem',      // 16px
  md: '1.25rem',   // 20px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
} as const;
```

---

## Breakpoint Tokens

### CSS Custom Properties

```css
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}
```

### JavaScript/TypeScript

```typescript
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;
```

---

## Complete Token Export (TypeScript)

```typescript
// tokens.ts
export const tokens = {
  colors,
  gradients,
  typography,
  spacing,
  radius,
  shadows,
  animations,
  icons,
  breakpoints,
} as const;

export type Tokens = typeof tokens;
```

---

## Usage Examples

### CSS Usage

```css
/* Using CSS custom properties */
.button-primary {
  background: var(--gradient-primary);
  color: white;
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  box-shadow: var(--shadow-md);
  transition: var(--transition-base);
}

.button-primary:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### React/TypeScript Usage

```typescript
import { tokens } from './tokens';

const ButtonPrimary = styled.button`
  background: ${tokens.gradients.primary};
  color: white;
  padding: ${tokens.spacing[4]} ${tokens.spacing[8]};
  border-radius: ${tokens.radius.lg};
  font-size: ${tokens.typography.fontSize.base};
  font-weight: ${tokens.typography.fontWeight.bold};
  box-shadow: ${tokens.shadows.md};
  transition: ${tokens.animations.transition.base};
  
  &:hover {
    box-shadow: ${tokens.shadows.lg};
    transform: translateY(-2px);
  }
`;
```

### Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#8b5cf6',
          dark: '#7c3aed',
          light: '#a78bfa',
          hover: '#7c3aed',
        },
        secondary: {
          DEFAULT: '#f472b6',
          hover: '#ec4899',
          light: '#f9a8d4',
        },
        // ... other colors
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'subtle': '0.375rem',
        'soft': '1rem',
        'organic': '1.5rem',
        'pill': '100px',
      },
      boxShadow: {
        'soft': '0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 12px rgba(0, 0, 0, 0.08)',
        'large': '0 12px 32px rgba(0, 0, 0, 0.12)',
        'glow': '0 0 0 3px rgba(139, 92, 246, 0.1)',
      },
    },
  },
};
```

---

## Token Naming Conventions

### Color Naming

- Use semantic names: `primary`, `success`, `error`
- Use descriptive modifiers: `hover`, `light`, `border`
- Avoid color names: Don't use `blue`, `red` (use `primary`, `error`)

### Spacing Naming

- Use numeric scale: `1`, `2`, `4`, `8`
- Based on 4px unit: `spacing-4` = 16px

### Typography Naming

- Use size names: `xs`, `sm`, `base`, `lg`, `xl`
- Use weight names: `light`, `regular`, `bold`

---

## Token Maintenance

### Version Control

- Store tokens in version control
- Tag releases with token versions
- Document breaking changes

### Documentation

- Keep token documentation up to date
- Include usage examples
- Document new tokens as they're added

### Testing

- Test token usage across platforms
- Verify accessibility (contrast ratios)
- Check consistency in implementation

---

## Migration Guide

### From Hardcoded Values to Tokens

**Before:**

```css
.button {
  background: #2563eb;
  padding: 16px 32px;
  border-radius: 8px;
}
```

**After:**

```css
.button {
  background: var(--color-primary);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-md);
}
```

---

## Next Steps

1. Implement tokens in codebase
2. Create token generation scripts
3. Build token documentation site
4. Create token testing suite
5. Establish token review process
