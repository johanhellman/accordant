# Visual Identity Guide

## Overview

Accordant's visual identity reflects our core values: collaboration, transparency, quality, and innovation. Our design system balances professionalism with approachability, using modern gradients, clean typography, and thoughtful spacing to create a cohesive experience across all touchpoints.

---

## Logo System

### Primary Logo

The Accordant logo combines the **Sparkles icon** (✨) with the wordmark "Accordant" to represent the collaborative spark of multiple AI personalities coming together.

**Logo Components:**

- **Icon**: Sparkles symbol (Lucide React icon)
- **Wordmark**: "Accordant" in bold, modern typography
- **Layout**: Horizontal arrangement with icon on the left

**Usage:**

- Primary logo should be used in headers, navigation, and main brand touchpoints
- Maintain clear space equal to the height of the icon around all sides
- Minimum size: 32px height for icon, 24px for wordmark

### Logo Variations

#### Horizontal Logo (Primary)

```
[✨] Accordant
```

- Use in headers, navigation bars, and most standard contexts
- Icon and wordmark aligned horizontally with 12px gap

#### Icon-Only Logo

```
[✨]
```

- Use when space is constrained (favicons, app icons, social avatars)
- Minimum size: 16px × 16px
- Ensure sufficient contrast against background

#### Wordmark-Only

```
Accordant
```

- Use when icon is displayed separately or in text-heavy contexts
- Maintain brand typography (Inter, Bold, 700 weight)

### Logo Clear Space

Maintain clear space around the logo equal to **1x the height of the icon** on all sides. This ensures the logo has breathing room and maintains visual impact.

```
[Clear Space = Icon Height]
    ┌─────────────┐
    │             │
    │   [✨]      │
    │  Accordant  │
    │             │
    └─────────────┘
```

### Logo Minimum Sizes

- **Full Logo**: Minimum 120px width (web), 80px width (mobile)
- **Icon Only**: Minimum 16px × 16px (favicon), 32px × 32px (standard)
- **Wordmark Only**: Minimum 14px font size

### Logo Usage Guidelines

#### ✅ Do's

- Use the primary logo in headers and navigation
- Maintain clear space around the logo
- Use appropriate logo variation for context
- Ensure sufficient contrast (WCAG AA minimum)
- Scale proportionally

#### ❌ Don'ts

- Don't stretch or distort the logo
- Don't rotate the logo
- Don't change logo colors (except for monochrome contexts)
- Don't place logo on busy backgrounds without sufficient contrast
- Don't use outdated logo versions

### App Icons & Favicons

#### Favicon

- **Format**: SVG (preferred) or PNG
- **Size**: 32px × 32px (standard), 16px × 16px (fallback)
- **Design**: Sparkles icon on brand gradient background
- **File**: `favicon.svg` or `favicon.ico`

#### App Icons (iOS/Android)

- **iOS**: 1024px × 1024px PNG
  - Rounded corners handled by iOS
  - Safe area: 20% padding from edges
- **Android**: 512px × 512px PNG
  - Full square (system handles rounding)
  - Safe area: 20% padding from edges

#### Social Media Avatars

- **Twitter/X**: 400px × 400px
- **LinkedIn**: 300px × 300px
- **GitHub**: 512px × 512px
- **Facebook**: 400px × 400px

---

## Color System

### Color Philosophy

Accordant's color palette reflects collaboration and innovation. Our primary gradient (blue to purple) represents the synthesis of different perspectives, while our accent colors provide visual interest and help differentiate elements.

### Primary Palette

#### Primary Gradient

The signature Accordant gradient represents the synthesis of multiple perspectives into a unified answer.

```css
/* Primary Gradient */
background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
```

**Color Breakdown:**

- **Start**: Blue (`#2563eb`) - Trust, reliability, intelligence
- **End**: Purple (`#7c3aed`) - Innovation, creativity, synthesis
- **Direction**: 135deg (diagonal, dynamic)

**Usage:**

- Primary CTAs and buttons
- Hero backgrounds
- Key brand elements
- Logo backgrounds (when needed)

#### Primary Color (Solid)

```css
--primary-color: #2563eb; /* Blue */
--primary-hover: #1d4ed8;  /* Darker blue for hover states */
```

**Usage:**

- Links and interactive elements
- Icons and accents
- Focus states
- Brand elements that need solid color

### Secondary Palette

#### Accent Colors

These colors represent the diversity of perspectives in the council:

