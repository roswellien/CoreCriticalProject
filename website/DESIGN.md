---
name: Core Critical
description: Original gameplay. A modern core.
colors:
  ground: "#141717"
  ink: "#eee6dc"
  amber: "#efa348"
  muted: "#c4c4be"
  rule: "#373b3a"
  panel: "#111615"
  reading-ink: "#d4d4cd"
  button-ground: "#332716"
  button-ink: "#ffd094"
  progress-ground: "#1b211e"
typography:
  display:
    fontFamily: "Orbitron, sans-serif"
    fontSize: "4.427vw"
    fontWeight: 900
    lineHeight: 0.86
    letterSpacing: ".01em"
  edition:
    fontFamily: "RussoOne, sans-serif"
    fontSize: "3.58vw"
    fontWeight: 400
    lineHeight: 0.95
    letterSpacing: ".07em"
  overview-display:
    fontFamily: "Orbitron, sans-serif"
    fontSize: "clamp(32px, 3.8vw, 60px)"
    fontWeight: 700
    lineHeight: 1.16
  headline:
    fontFamily: "Barlow, sans-serif"
    fontSize: "36px"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "Barlow, sans-serif"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: "Barlow, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.55
  reading:
    fontFamily: "Barlow, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Barlow, sans-serif"
    fontSize: "12px"
    letterSpacing: ".16em"
rounded:
  square: "0px"
  track-icon: "6px"
spacing:
  gutter: "3.646vw"
  mobile-gutter: "24px"
  button: "12px 22px"
  section-gap: "50px"
  mobile-section-gap: "32px"
components:
  button-primary:
    backgroundColor: "{colors.button-ground}"
    textColor: "{colors.button-ink}"
    rounded: "{rounded.square}"
    padding: "{spacing.button}"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.ground}"
  progress-note:
    backgroundColor: "{colors.progress-ground}"
    padding: "26px 30px"
    rounded: "{rounded.square}"
  section-index:
    textColor: "{colors.muted}"
    width: "230px"
  section-index-hover:
    textColor: "{colors.amber}"
  navigation-active:
    textColor: "{colors.amber}"
---

# Design System: Core Critical

## Overview

**Creative North Star: "Original gameplay. A modern core."**

This is a scan of the incumbent website, not a new identity proposal. Its charcoal material ground, amber controls, reactor mark, and approved generated illustrations establish the existing Core Critical world. Large mechanical display lettering introduces the flagship; quieter Barlow text supports project reading.

The homepage remains an artwork-led game project presentation. The four overview surfaces extend its material and type system with restrained dividers and readable prose. They are static reading pages implemented in the HTML files in `website/`.

**Key Characteristics:**

- Charcoal texture and amber controls.
- Orbitron display lettering, Barlow reading text, and the desktop RussoOne MW3 edition treatment.
- Existing reactor mark and illustrative raster artwork.
- Square controls, fine dividers, and bounded prose.

## Colors

The frontmatter is the normative extracted palette; these names retain the stylesheet's existing roles.

### Primary

- **Amber:** actions, current navigation, status labels, arrows, selection, and keyboard focus.
- **Button ground / button ink:** the resting amber action uses a dark warm fill and lighter warm text; hover uses amber against the ground.

### Neutral

- **Ground:** textured page field.
- **Panel:** overview hero, overview header, and mobile navigation field.
- **Ink:** primary text and headings.
- **Reading ink:** long-form content paragraphs.
- **Muted:** supporting descriptions and section-index links.
- **Rule:** section boundaries, cards, and reading dividers.
- **Progress ground:** the factual progress-note container.

**The Incumbent Palette Rule.** Extend the observed charcoal and amber assignments; do not introduce a replacement palette into these pages.

## Typography

**Display Font:** Orbitron with sans-serif fallback.
**Body Font:** Barlow with sans-serif fallback.
**Edition Font:** RussoOne with sans-serif fallback, restricted to the existing desktop MW3 edition treatment.

Self-hosted font files in `assets/fonts` are part of the shipped implementation. The display/body contrast supplies hierarchy without a separate technical monospace system.

### Hierarchy

- **Display:** homepage title, two stacked lines; its desktop spatial treatment is retained below.
- **Edition:** the desktop MW3 label, paired with an amber horizontal rule.
- **Overview display:** project intro headings with balanced wrapping and a 20ch limit.
- **Headline:** overview section headings.
- **Title:** overview subsections and cross-effort rows.
- **Body:** site baseline text.
- **Reading:** overview paragraphs, bounded to 72ch.
- **Label:** uppercase project-state labels. Navigation uses Barlow rather than the display face.

