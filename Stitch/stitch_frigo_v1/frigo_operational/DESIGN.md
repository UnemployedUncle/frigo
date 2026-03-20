# Operational Elegance: A Design System Document

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Kinetic Manuscript."** 

This system rejects the cluttered, image-heavy "lifestyle" tropes of cooking apps in favor of high-performance utility. It treats the interface as a living, breathing document. By prioritizing a text-first aesthetic, we create a high-speed operational environment for the kitchen—where clarity is safety and whitespace is room to breathe.

To move beyond the "generic template" look, this system utilizes **Intentional Asymmetry** and **Tonal Depth**. By avoiding rigid grid-lines and boxy containers, we create a layout that feels curated and editorial. Elements should feel "placed" rather than "poured" into a template, using dramatic shifts in typographic scale to guide the eye through the cooking process.

---

## 2. Colors & Surface Philosophy
The palette is "Operational"—every color serves a functional purpose. We move away from decorative color, using it only to signal action, state, or hierarchy.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or layout containment. Boundaries must be defined solely through background color shifts. For example, a `surface-container-low` section sitting on a `surface` background creates a clear, sophisticated boundary without the visual "noise" of a stroke.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers, like stacked sheets of fine vellum. 
- **Base Layer:** `surface` (#f8fafb)
- **Secondary Logic:** `surface-container-low` (#f2f4f5)
- **Interactive Layers:** `surface-container-highest` (#e1e3e4)
- **The "Glass & Gradient" Rule:** For floating action panels or mobile overlays, use `surface-container-lowest` (#ffffff) at 85% opacity with a `20px` backdrop-blur. 

### Signature Textures
Main CTAs should use a subtle linear gradient from `primary` (#a14000) to `primary_container` (#f26d21) at a 135-degree angle. This adds a "jewel-like" depth that distinguishes operational actions from static information.

---

## 3. Typography: The Kinetic Manuscript
Typography is the primary UI element. We use **Inter** to achieve a technical, highly-readable feel.

- **Display (Display-LG/MD):** Used for recipe titles or "Current Step" numbers. Use `display-md` (2.75rem) with `-0.02em` letter spacing to create a commanding presence.
- **The "Active Step" Headline:** Use `headline-lg` (2rem) for instructions. The contrast between this and `body-md` (0.875rem) ingredient lists creates an immediate visual anchor.
- **Labels (Label-MD/SM):** Use for technical data (e.g., "PREP TIME," "TEMP"). These should always be uppercase with `0.05em` letter spacing to feel like an industrial readout.

---

## 4. Elevation & Depth
We eschew traditional drop-shadows for **Tonal Layering**.

- **The Layering Principle:** To lift a card, place a `surface-container-lowest` card on a `surface-container` background. This creates a "soft lift" that feels lightweight and modern.
- **Ambient Shadows:** Only used for floating modals or global navigation. Use a blur of `40px`, a spread of `-10px`, and an opacity of 6% using the `on_surface` color.
- **The "Ghost Border" Fallback:** If a border is required for accessibility in input fields, use `outline_variant` (#e0c0b2) at **20% opacity**. Never use 100% opaque borders.

---

## 5. Components

### Buttons
- **Primary:** Gradient fill (`primary` to `primary_container`), `on_primary` text, `DEFAULT` (0.5rem/8px) corners.
- **Secondary:** `secondary_fixed` background with `on_secondary_fixed_variant` text. High-contrast but lower priority than the main action.
- **Tertiary/Ghost:** No container. Use `title-sm` typography with an icon, utilizing `primary` color for the label.

### Cards & Lists
**Forbid the use of divider lines.**
- Separate recipe steps or ingredients using the **Spacing Scale**. Use `spacing-5` (1.7rem) between items.
- For grouped content, use a background shift to `surface_container_low`. 

### Input Fields
- Avoid boxes. Use a "bottom-line-only" approach or a very subtle `surface_container_high` background with `none` border. 
- Focus states must transition the background to `primary_fixed` at 30% opacity.

### Operational Chips
- **Status Chips:** Use `secondary_container` for "Ready" and `error_container` for "Missing Ingredient." Text must remain high-contrast (`on_secondary_container`).

### The "Timer" Component (Custom)
A large, `display-lg` readout using `tertiary` (#005faf) color. Place it on a `surface_container_highest` background with a `xl` (1.5rem) corner radius to signify its importance as an active operational tool.

---

## 6. Do's and Don'ts

### Do
- **Do** use whitespace as a functional tool. If the screen feels crowded, increase spacing using the `spacing-8` or `spacing-10` tokens.
- **Do** use `title-lg` for section headers, ensuring they are at least 40px away from the previous section.
- **Do** lean into the "Text-first" aesthetic. If an icon isn't strictly necessary for speed, use a text label.

### Don't
- **Don't** use 1px black or grey borders. They clutter the "Kinetic Manuscript" feel.
- **Don't** use standard Material Design drop shadows. They feel heavy and "late-2010s."
- **Don't** use images as background fillers. Backgrounds must remain clean and functional to ensure maximum text legibility.
- **Don't** use center-alignment for long-form text. All operational instructions must be left-aligned for rapid scanning.