```css
/* Accent Gradients */
--accent-pink-orange: linear-gradient(135deg, #ec4899 0%, #f59e0b 100%);
--accent-green-blue: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
```

**Usage:**

- Visual variety in UI elements
- Personality avatars
- Decorative elements
- Secondary CTAs

### Functional Colors

#### Success

```css
--success-color: #10b981; /* Green */
```

- Confirmation messages
- Success states
- Positive indicators
- Checkmarks and validation

#### Warning

```css
--warning-color: #f59e0b; /* Amber/Orange */
```

- Warning messages
- Caution states
- Important notices

#### Error/Danger

```css
--danger-color: #ef4444; /* Red */
--danger-hover: #dc2626;  /* Darker red */
```

- Error messages
- Destructive actions
- Critical alerts
- Validation errors

#### Info

```css
--info-color: #3b82f6; /* Blue */
```

- Informational messages
- Tooltips
- Help text
- Neutral notifications

### Neutral Palette

#### Background Colors

```css
--bg-primary: #f8f9fa;    /* Light gray - Main background */
--bg-secondary: #ffffff;  /* White - Card/surface background */
--bg-tertiary: #f1f3f5;   /* Slightly darker - Subtle backgrounds */
```

#### Text Colors

```css
--text-primary: #1f2937;   /* Dark gray - Primary text */
--text-secondary: #4b5563; /* Medium gray - Secondary text */
--text-muted: #9ca3af;     /* Light gray - Muted/disabled text */
```

#### Border Colors

```css
--border-color: #e5e7eb; /* Light gray - Borders and dividers */
```

### Color Accessibility

#### Contrast Ratios

All color combinations meet WCAG AA standards:

- **Normal Text**: Minimum 4.5:1 contrast ratio
  - `--text-primary` on `--bg-primary`: ✅ 12.6:1
  - `--text-secondary` on `--bg-secondary`: ✅ 7.2:1
  - `--primary-color` on `--bg-secondary`: ✅ 4.6:1

- **Large Text** (18px+): Minimum 3:1 contrast ratio
  - All combinations meet this standard

#### Color Blindness Considerations

- Never rely on color alone to convey information
- Use icons, labels, or patterns in addition to color
- Test with color blindness simulators
- Ensure gradients maintain contrast in grayscale

### Color Usage Guidelines

#### ✅ Do's

- Use primary gradient for key brand elements
- Maintain sufficient contrast for accessibility
- Use functional colors consistently (success = green, error = red)
- Use neutrals for backgrounds and text hierarchy
- Test color combinations for accessibility

#### ❌ Don'ts

- Don't use colors that aren't in the palette
- Don't create new gradients without brand approval
- Don't use low-contrast combinations
- Don't rely solely on color to convey meaning
- Don't use primary colors for large text blocks (use neutrals)

---

## Typography

### Font Family

#### Primary Font: Inter

```css
font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
```

**Why Inter:**

- Excellent readability at all sizes
- Modern, professional appearance
- Strong support for UI elements
- Optimized for screens

**Fallback Stack:**

1. Inter (primary)
2. system-ui (OS default)
3. Avenir (macOS fallback)
4. Helvetica (universal fallback)
5. Arial (Windows fallback)
6. sans-serif (generic fallback)

### Type Scale

#### Display (Marketing Only)

```css
font-size: clamp(2.5rem, 5vw, 4rem); /* 40px - 64px */
font-weight: 800;
line-height: 1.1;
letter-spacing: -0.02em;
```

- Hero headlines
- Landing page titles
- Large marketing messages

#### H1 - Primary Heading

```css
font-size: clamp(2rem, 4vw, 3rem); /* 32px - 48px */
font-weight: 800;
line-height: 1.1;
letter-spacing: -0.02em;
```

- Page titles
- Section headers
- Major content headings

#### H2 - Secondary Heading

```css
font-size: clamp(1.5rem, 3vw, 2rem); /* 24px - 32px */
font-weight: 700;
line-height: 1.3;
```

- Subsection headers
- Card titles
- Feature headings

#### H3 - Tertiary Heading

```css
font-size: 1.25rem; /* 20px */
font-weight: 700;
line-height: 1.4;
```

- Component titles
- List headers
- Minor section headers

#### Body - Primary Text

```css
font-size: 1rem; /* 16px */
font-weight: 400;
line-height: 1.7;
```