The homepage title's approved desktop composition is deliberately spatial: above 760px, CORE scales horizontally by 1.2 and CRITICAL by 1.16 from a left origin, with no inter-line margin. The copy begins at 39.1% of hero height. The edition rule is 13vw wide, and the RussoOne MW3 lettering scales horizontally by 1.36. Preserve these as homepage-specific composition, not a generic heading recipe. At 1800px and above, the title caps at 80px. On mobile the title uses `clamp(37px,10.9vw,66px)` with .92 leading; the MW3 label returns to Orbitron at 40px.

Overview headings become 32px on mobile; section headings become 29px and reading text 17px while retaining its 1.7 leading.

## Layout

The site uses full-width material sections with a fluid gutter and a 24px mobile gutter. The homepage hero is 37.1745vw tall on desktop and 600px on mobile. Its art fills the frame; mobile crops at 64% horizontally and places the title near the lower left. The homepage track grid has three columns, then one column at 760px and below.

Overview pages use an 82px desktop header, a two-column split introduction/art hero with a 460px minimum height, and a reading area capped at 1480px. A 230px section index sits beside the prose with a 70px gap; the index sticks 32px from the viewport top. The reading sections are bounded to 76ch, with paragraphs at 72ch and dividers between sections. At 1150px and below, the index becomes 190px and its gap 36px. Between 761px and 900px the overview navigation occupies a separate row.

At 760px and below the header is 68px, the hero artwork becomes a 200px-high block above the introduction, the section index becomes an inline link group, and the body becomes a single column. Overview work rows stack. The mobile section rhythm is 32px. Keep these reading adaptations scoped to the overview surfaces.

## Elevation & Depth

Depth comes from the actual repeated surface-texture raster, cropped illustrative art, dark translucent overlays, tonal panels, and thin rules. There is no box-shadow vocabulary in the current stylesheet. Homepage artwork tracks carry imagery behind text, while progress notes use a quiet tonal container. Preserve the original assets rather than simulating their material with decorative CSS.

Motion is limited to existing smooth anchor scrolling and a .2s background/color transition on action-rail links. Reduced-motion preference disables smooth scrolling and transitions. No new animation is needed by the overview reading surfaces.

## Shapes

Buttons and reading containers have square corners. Track-icon tiles are the established small rounded exception. Borders are thin and mostly use the rule color; primary buttons use amber. Arrows and menu icons use inline stroked SVG with rounded line caps and joins. Retain the reactor mark rather than replacing it with a generic geometric symbol.

## Components

### Buttons

Square, confident amber actions. The frontmatter records the resting fill, text, padding, and hover assignments. The existing 48px value is a minimum height, not a fixed height; longer labels remain readable. The inline arrow is separated from the label by 24px. Keyboard focus uses a 2px amber outline offset by 5px. Overview buttons preserve this same treatment.

### Navigation

The homepage's approved desktop links are positioned individually across its header; do not normalize that composition as part of overview work. Overview navigation instead flows naturally beside the brand with 24px gaps. Current-page links and hovered links become amber. Mobile uses the existing Menu control and a dark disclosure below the 68px header. Escape returns focus to Menu; links, outside clicks, and desktop resizing close the disclosure.

### Cards / Containers

Homepage modernization tracks retain their existing cropped raster art, border, icon tile, and bottom-aligned text. Hover turns the border and heading amber. Progress notes use the progress ground, a rule border, and the observed padding; mobile padding becomes 22px. They communicate a development boundary without introducing a new visual alert system.

### Section Index

A fine top rule and quiet Barlow links orient the reader. Desktop positioning is sticky; mobile changes to normal flow and inline links. Hover uses amber. Anchor destinations retain the existing scroll offsets.

### Reading Rows and FAQ

Work rows align a short label with an explanation on desktop and stack on mobile. Cross-effort rows use a divider and a right-aligned amber SVG arrow. FAQ uses native `details` and `summary`, with an amber disclosure marker, a thin separator, and the shared keyboard focus treatment. There are no inputs, form fields, custom dialogs, or filter chips on the documented surfaces.

## Do's and Don'ts

### Do:

- **Do** preserve the charcoal texture, amber controls, reactor mark, and approved illustrative artwork.
- **Do** retain the Orbitron/Barlow roles and the homepage-specific RussoOne edition treatment.
- **Do** preserve bounded prose, clear dividers, and the observed mobile reading adaptation.
- **Do** retain visible keyboard focus and reduced-motion behavior.
- **Do** identify website artwork as illustrative rather than captured gameplay or tool interfaces.

### Don't:

- **Don't** replace the incumbent visual identity while extending these overview pages.
- **Don't** generalize the homepage title's horizontal scaling to ordinary page headings.
- **Don't** invent rounded controls, shadow stacks, forms, or animation that the current system does not use.
- **Don't** present the generated illustrations as evidence of completed software features.
