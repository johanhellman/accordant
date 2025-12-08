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

### CSS Custom Properties

```css
:root {
  /* Primary Colors */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-light: rgba(37, 99, 235, 0.1);
  --color-primary-border: rgba(37, 99, 235, 0.2);

  /* Secondary Colors */
  --color-secondary: #7c3aed;
  --color-secondary-hover: #6d28d9;

  /* Accent Colors */
  --color-accent-pink: #ec4899;
  --color-accent-orange: #f59e0b;
  --color-accent-green: #10b981;
  --color-accent-blue: #3b82f6;

  /* Functional Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-error-hover: #dc2626;
  --color-info: #3b82f6;

  /* Neutral Colors - Backgrounds */
  --color-bg-primary: #f8f9fa;
  --color-bg-secondary: #ffffff;
  --color-bg-tertiary: #f1f3f5;

  /* Neutral Colors - Text */
  --color-text-primary: #1f2937;
  --color-text-secondary: #4b5563;
  --color-text-muted: #9ca3af;

  /* Neutral Colors - Borders */
  --color-border: #e5e7eb;
}
```

### Gradients

```css
:root {
  /* Primary Gradient */
  --gradient-primary: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  
  /* Accent Gradients */
  --gradient-accent-1: linear-gradient(135deg, #ec4899 0%, #f59e0b 100%);
  --gradient-accent-2: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
  
  /* Text Gradient */
  --gradient-text: linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #ec4899 100%);
}
```

### JavaScript/TypeScript Tokens

```typescript
export const colors = {
  primary: {
    base: '#2563eb',
    hover: '#1d4ed8',
    light: 'rgba(37, 99, 235, 0.1)',
    border: 'rgba(37, 99, 235, 0.2)',
  },
  secondary: {
    base: '#7c3aed',
    hover: '#6d28d9',
  },
  accent: {
    pink: '#ec4899',
    orange: '#f59e0b',
    green: '#10b981',
    blue: '#3b82f6',
  },
  functional: {
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    errorHover: '#dc2626',
    info: '#3b82f6',
  },
  neutral: {
    bg: {
      primary: '#f8f9fa',
      secondary: '#ffffff',
      tertiary: '#f1f3f5',
    },
    text: {
      primary: '#1f2937',
      secondary: '#4b5563',
      muted: '#9ca3af',
    },
    border: '#e5e7eb',
  },
} as const;

export const gradients = {
  primary: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
  accent1: 'linear-gradient(135deg, #ec4899 0%, #f59e0b 100%)',
  accent2: 'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)',
  text: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #ec4899 100%)',
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

### CSS Custom Properties

```css
:root {
  --radius-sm: 0.25rem;   /* 4px */
  --radius-md: 0.5rem;    /* 8px */
  --radius-lg: 0.75rem;   /* 12px */
  --radius-xl: 1rem;     /* 16px */
  --radius-2xl: 1.25rem; /* 20px */
  --radius-full: 9999px;
}
```

### JavaScript/TypeScript

```typescript
export const radius = {
  sm: '0.25rem',   // 4px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px
  xl: '1rem',      // 16px
  '2xl': '1.25rem', // 20px
  full: '9999px',
} as const;
```

---

## Shadow Tokens

### CSS Custom Properties

```css
:root {
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 
               0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 
               0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 
               0 8px 10px -6px rgb(0 0 0 / 0.1);
}
```

### JavaScript/TypeScript

```typescript
export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
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
          DEFAULT: '#2563eb',
          hover: '#1d4ed8',
        },
        // ... other colors
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        // ... spacing scale
      },
      borderRadius: {
        // ... radius scale
      },
      boxShadow: {
        // ... shadow scale
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