- Paragraphs
- Main content
- UI labels
- Default text size

#### Small - Secondary Text

```css
font-size: 0.875rem; /* 14px */
font-weight: 400;
line-height: 1.6;
```

- Captions
- Helper text
- Metadata
- Secondary information

#### Caption - Smallest Text

```css
font-size: 0.75rem; /* 12px */
font-weight: 400;
line-height: 1.5;
```

- Fine print
- Timestamps
- Small labels
- Legal text

### Font Weights

```css
--font-weight-light: 300;    /* Optional accents - rarely used */
--font-weight-regular: 400;  /* Body text, default */
--font-weight-medium: 500;   /* UI elements, emphasis */
--font-weight-bold: 700;     /* Headers, strong emphasis */
--font-weight-extrabold: 800; /* Display text, hero headlines */
```

**Usage Guidelines:**

- **300 (Light)**: Rarely used, only for special decorative text
- **400 (Regular)**: Default for body text and most content
- **500 (Medium)**: Buttons, labels, UI elements that need slight emphasis
- **700 (Bold)**: Headers, important callouts, strong emphasis
- **800 (Extrabold)**: Hero headlines, display text, maximum impact

### Typography Hierarchy

```
Display (64px, 800)    → Hero headlines
H1 (48px, 800)         → Page titles
H2 (32px, 700)         → Section headers
H3 (20px, 700)         → Subsection headers
Body (16px, 400)       → Main content
Small (14px, 400)      → Secondary text
Caption (12px, 400)    → Fine print
```

### Typography Usage Guidelines

#### ✅ Do's

- Use Inter for all UI text
- Follow the type scale consistently
- Maintain proper line-height for readability
- Use appropriate font weights for hierarchy
- Ensure sufficient contrast for text

#### ❌ Don'ts

- Don't use custom fonts without approval
- Don't mix font families
- Don't use font weights outside the scale
- Don't use display sizes for body text
- Don't use body sizes for headings

---

## Spacing System

### Base Unit

```css
--spacing-unit: 4px; /* Base unit for all spacing */
```

All spacing values are multiples of 4px to ensure visual consistency and alignment.

### Spacing Scale

```css
--spacing-0: 0;      /* 0px - No spacing */
--spacing-1: 4px;    /* 0.25rem - Tight spacing */
--spacing-2: 8px;    /* 0.5rem - Small spacing */
--spacing-3: 12px;   /* 0.75rem - Medium-small spacing */
--spacing-4: 16px;   /* 1rem - Base spacing */
--spacing-5: 20px;   /* 1.25rem - Medium spacing */
--spacing-6: 24px;   /* 1.5rem - Standard spacing */
--spacing-8: 32px;   /* 2rem - Large spacing */
--spacing-10: 40px;  /* 2.5rem - Extra large spacing */
--spacing-12: 48px;  /* 3rem - Section spacing */
--spacing-16: 64px;  /* 4rem - Major section spacing */
--spacing-20: 80px;  /* 5rem - Hero spacing */
--spacing-24: 96px;  /* 6rem - Maximum spacing */
```

### Spacing Usage

#### Component Spacing

- **Padding (internal)**: 16px - 32px for cards, 8px - 16px for buttons
- **Gap (between elements)**: 8px - 16px for related items, 24px - 32px for sections
- **Margin (external)**: 24px - 48px for sections, 16px - 24px for components

#### Layout Spacing

- **Container padding**: 24px (mobile), 32px (desktop)
- **Section padding**: 60px - 100px vertical
- **Grid gaps**: 32px for card grids, 16px for tight layouts

### Spacing Guidelines

#### ✅ Do's

- Use spacing scale values consistently
- Maintain rhythm through consistent spacing
- Use larger spacing for major sections
- Use smaller spacing for related elements
- Align to 4px grid

#### ❌ Don'ts

- Don't use arbitrary spacing values
- Don't mix spacing systems
- Don't create inconsistent gaps
- Don't use spacing that breaks alignment
- Don't ignore spacing scale

---

## Border Radius

### Radius Scale

```css
--radius-sm: 4px;   /* Small elements - badges, tags */
--radius-md: 8px;   /* Standard elements - buttons, inputs */
--radius-lg: 12px;  /* Large elements - cards, modals */
--radius-xl: 16px;  /* Extra large - feature cards */
--radius-2xl: 20px; /* Maximum - special containers */
--radius-full: 9999px; /* Pills, avatars */
```

