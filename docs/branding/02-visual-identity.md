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

### The Warm Intelligence Palette

Accordant's redesigned color palette emphasizes **warm, collaborative intelligence**. Moving away from conventional corporate blues, we've adopted a distinctive violet-pink-orange combination that communicates sophistication, warmth, and innovation.

**Design Philosophy:**
- **Distinctiveness**: Stand out from generic SaaS aesthetics
- **Warmth**: Create an inviting, collaborative atmosphere
- **Sophistication**: Convey intelligence and professionalism
- **Collaboration**: Visual representation of multiple perspectives

### Primary Palette

#### Primary Gradient - The Signature

The signature Accordant gradient represents the synthesis of intelligence (violet) and collaboration (pink).

```css
/* Primary Gradient - Violet to Pink */
background: linear-gradient(135deg, #8b5cf6 0%, #f472b6 100%);
```

**Color Breakdown:**

- **Start**: Vibrant Violet (`#8b5cf6`) - Intelligence, sophistication, innovation
- **End**: Warm Pink (`#f472b6`) - Collaboration, warmth, synthesis
- **Direction**: 135deg (diagonal, dynamic)

**Usage:**

- Primary CTAs and buttons
- Hero backgrounds
- Key brand elements
- Signature design moments

#### Primary Color (Solid)

```css
--color-primary: #8b5cf6;       /* Vibrant Violet */
--color-primary-hover: #7c3aed;  /* Deep Violet */
--color-primary-light: #a78bfa;  /* Light Violet */
```

**Usage:**

- Links and interactive elements
- Icons and accents
- Focus states
- Information states

### Secondary Colors

#### Warm Pink (Secondary Brand Color)

```css
--color-secondary: #f472b6;       /* Warm Pink */
--color-secondary-hover: #ec4899;  /* Hot Pink */
--color-secondary-light: #f9a8d4;  /* Light Pink */
```

**Usage:**

- Secondary CTAs
- Accent elements
- Gradient combinations
- Collaborative features

#### Warm Orange (Tertiary Accent)

```css
--color-accent: #fb923c;       /* Warm Orange */
--color-accent-hover: #f97316;  /* Bright Orange */
```

**Usage:**

- Tertiary accents
- Gradient endings
- Energy indicators
- Warning states

### Gradient System

#### Primary Gradient
```css
linear-gradient(135deg, #8b5cf6 0%, #f472b6 100%)
```
Use for: Primary CTAs, hero sections, signature moments

#### Subtle Gradient
```css
linear-gradient(135deg, #faf5ff 0%, #fdf2f8 100%)
```
Use for: Background accents, hover states, subtle emphasis

#### Accent Gradient 1 (Pink to Orange)
```css
linear-gradient(135deg, #f472b6 0%, #fb923c 100%)
```
Use for: Secondary CTAs, decorative elements

#### Accent Gradient 2 (Green to Violet)
```css
linear-gradient(135deg, #10b981 0%, #8b5cf6 100%)
```
Use for: Success states with brand color, positive features

#### Text Gradient
```css
linear-gradient(135deg, #8b5cf6 0%, #f472b6 50%, #fb923c 100%)
```
Use for: Hero headlines, special text treatments

### Functional Colors

#### Success
```css
--color-success: #10b981; /* Emerald Green */
```
Use for: Confirmations, success states, positive indicators

#### Warning
```css
--color-warning: #f59e0b; /* Amber/Orange */
```
Use for: Warnings, caution states, important notices

#### Error
```css
--color-error: #ef4444; /* Red */
--color-error-hover: #dc2626;
```
Use for: Errors, destructive actions, critical alerts

#### Info
```css
--color-info: #8b5cf6; /* Vibrant Violet (matches primary) */
```
Use for: Informational messages, tooltips, help text

### Neutral Palette - Warmer Tones

Unlike conventional cool grays, Accordant uses **warmer stone-based neutrals** for a more inviting feel.

#### Background Colors
```css
--color-bg-primary: #fafaf9;    /* Warm stone-50 */
--color-bg-secondary: #ffffff;  /* White */
--color-bg-tertiary: #f5f5f4;   /* Warm stone-100 */
```

#### Text Colors
```css
--color-text-primary: #292524;   /* Warm stone-800 */
--color-text-secondary: #78716c; /* Warm stone-500 */
--color-text-muted: #a8a29e;     /* Warm stone-400 */
```

#### Border Colors
```css
--color-border: #e7e5e4; /* Warm stone-200 */
```

### Color Accessibility

All color combinations meet WCAG AA standards for accessibility.

#### Contrast Ratios

- **Normal Text** (Minimum 4.5:1):
  - Violet on white: ✅ 5.2:1
  - Stone-800 text on stone-50 background: ✅ 12.1:1
  - Stone-500 text on white: ✅ 4.7:1

