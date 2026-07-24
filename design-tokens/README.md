# Obsidian Dark SaaS Theme - Design Tokens

This folder contains the design tokens for the Obsidian Dark SaaS Theme used in AstroOS.

## Files

1. `obsidian-saas-theme.json` - Structured JSON format for design tokens
2. `obsidian-saas-theme.css` - CSS custom properties file for direct use in CSS
3. `README.md` - This documentation file

## Color Palette

### Background Colors
| Token | Value | Description |
|-------|-------|-------------|
| `--obsidian-canvas` | `#0B0E14` | Main canvas background - Deep Obsidian Dark |
| `--obsidian-surface` | `#121824` | Surface/Card background - Dark Navy Slate |
| `--obsidian-surface-hover` | `#161D2C` | Surface hover state |
| `--obsidian-input` | `#121824` | Input field background |

### Border Colors
| Token | Value | Description |
|-------|-------|-------------|
| `--obsidian-border` | `#1F293D` | Subtle 1px borders |
| `--obsidian-border-hover` | `#374151` | Border hover state |
| `--obsidian-border-focus` | `rgba(99, 102, 241, 0.6)` | Border focus state (indigo with opacity) |

### Text Colors
| Token | Value | Description |
|-------|-------|-------------|
| `--obsidian-text-primary` | `#F3F4F6` | Bright crisp white for primary text |
| `--obsidian-text-secondary` | `#9CA3AF` | Muted slate for secondary text |
| `--obsidian-text-muted` | `#6B7280` | Muted text for placeholders |
| `--obsidian-text-accent` | `#6366F1` | Indigo/Purple accent text color |

### Accent Colors
| Token | Value | Description |
|-------|-------|-------------|
| `--obsidian-accent-primary` | `#6366F1` | Indigo/Purple accent color |
| `--obsidian-accent-hover` | `#4F46E5` | Darker indigo for hover states |
| `--obsidian-accent-success` | `#10B981` | Emerald green for success/active states |
| `--obsidian-accent-warning` | `#F59E0B` | Amber for warning/moderate states |
| `--obsidian-accent-deep` | `#8B5CF6` | Deep purple for special highlights |

### Status Backgrounds (40% opacity as specified)
| Token | Value | Description |
|-------|-------|-------------|
| `--obsidian-status-success-bg` | `rgba(6, 78, 59, 0.2)` | Success status background (emerald-950/40) |
| `--obsidian-status-warning-bg` | `rgba(120, 53, 15, 0.2)` | Warning status background (amber-950/40) |
| `--obsidian-status-danger-bg` | `rgba(127, 29, 29, 0.2)` | Danger status background |

### Icon Background Boxes (soft, lower opacity)
| Token | Value | Description |
|-------|-------|-------------|
| `--obsidian-icon-bg` | `rgba(139, 92, 246, 0.4)` | Icon background with lower opacity |
| `--obsidian-icon-border` | `rgba(139, 92, 246, 0.3)` | Icon border with lower opacity |
| `--obsidian-icon-text` | `#8B5CF6` | Icon text color (deep purple) |

## Typography

### Font Families
- `--font-sans`: `["Inter", "system-ui", "sans-serif"]`
- `--font-mono`: `["JetBrains Mono", "Fira Code", "monospace"]`
- `--font-display`: `["var(--font-noto-serif)", "Georgia", "serif"]`

### Font Sizes
| Token | Value | Use Case |
|-------|-------|----------|
| `--font-size-header-sm` | `20px` | Smaller headers |
| `--font-size-header-md` | `24px` | Larger headers |
| `--font-size-label-sm` | `12px` | Smaller labels |
| `--font-size-label-md` | `14px` | Larger labels |

### Font Weights
- `--font-weight-bold`: `700`
- `--font-weight-semibold`: `600`
- `--font-weight-medium`: `500`
- `--font-weight-normal`: `400`

## Borders

### Border Radius
| Token | Value | Tailwind Equivalent |
|-------|-------|---------------------|
| `--radius-container` | `0.75rem` | `rounded-xl` |
| `--radius-inner` | `0.5rem` | `rounded-lg` |

## Component Classes

### Card Component
```html
<div class="obsidian-card">
  <!-- Card content here -->
</div>
```
- Applies 1px border using `--obsidian-border`
- Background color: `--obsidian-surface`
- Border radius: `--radius-container` (0.75rem / rounded-xl)
- Hover effect: border changes to `--obsidian-border-hover`

### Icon Background Box
```html
<div class="obsidian-icon-bg">
  <i class="icon"></i>
</div>
```
- Background: `--obsidian-icon-bg` (40% opacity deep purple)
- Border: `--obsidian-icon-border` (30% opacity deep purple)
- Text color: `--obsidian-icon-text` (deep purple #8B5CF6)
- Border radius: `--radius-inner` (0.5rem / rounded-lg)

### Input Field
```html
<input class="obsidian-input" placeholder="Enter text..." />
```
- Full width
- Border radius: `--radius-inner` (0.5rem / rounded-lg)
- Border: `--obsidian-border` (default), `--obsidian-border-focus` (on focus)
- Background: `--obsidian-input`
- Text color: `--obsidian-text-primary`

### Primary Button
```html
<button class="obsidian-btn-primary">Primary Action</button>
```
- Background: `--obsidian-accent-primary`
- Hover background: `--obsidian-accent-hover`
- Text color: white
- Border radius: `--radius-inner`
- Active state: scales down to 95%

### Ghost/Secondary Button
```html
<button class="obsidian-btn-ghost">Secondary Action</button>
```
- Border: `--obsidian-border`
- Text color: `--obsidian-text-secondary`
- Hover: border changes to `--obsidian-border-hover`, text to `--obsidian-text-primary`
- No background (transparent)

### Label
```html
<label class="obsidian-label">Field Label</label>
```
- Uppercase text with tracking
- Font size: `--font-size-label-sm` (12px)
- Text color: `--obsidian-text-secondary`

### Status Badges
```html
<span class="obsidian-status-success">Success</span>
<span class="obsidian-status-warning">Warning</span>
<span class="obsidian-status-danger">Error</span>
```
- Background: respective status background with 20% opacity
- Text color: matching accent color
- Border radius: `--radius-inner`
- Font size: 12px, medium weight

## Usage in Tailwind CSS

The design tokens have also been added to the Tailwind configuration in `apps/web/tailwind.config.ts` under the `obsidian` namespace. You can use them as:

```html
<!-- Colors -->
<div class="bg-obsidian-canvas">Canvas background</div>
<div class="bg-obsidian-surface">Surface background</div>
<div class="text-obsidian-text-primary">Primary text</div>
<div class="border-obsidian-border">Border color</div>

<!-- Accent colors -->
<button class="bg-obsidian-accent text-white">Accent button</button>
<button class="bg-obsidian-accent-success">Success button</button>

<!-- Status backgrounds (with opacity) -->
<div class="bg-obsidian-status-success-bg">Success status</div>
<div class="bg-obsidian-status-warning-bg">Warning status</div>

<!-- Icon backgrounds -->
<div class="bg-obsidian-icon-bg border border-obsidian-icon-border text-obsidian-icon-text">
  Icon container
</div>
```

## Integration with Existing AstroOS Theme

These design tokens are designed to complement the existing AstroOS cosmic theme. The `cosmos` palette remains available for brand-specific elements, while the `obsidian` tokens provide a consistent dark SaaS theme for general UI components.

## Version History

- **v1.0.0** (2026-07-24): Initial implementation of Obsidian Dark SaaS Theme design tokens
