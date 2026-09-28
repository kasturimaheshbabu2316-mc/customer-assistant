---
name: Tactile Clay AI
colors:
  surface: '#fbf9f4'
  surface-dim: '#dcdad5'
  surface-bright: '#fbf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3ee'
  surface-container: '#f0eee9'
  surface-container-high: '#eae8e3'
  surface-container-highest: '#e4e2dd'
  on-surface: '#1b1c19'
  on-surface-variant: '#464554'
  inverse-surface: '#30312d'
  inverse-on-surface: '#f3f1eb'
  outline: '#767586'
  outline-variant: '#c7c4d7'
  surface-tint: '#494bd6'
  primary: '#4648d4'
  on-primary: '#ffffff'
  primary-container: '#6063ee'
  on-primary-container: '#fffbff'
  inverse-primary: '#c0c1ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#b90538'
  on-tertiary: '#ffffff'
  tertiary-container: '#dc2c4f'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdadb'
  tertiary-fixed-dim: '#ffb2b7'
  on-tertiary-fixed: '#40000d'
  on-tertiary-fixed-variant: '#92002a'
  background: '#fbf9f4'
  on-background: '#1b1c19'
  surface-variant: '#e4e2dd'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.375rem
  space-sm: 0.75rem
  space-md: 1.25rem
  space-lg: 2rem
  space-xl: 3rem
---

## Brand & Style

This design system expresses a friendly, tangible, and deeply approachable vision for AI-driven customer support. By steering clear of cold, clinical corporate SaaS aesthetics and hyper-minimalist flat layers, the interface adopts a warm **Claymorphism** visual philosophy. The system treats interface elements as volumetric, soft-touch matte physical objects—reminiscent of sculpted clay, soft silicone, and tactile designer toys.

### Emotional Resonance & User Experience
Customer support environments often trigger anxiety, friction, and impatience. This visual identity actively counterbalances stress through friendly, pillowy surfaces, soft rounded geometry, and tangible physics. The UI feels responsive, organic, and friendly, reinforcing the reassuring presence of an AI co-pilot that is eager to assist rather than imposing complex technical overhead.

### Key Visual Tenets
- **Volumetric 3D Form:** Surfaces are defined by soft inflation rather than flat fills or sharp borders. Every component displays subtle curvature.
- **Dual Lighting (Inner Chamfers):** Light hits elements from the top-left to cast an inner white highlight, while an opposing soft inner shadow creates depth and thickness on the bottom-right.
- **Diffused Ambient Grounding:** External shadows are broad, deeply feathered, and colored by ambient hues—never pure black or sharp.
- **Tactile Squish & Press:** Active and interactive states simulate physical compression, depressing the shape inward as if made of malleable rubber or modeling clay.

## Colors

The palette balances a warm, grounded clay base with vibrant, cheerful accents that guide user attention across support tickets, AI suggestions, and resolution states.

### Color Roles & Application
- **Base Canvas (`#F1EFEA`):** A warm, soft-clay porcelain tone that prevents the sterile chill of stark white and gives dual inner shadows their visible contrast.
- **Primary Indigo (`#6366F1`):** Applied to primary actions, interactive chat triggers, and key AI response nodes. In claymorphic treatments, it is shaded with a top-left highlight of `#818CF8` and an underside tint of `#4338CA`.
- **Secondary Mint (`#10B981`):** Represents resolution, positive customer feedback, active agent states, and successful automations. Chamfers use `#34D399` on top-left and `#059669` on the bottom-right.
- **Tertiary Soft Coral (`#F43F5E`):** Reserved for urgent tickets, SLA breaches, destructive actions, and alerts. Pairs with soft highlights to prevent aggression while maintaining urgency.
- **Sky Blue Accent (`#0EA5E9`):** Dedicated to secondary metadata, customer transcript chips, and ongoing live typing/processing indicators.
- **Surface Elevation Neutral (`#FFFFFF`):** Sits on top of the base neutral canvas to create extruded, pillowy floating containers.
- **Text & Foreground Neutral (`#1E1B4B` / `#475569`):** Deep indigo-tinted slate for high legibility without resorting to harsh true black.

