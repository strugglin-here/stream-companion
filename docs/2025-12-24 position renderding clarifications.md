# Introduction

We need to address a huge oversight in the design of the system's positioning of elements. The documentation omits that all positioning is described in terms of a relative location as a fraction between zero and one. No locations are given in terms of exact pixels, so that the size of the overlay can be dynamically changed and that the measurements -- because they are given relatively -- do not need to be updated.

As an expert programmer receiving my designs as an engineer their job is to ask me a series of questions to clarify the unclear parts and available decisions in this framework that I'm proposing. Our job is to develop a specification together Which we will use then to implement the feature.


# Goal

As an expert programmer receiving my designs as an engineer their job is to ask me a series of questions to clarify the unclear parts and available decisions in this framework that I'm proposing. Our job is to develop a specification together Which we will use then to implement the feature.

# Clarifying points

Not all elements have positions such as sound elements. 

When overlay resizes, elements scale proportionally with the overlay. In the overlay implementation, relative coordinates translate to CSS position: absolute; left/top (then scale via viewport).

z-index should be handled as absolute integers at the overlay level, managed by their associated elements, which are managed by their associated widget through updates.

The "standard" overlay dimensions are 1920×1080 and are configurable per dashboard?
Calculations shouldn't need to account for different aspect ratios (16:9, 4:3, etc.) of the overlay, since we will rely on defining just one of the two dimensions and set the other relative when the ratio of height and width (or x and y position) is important.

elements be positioned relative to the overlay only. media inside of the elemetns are always positioned relative to the origin of th element itself. We do not employe a grid system or flexbox positions, beacuse Python will be able to manipulate the position of elements precisely from within the Python widget code.

For FriendlyFeud cards in a 2-column grid, we specify each card's absolute position on overlay.

0,0 It is at the top left corner and is considered the origin of the relative positioning system.

Position composition is a simple X, Y pair. "position": {"x": 0.5, "y": 0.5}

Size representations can be mixed to preserve an aspect ratio with one relative dimension, using "auto".  "size": {"width": 0.25, "height": "auto"}

Position Not Always Required, Optional in properties (elements without position key are simply not rendered)

Transform Properties in Schema: rotation, scale, opacity, etc. live in properties alongside position/size.

When height: "auto",  ratio explicitly specified in element's properties should be used . If not specified, use  the media's native aspect ratio (for images/videos). Wherever possible, handle at the overlay level.

Position Anchor Point: When you set "position": {"x": 0.5, "y": 0.5}, this refers to Element's center at a Configurable achor point per element via "anchor" property:
"properties": {
  "position": {"x": 0.5, "y": 0.5},
  "anchor": "center"  // or "top-left", "bottom-right", etc.
}

Z-Index Management: z-index is managed by widgets and updated dynamically. Z-index is in properties alongside position.

Overlay Resize Behavior - Viewport Scaling: CSS uses position: absolute; left/top with viewport scaling. This could be implemented via CSS position: absolute; left: 50%; top: 50% (percentage-based, auto-scales).
.element {
  position: absolute;
  left: calc(50% * 1920 / 1920);  /* Always works */
  top: calc(50% * 1080 / 1080);   /* Always works */
  width: 25%;  /* 25% of viewport */
  height: auto;
}

Media Positioning Within Elements: Media inside elements are always positioned relative to the origin of the element itself. For a CARD element with front/back backgrounds, card media (background images) are they always stretched to fill the card's size.

Element Type-Specific Property Schemas: different element types have different allowed properties. properties should be validated at the service layer to ensure widgets don't set invalid properties.

Relative vs Absolute Coordinates in Widget Code: when a widget updates card positions (for the 2-column grid), it should use relative coordinates (0-1) via a Helper method that converts grid positions to relative coordinates. The helper will define these positions using python loops to facilitate the calculation of a little padding between cards.

The meta position-related parameters, accepted by the helper -- from which the positions of cards will be calculated -- are: 
1. total width and the total height of the widget given as relative fractions of the total of overlay
2. vertical spacing between cards as a fraction of overlay height
3. horizontal spacing between columns as a fraction of overlay width
4. the number of cards