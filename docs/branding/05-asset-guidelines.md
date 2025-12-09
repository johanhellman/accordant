# Asset Guidelines & Organization

## Overview

This document outlines how to organize, name, and use Accordant brand assets. Proper asset management ensures consistency, makes assets easy to find, and maintains brand integrity across all touchpoints.

---

## Asset Organization Structure

### Recommended Directory Structure

```
/brand-assets
  /logos
    /svg
      - logo-primary.svg
      - logo-icon-only.svg
      - logo-wordmark-only.svg
    /png
      /light-bg
        - logo-primary-@1x.png
        - logo-primary-@2x.png
        - logo-primary-@3x.png
      /dark-bg
        - logo-primary-@1x.png
        - logo-primary-@2x.png
        - logo-primary-@3x.png
    /guidelines
      - logo-usage-guide.pdf
      - logo-clear-space.pdf
  /icons
    /system
      - favicon.svg
      - favicon.ico
      - apple-touch-icon.png
      - android-chrome-512x512.png
    /social
      - twitter-400x400.png
      - linkedin-300x300.png
      - github-512x512.png
      - facebook-400x400.png
  /colors
    /swatches
      - color-palette.svg
      - color-palette.png
    /gradients
      - gradient-primary.svg
      - gradient-accent-1.svg
      - gradient-accent-2.svg
  /typography
    /fonts
      - Inter-Regular.woff2
      - Inter-Medium.woff2
      - Inter-Bold.woff2
      - Inter-ExtraBold.woff2
    /specimens
      - type-scale.pdf
      - type-specimen.pdf
  /illustrations
    /characters
      - ai-personality-1.svg
      - ai-personality-2.svg
    /patterns
      - collaboration-pattern.svg
      - deliberation-pattern.svg
  /photography
    /style-guide
      - photography-guidelines.pdf
    /examples
      - hero-image-1.jpg
      - hero-image-2.jpg
  /templates
    /presentations
      - slide-template.pptx
      - slide-template.key
    /documents
      - letterhead.pdf
      - email-signature.html
  /guidelines
    - brand-guidelines.pdf
    - quick-reference.pdf
```

---

## Logo Assets

### Logo Formats

#### SVG (Preferred)

- **Use for**: Web, scalable graphics, print (high quality)
- **Files**: `logo-primary.svg`, `logo-icon-only.svg`, `logo-wordmark-only.svg`
- **Advantages**: Scalable, small file size, crisp at any size

#### PNG (Raster)

- **Use for**: Email, social media, contexts where SVG isn't supported
- **Resolutions**: @1x, @2x, @3x for different display densities
- **Backgrounds**: Separate versions for light and dark backgrounds

#### PDF (Print)

- **Use for**: Print materials, documents, presentations
- **Advantages**: Vector-based, print-ready, maintains quality

### Logo Variations

#### Primary Logo (Horizontal)

- **File**: `logo-primary.svg`
- **Layout**: Icon + Wordmark horizontal
- **Usage**: Headers, navigation, main brand touchpoints
- **Minimum size**: 120px width (web), 80px width (mobile)

#### Icon Only

- **File**: `logo-icon-only.svg`
- **Layout**: Sparkles icon only
- **Usage**: Favicons, app icons, social avatars, constrained spaces
- **Minimum size**: 16px × 16px

#### Wordmark Only

- **File**: `logo-wordmark-only.svg`
- **Layout**: "Accordant" text only
- **Usage**: Text-heavy contexts, when icon is separate
- **Minimum size**: 14px font size

### Logo File Naming Convention

```
logo-{variation}-{background}-{resolution}.{format}

Examples:
- logo-primary-light-bg-@2x.png
- logo-icon-only-dark-bg.svg
- logo-wordmark-only-light-bg.pdf
```

---

## Icon Assets

### System Icons

#### Favicon

- **File**: `favicon.svg` (preferred) or `favicon.ico`
- **Size**: 32px × 32px (standard), 16px × 16px (fallback)
- **Design**: Sparkles icon on brand gradient background
- **Location**: `/brand-assets/icons/system/favicon.svg`

#### Apple Touch Icon

- **File**: `apple-touch-icon.png`
- **Size**: 180px × 180px
- **Design**: Sparkles icon, square with rounded corners (iOS handles rounding)
- **Location**: `/brand-assets/icons/system/apple-touch-icon.png`

#### Android Chrome Icon

- **File**: `android-chrome-512x512.png`
- **Size**: 512px × 512px
- **Design**: Sparkles icon, full square (Android handles rounding)
- **Location**: `/brand-assets/icons/system/android-chrome-512x512.png`

### Social Media Icons

#### Twitter/X

- **File**: `twitter-400x400.png`
- **Size**: 400px × 400px
- **Format**: PNG
- **Design**: Sparkles icon on brand gradient background

#### LinkedIn