## Typography

The typographic hierarchy relies entirely on **Plus Jakarta Sans**, chosen for its friendly geometric curves, wide aperatures, and organic rounded qualities that directly complement the claymorphic aesthetic.

### Stylistic Execution
- **Weight Pairing:** Headings use bold and extra-bold weights (`700` and `800`) to anchor voluminous, inflated cards. Body copy shifts down to regular (`400`) and semi-bold (`600`) to ensure legible reading of dense customer support logs.
- **Letter Spacing:** Headlines pull negative tracking (`-0.02em` to `-0.03em`) to balance the plush visual weight of containers. Labels and pill badges carry slightly opened tracking (`0.01em` to `0.04em`) to ensure quick glanceability during high-volume support triage.
- **Color Contrast:** Headers are set in deep indigo slate (`#1E1B4B`), and body text uses `#475569` to prevent stark black text from disrupting the soft clay illusion.

## Layout & Spacing

Because claymorphic elements occupy visual volume through dual shadows and broad rounded corners, layouts require generous breathing room to avoid visual crowding.

### Layout Philosophy
- **Desk & Dashboard Canvas:** Employs a 12-column responsive fluid grid with wide `1.5rem` (`24px`) gutters on desktop, scaling to a 4-column layout with `1rem` (`16px`) gutters on mobile devices.
- **Breathing Island Structure:** Cards and interaction panels sit as separated, buoyant physical "pads" rather than interlocking full-bleed tiles. Outer container margins default to `2rem` (`32px`) to leave room for soft ambient drop shadows.
- **Padding Generosity:** Internal component padding is deliberately increased (`space-md` for standard cards, `space-lg` for modal pads) so that inflated inner chamfers never clip against or crowd textual content.

## Elevation & Depth

Depth in this system is achieved without hard borders or flat dividers. Instead, elevation relies on multi-source light simulation combining inner highlights, inner shadows, and soft ambient drop shadows.

### The Clay Lighting Rig
All components are rendered as if lit from an angle of 315° (top-left light source):
1. **Top-Left Inner Highlight:** White (`rgba(255, 255, 255, 0.7)`) inset shadow running across top and left borders, simulating a bevel where light catches the curve.
2. **Bottom-Right Inner Shade:** Toned dark tint (`rgba(71, 85, 105, 0.12)` or a darker shade of the element’s own fill) inset shadow on the bottom and right edges, delivering physical mass.
3. **Ambient Drop Shadow:** Multi-layered, diffused, non-directional blur (`0 14px 28px -6px rgba(100, 116, 139, 0.16), 0 6px 12px -3px rgba(100, 116, 139, 0.1)`) extending outward to ground the element over the warm canvas.

### Elevation Hierarchy
- **Level 0 (Base Canvas):** `#F1EFEA` flat, soft clay foundation.
- **Level 1 (Panels & Cards):** Raised surface (`#FFFFFF`), `16px` to `24px` drop blur, subtle dual inner shadows (`inset 2px 2px 4px rgba(255,255,255,0.8)`, `inset -3px -3px 6px rgba(148, 163, 184, 0.2)`).
- **Level 2 (Buttons, Pills, Floating Tools):** Highly extruded elements with pronounced tactile relief (`inset 3px 3px 5px rgba(255,255,255,0.6)`, `inset -4px -4px 8px rgba(0,0,0,0.14)`).
- **Level 3 (Pressed / Inset State):** Reversal of shadows (`inset 4px 4px 8px rgba(0,0,0,0.16)`, `inset -2px -2px 4px rgba(255,255,255,0.5)`), visually flattening the object into the canvas as if physically indented.

## Shapes

The shape system strictly uses high-radius pillowy contours. Sharp vertices contradict the physical metaphor of molded clay and are avoided across all UI primitives.