- **Large Text** (Minimum 3:1):
  - All combinations exceed this standard

#### Color Blindness Considerations

- Icons and labels supplement color coding
- Gradients maintain contrast in grayscale
- Functional colors remain distinguishable
- Never rely on color alone for information

### Color Usage Guidelines

#### ✅ Do's

- Use primary gradient for signature brand moments
- Apply subtle gradient backgrounds for hover states
- Use warmer neutrals for all backgrounds and text
- Maintain violet as the primary interactive color
- Test all color combinations for accessibility

#### ❌ Don'ts

- Don't use old blue/purple palette colors
- Don't create new gradients without approval
- Don't use cool grays (use warm stone neutrals)
- Don't rely solely on color to convey meaning
- Don't use low-contrast combinations

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

## Border Radius - Organic System

### Organic, Varied Radii

Accordant uses an **organic border radius system** that creates visual interest through variation. Instead of uniform 12px corners everywhere, we use semantically named radii that vary by component type.

**Design Philosophy:**
- **Variety Creates Interest**: Different radii for different contexts
- **Organic Feel**: Larger radii feel softer and more approachable
- **Sophistication**: Intentional variation shows design thoughtfulness

### Radius Scale

```css
/* Semantic Radii - Primary System */
--radius-subtle: 6px;    /* Small UI elements - badges, small buttons */
--radius-soft: 16px;     /* Standard containers - cards, message boxes */
--radius-organic: 24px;  /* Large features - stage containers, modals */
--radius-pill: 100px;    /* Pills, tags, fully rounded */

/* Legacy Support */
--radius-sm: 6px;
--radius-md: 8px;
--radius-lg: 16px;
--radius-xl: 24px;
--radius-2xl: 32px;
--radius-full: 9999px;
```

### Radius Usage Guidelines

- **Small Interactive Elements** (`subtle` - 6px):
  - Small buttons
  - Input fields
  - Badges
  - Navigation items

- **Standard Containers** (`soft` - 16px):
  - Message cards
  - Chat bubbles
  - Standard cards
  - Tabs
  - Buttons

- **Large Feature Elements** (`organic` - 24px):
  - Stage containers (Stage 1, 2, 3)
  - Large feature cards
  - Modals and dialogs
  - Hero sections with cards

- **Pills & Rounded** (`pill` - 100px):
  - Pills and tags
  - Rounded badges
  - Avatars (use with `full` for perfect circles)

### Why Different Radii?

**Visual Hierarchy**: Larger radii on important elements draw attention
**Context Differentiation**: Different radii help distinguish component types
**Less Generic**: Varied radii create a more distinctive, less templated feel
**Organic Feel**: Softer corners feel more inviting and collaborative

---

## Shadows & Elevation - Softer Approach

### Softer, More Sophisticated Shadows

Accordant uses **softer, more sophisticated shadows** that create depth without harshness. The shadow system emphasizes subtlety and refinement.

**Design Philosophy:**
- **Subtle Over Dramatic**: Gentle shadows create sophistication
- **Refined Depth**: Depth without heavy drop shadows
- **Context-Appropriate**: Different shadows for different elevations
- **Glow for Accent**: Special glow shadow for focus and active states

### Shadow Scale

```css
/* Semantic Shadows - Primary System */
--shadow-soft: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
--shadow-medium: 0 4px 12px rgba(0, 0, 0, 0.08);
--shadow-large: 0 12px 32px rgba(0, 0, 0, 0.12);
--shadow-glow: 0 0 0 3px rgba(139, 92, 246, 0.1);  /* Violet glow */

/* Legacy Support */
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
--shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.12);
--shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.15);
```

### Shadow Usage Guidelines

- **Soft** (Level 1):
  - Message cards
  - Standard containers
  - Subtle elevation
  - Resting state cards
  - Use: Cards that need gentle separation

- **Medium** (Level 2):
  - Buttons (especially CTAs)
  - Dropdowns
  - Hover states
  - Moderate elevation
  - Use: Interactive elements that need emphasis

- **Large** (Level 3):
  - Modals
  - Popovers
  - Overlays
  - High elevation
  - Use: Elements that float above the page

- **Glow** (Special):
  - Focus states (inputs, buttons)
  - Active states
  - Highlighted elements
  - Selected items
  - Use: Violet-tinted glow for brand-aligned emphasis

### Why Softer Shadows?

**Sophistication**: Subtle shadows feel more refined and premium
**Less Harsh**: Softer shadows are easier on the eyes
**Modern**: Follows contemporary design trends toward subtlety
**Brand Alignment**: Gentle shadows match the warm, collaborative feel

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