- **File**: `linkedin-300x300.png`
- **Size**: 300px × 300px
- **Format**: PNG
- **Design**: Sparkles icon on brand gradient background

#### GitHub

- **File**: `github-512x512.png`
- **Size**: 512px × 512px
- **Format**: PNG
- **Design**: Sparkles icon on brand gradient background

#### Facebook

- **File**: `facebook-400x400.png`
- **Size**: 400px × 400px
- **Format**: PNG
- **Design**: Sparkles icon on brand gradient background

---

## Color Assets

### Color Swatches

#### Digital Swatches

- **File**: `color-palette.svg` (vector) or `color-palette.png` (raster)
- **Contents**: All brand colors with hex codes, RGB values, and usage notes
- **Formats**: SVG (preferred), PNG (fallback)
- **Location**: `/brand-assets/colors/swatches/`

#### Print Swatches

- **File**: `color-palette-print.pdf`
- **Contents**: CMYK values for print production
- **Usage**: Print materials, physical brand applications

### Gradient Assets

#### Primary Gradient

- **File**: `gradient-primary.svg`
- **Design**: Blue to purple gradient (135deg)
- **Usage**: Backgrounds, CTAs, key brand elements

#### Accent Gradients

- **Files**: `gradient-accent-1.svg`, `gradient-accent-2.svg`
- **Design**: Pink-orange and green-blue gradients
- **Usage**: Visual variety, personality avatars, decorative elements

---

## Typography Assets

### Font Files

#### Web Fonts (WOFF2)

- **Files**:
  - `Inter-Regular.woff2`
  - `Inter-Medium.woff2`
  - `Inter-Bold.woff2`
  - `Inter-ExtraBold.woff2`
- **Format**: WOFF2 (preferred for web)
- **Location**: `/brand-assets/typography/fonts/`

#### Desktop Fonts

- **Files**: TTF or OTF versions for design tools
- **Usage**: Figma, Sketch, Adobe Creative Suite
- **Location**: `/brand-assets/typography/fonts/desktop/`

### Type Specimens

#### Type Scale Document

- **File**: `type-scale.pdf`
- **Contents**: All type sizes, weights, and line heights
- **Usage**: Reference for designers and developers

#### Type Specimen

- **File**: `type-specimen.pdf`
- **Contents**: Full character set, examples, usage guidelines
- **Usage**: Design reference, font showcase

---

## Illustration Assets

### Character Illustrations

- **Purpose**: Represent AI personalities visually
- **Style**: Modern, clean, approachable
- **Format**: SVG (preferred) or PNG
- **Location**: `/brand-assets/illustrations/characters/`

### Pattern Illustrations

- **Purpose**: Decorative elements, backgrounds
- **Style**: Abstract, geometric, representing collaboration
- **Format**: SVG (preferred)
- **Location**: `/brand-assets/illustrations/patterns/`

---

## Photography Assets

### Photography Style Guide

- **File**: `photography-guidelines.pdf`
- **Contents**:
  - Style principles
  - Composition guidelines
  - Color treatment
  - Subject matter
  - Usage examples

### Example Images

- **Purpose**: Reference for approved photography style
- **Formats**: JPG (web), RAW (source files)
- **Location**: `/brand-assets/photography/examples/`

### Photography Guidelines

#### Style Principles

- **Light**: Bright, natural lighting
- **Composition**: Clean, uncluttered, focused
- **Color**: Align with brand palette
- **Mood**: Professional, approachable, innovative

#### Subject Matter

- Collaboration and teamwork
- Technology and AI
- Diverse perspectives
- Professional environments
- Innovation and creativity

---

## Template Assets

### Presentation Templates

#### PowerPoint Template

- **File**: `slide-template.pptx`
- **Contents**:
  - Master slides with brand colors and fonts
  - Logo placement
  - Typography styles
  - Color swatches

#### Keynote Template

- **File**: `slide-template.key`
- **Contents**: Same as PowerPoint template

### Document Templates

#### Letterhead

- **File**: `letterhead.pdf`
- **Contents**: Branded letterhead with logo and contact info
- **Usage**: Official correspondence

#### Email Signature

- **File**: `email-signature.html`
- **Contents**: HTML email signature template
- **Usage**: Team email signatures

---

## Asset Naming Conventions

### General Naming Pattern

```
{category}-{name}-{variant}-{size}-{format}

Examples:
- logo-primary-light-bg-@2x.png
- icon-sparkles-32px.svg
- gradient-primary-1920x1080.svg
- photo-hero-collaboration-@2x.jpg
```

### Category Prefixes

- `logo-` - Logo files
- `icon-` - Icon files
- `gradient-` - Gradient assets
- `photo-` - Photography
- `illustration-` - Illustrations
- `template-` - Templates

### Size Suffixes