### Radius Usage

- **Buttons**: 8px - 12px (medium to large)
- **Inputs**: 8px - 12px (medium to large)
- **Cards**: 12px - 16px (large to extra large)
- **Badges**: 4px - 8px (small to medium)
- **Avatars**: 9999px (full circle)
- **Modals**: 16px - 20px (extra large to 2xl)

---

## Shadows & Elevation

### Shadow Scale

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 
             0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 
             0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 
             0 8px 10px -6px rgb(0 0 0 / 0.1);
```

### Elevation Usage

- **Level 0 (flat)**: No shadow - backgrounds, base elements
- **Level 1 (subtle)**: `shadow-sm` - Hover states, subtle elevation
- **Level 2 (standard)**: `shadow-md` - Cards, inputs, standard UI elements
- **Level 3 (elevated)**: `shadow-lg` - Modals, dropdowns, floating elements
- **Level 4 (maximum)**: `shadow-xl` - Overlays, important modals

---

## Icons

### Icon System

Accordant uses **Lucide React** icon library for consistent, modern iconography.

**Icon Style:**

- Outline style (not filled)
- 2px stroke width
- Rounded line caps and joins
- Consistent sizing

### Icon Sizes

```css
--icon-xs: 12px;   /* Extra small - inline text icons */
--icon-sm: 16px;   /* Small - buttons, labels */
--icon-md: 20px;   /* Medium - standard UI */
--icon-lg: 24px;   /* Large - feature icons */
--icon-xl: 32px;   /* Extra large - hero icons */
--icon-2xl: 48px;  /* Maximum - major features */
```

### Icon Usage

- **Navigation**: 20px - 24px
- **Buttons**: 16px - 20px
- **Cards**: 24px - 32px
- **Hero sections**: 32px - 48px
- **Inline text**: 16px

### Icon Guidelines

#### ✅ Do's

- Use Lucide React icons consistently
- Maintain consistent sizing within contexts
- Use appropriate icon sizes for hierarchy
- Ensure icons have sufficient contrast
- Align icons with text baseline

#### ❌ Don'ts

- Don't mix icon libraries
- Don't use custom icons without approval
- Don't scale icons disproportionately
- Don't use icons that don't match the style
- Don't use icons without sufficient contrast

---

## Animation & Motion

### Animation Principles

1. **Purposeful**: Animations should serve a function, not just decoration
2. **Subtle**: Motion should enhance, not distract
3. **Fast**: Animations should be quick (200-300ms) for responsiveness
4. **Smooth**: Use easing functions for natural motion

### Standard Animations

```css
/* Transitions */
--transition-fast: 150ms ease;
--transition-base: 200ms ease;
--transition-slow: 300ms ease;

/* Easing */
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Common Animations

- **Hover states**: 200ms ease (transform, color, shadow)
- **Focus states**: 150ms ease (outline, border)
- **Page transitions**: 300ms ease-in-out
- **Loading states**: Continuous, smooth animations
- **Floating elements**: 20s ease-in-out infinite (gradient orbs)

### Animation Guidelines

#### ✅ Do's

- Use animations for feedback (hover, focus, loading)
- Keep animations fast and subtle
- Use consistent timing across the app
- Respect prefers-reduced-motion
- Animate transforms and opacity (performant)

#### ❌ Don'ts

- Don't animate without purpose
- Don't use slow or jarring animations
- Don't ignore accessibility preferences
- Don't animate layout properties (use transform)
- Don't create motion that distracts from content

---

## Responsive Design

### Breakpoints

```css
--breakpoint-sm: 640px;   /* Mobile landscape */
--breakpoint-md: 768px;   /* Tablet */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large desktop */
--breakpoint-2xl: 1536px; /* Extra large desktop */
```

### Responsive Guidelines

- **Mobile First**: Design for mobile, enhance for larger screens
- **Fluid Typography**: Use `clamp()` for responsive text sizes
- **Flexible Layouts**: Use CSS Grid and Flexbox for adaptability
- **Touch Targets**: Minimum 44px × 44px for interactive elements
- **Content Priority**: Show most important content first on mobile

---

## Next Steps

1. Review visual identity with stakeholders
2. Create logo files in all required formats (see [Asset Guidelines](./05-asset-guidelines.md))
3. Implement design tokens (see [Design Tokens](./04-design-tokens.md))
4. Build component library following these guidelines
5. Create design system documentation for developers