### Radius Architecture
- **Pill Primitives (`rounded-full`):** Used on buttons, active badges, status chips, avatar framing, search pills, and floating action prompts.
- **Large Container Pads (`rounded-xl` / `24px` to `32px`):** Used for workspace panels, chat message clusters, AI insight widgets, and modals.
- **Input Channels (`rounded-lg` / `16px` to `20px`):** Input containers maintain curved, ergonomic bounds to match surrounding buttons.
- **Micro Radii:** No interactive element carries a corner radius smaller than `12px`.

## Components

### Buttons
- **Primary Action (Indigo Clay):** Extruded solid `#6366F1` pill shape. Inset highlight: `2px 2px 3px rgba(255, 255, 255, 0.45)`. Inset shade: `-3px -3px 5px rgba(49, 46, 129, 0.45)`. Outer shadow: `0 10px 20px -4px rgba(99, 102, 241, 0.4)`. Text is pure white bold.
- **Secondary Action (Porcelain Clay):** Extruded `#FFFFFF` pill shape. Inset highlight: `2px 2px 3px rgba(255, 255, 255, 0.9)`. Inset shade: `-3px -3px 5px rgba(203, 213, 225, 0.6)`. Text is `#1E1B4B`.
- **Interaction Physics:** On `:hover`, translateY shifts up `-2px`, and ambient drop shadow spreads. On `:active`, translateY shifts `+2px`, inner shadows flip to debossed values, and external drop shadow shrinks to zero, giving a tactile squish effect.

### Chips & Status Badges
- **Form:** Pill-shaped, compact containers.
- **States:** 
  - *Resolved (Mint):* `#D1FAE5` surface with `#059669` text, soft mint inset highlight.
  - *SLA Warning (Coral):* `#FFE4E6` surface with `#E11D48` text.
  - *AI Automated (Sky):* `#E0F2FE` surface with `#0284C7` text.
- **Lighting:** Ultra-soft inner highlight (`inset 1px 1px 2px rgba(255,255,255,0.8)`) making each badge resemble a smooth enameled bead.

### Cards & Ticket Modules
- **Container Structure:** Rendered in `#FFFFFF` with `28px` corner radius.
- **Card Depth:** Exterior glow using `box-shadow: 0 16px 32px -8px rgba(148, 163, 184, 0.25)`. Interior edge softness using `inset 2px 2px 4px #FFFFFF` and `inset -3px -3px 6px rgba(226, 232, 240, 0.6)`.
- **Dividers:** Strictly prohibited. Distinct sections within cards are separated using recessed "sunken clay" wells (`#F8FAFC` with inset shadow) rather than divider strokes.

### Input Fields & Search Bars
- **Well Construction:** Textured as debossed depressions carved directly into the surface.
- **Resting State:** `#F1EFEA` background, `inset 2px 2px 5px rgba(0, 0, 0, 0.08)`, `inset -2px -2px 4px rgba(255, 255, 255, 0.8)`. Corner radius `20px`.
- **Focus State:** Transitions to `#FFFFFF` fill with an indigo glow ring (`0 0 0 4px rgba(99, 102, 241, 0.2)`) and light top-left chamfer.

### Checkboxes & Radio Controls
- **Checkboxes:** Rounded squares (`8px` radius) with debossed inner shadows when unchecked. When checked, inflates with `#6366F1` clay fill and a white extruded checkmark glyph.
- **Radios:** Round pills that feature an extruded spherical inner bead when selected, creating the appearance of a ball nested in a soft dimple.

### Lists & Activity Feeds
- **Feed Row:** Rows hover into elevated clay pads rather than highlighting with flat tint lines.
- **Timeline Nodes:** Represented as 3D spherical clay beads interconnected by soft, thick vertical rails (`4px` width, rounded cap terminals, `#E2E8F0`).

### AI Assistant Specific Components
- **AI Suggestion Bubble:** Rendered in an iridescent soft indigo-tinted clay (`#EEF2FF`) with playful inflated edges. Includes an animated tactile "shimmer" along the top-left highlight while the AI generates responses.
- **Confidence Meter:** A thick, rounded track (`12px` height) with a sunken well appearance, containing an inflated pill-shaped progress bar in vibrant mint or sky blue.