- `@1x` - Standard resolution
- `@2x` - Retina/high-DPI (2×)
- `@3x` - Ultra-high-DPI (3×)
- `-{width}x{height}` - Specific dimensions (e.g., `-512x512`)

---

## Asset Usage Guidelines

### Logo Usage

#### ✅ Approved Uses

- Product interfaces and applications
- Marketing materials
- Documentation
- Presentations
- Email signatures
- Social media profiles

#### ❌ Prohibited Uses

- Modifying logo colors (except approved variations)
- Stretching or distorting the logo
- Placing logo on low-contrast backgrounds
- Using outdated logo versions
- Creating derivative logos

### Color Usage

#### ✅ Approved Uses

- UI elements and interfaces
- Marketing materials
- Presentations
- Documentation
- Branded communications

#### ❌ Prohibited Uses

- Creating new color combinations without approval
- Using colors outside the brand palette
- Modifying color values
- Using low-contrast combinations

### Typography Usage

#### ✅ Approved Uses

- All brand communications
- Product interfaces
- Marketing materials
- Documentation

#### ❌ Prohibited Uses

- Using fonts outside the brand system
- Modifying font weights or styles
- Creating custom typography treatments
- Mixing font families

---

## Asset Delivery Formats

### For Web

- **Logos**: SVG (preferred), PNG @1x/@2x/@3x
- **Icons**: SVG (preferred), PNG @1x/@2x/@3x
- **Images**: JPG (photos), PNG (graphics), WebP (optimized)
- **Fonts**: WOFF2

### For Print

- **Logos**: PDF, SVG, EPS
- **Images**: High-resolution TIFF or PNG (300 DPI minimum)
- **Fonts**: TTF or OTF
- **Colors**: CMYK color profiles

### For Design Tools

- **Logos**: SVG, PDF
- **Icons**: SVG
- **Fonts**: TTF or OTF
- **Colors**: Design token files (JSON, CSS)

---

## Asset Version Control

### Versioning System

```
{filename}-v{major}.{minor}.{patch}.{format}

Examples:
- logo-primary-v1.0.0.svg
- logo-primary-v1.1.0.svg (minor update)
- logo-primary-v2.0.0.svg (major update)
```

### Change Log

Maintain a changelog for asset updates:

```markdown
## Asset Changelog

### v1.1.0 - 2025-01-15
- Updated logo with refined spacing
- Added dark background variations
- New social media icon sizes

### v1.0.0 - 2025-01-01
- Initial asset release
- Primary logo variations
- Color palette established
```

---

## Asset Access & Distribution

### Internal Access

- **Location**: Shared drive or version control
- **Permissions**: Read-only for most, edit for brand team
- **Backup**: Regular backups of all assets

### External Distribution

- **Client Delivery**: Branded zip file with guidelines
- **Partner Delivery**: Specific assets with usage terms
- **Public Assets**: Available on brand website

### Asset Request Process

1. **Request**: Submit asset request with use case
2. **Review**: Brand team reviews request
3. **Approval**: Approved requests get asset package
4. **Delivery**: Assets delivered with usage guidelines
5. **Follow-up**: Check usage compliance

---

## Asset Quality Standards

### Logo Quality

- **Vector**: SVG or PDF for scalability
- **Raster**: Minimum 300 DPI for print, appropriate @2x/@3x for web
- **Clean**: No artifacts, crisp edges, proper alignment

### Image Quality

- **Resolution**: Appropriate for use case (web vs. print)
- **Compression**: Optimized file sizes without quality loss
- **Color**: Accurate color representation, proper color profiles

### File Organization

- **Naming**: Consistent naming conventions
- **Structure**: Logical folder organization
- **Metadata**: Proper file metadata and tags

---

## Asset Maintenance

### Regular Reviews

- **Quarterly**: Review asset library for outdated files
- **Annually**: Comprehensive asset audit
- **As Needed**: Update assets when brand evolves

### Deprecation Process

1. **Notice**: Announce deprecated assets
2. **Timeline**: Provide migration timeline
3. **Replacement**: Provide new asset versions
4. **Archive**: Move deprecated assets to archive folder

---

## Quick Reference

### Most Common Assets

**Logos:**

- `logo-primary.svg` - Main logo
- `logo-icon-only.svg` - Icon only
- `favicon.svg` - Favicon

**Colors:**

- `color-palette.svg` - Color reference
- `gradient-primary.svg` - Primary gradient

**Icons:**

- `favicon.svg` - Website favicon
- `apple-touch-icon.png` - iOS icon
- `android-chrome-512x512.png` - Android icon

**Fonts:**

- `Inter-Regular.woff2` - Regular weight
- `Inter-Bold.woff2` - Bold weight

---

## Next Steps

1. Create actual logo files in all required formats
2. Generate color swatch files
3. Prepare font files for distribution
4. Create icon assets for all platforms
5. Build asset library structure
6. Set up asset version control
7. Create asset request process
8. Document asset delivery workflows
