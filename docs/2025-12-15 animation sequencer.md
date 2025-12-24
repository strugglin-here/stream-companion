# AnimationSequencer Implementation

## Overview

The `AnimationSequencer` class executes step-based animation sequences on overlay elements using GSAP timeline. It converts the `element.behavior` array (defined in the database) into smooth GSAP animations.

**Location:** `frontend/shared/js/AnimationSequencer.js`
**Imported in:** `frontend/overlay/index.html`

## Architecture

### Step-Based Animation Model

Each element's `behavior` property is an **array of animation steps**. When `element.playing = true`, the overlay:

1. Creates a new `AnimationSequencer` instance
2. Calls `.build()` to parse steps into GSAP timeline
3. Calls `.play()` to execute the timeline

**State Control:**
- `playing: true` → AnimationSequencer executes behavior steps
- `playing: false` → AnimationSequencer stops and element is hidden

### Step Types

| Step Type | Purpose | Example |
|-----------|---------|---------|
| `appear` | Entrance animation | `{type: "appear", animation: "fade-in", duration: 500}` |
| `animate_property` | Animate CSS properties | `{type: "animate_property", properties: [{property: "opacity", from: 0, to: 1, duration: 500}]}` |
| `animate` | Predefined animation | `{type: "animate", animation: "spin", duration: 1000}` |
| `wait` | Pause animation | `{type: "wait", duration: 2000}` |
| `set` | Instantly set properties | `{type: "set", properties: {opacity: 1, color: "red"}}` |
| `disappear` | Exit animation | `{type: "disappear", animation: "fade-out", duration: 300}` |

### Animation Catalog

Predefined animations available via `animation` parameter:

```
fade-in, fade-out
slide-in, slide-out
scale-in, scale-out
explosion, pop
spin, flip
zoom, fly, swipe
```

### Easing Functions

Modulation functions for property animations:

```
linear, ease-in, ease-out, ease-in-out, cubic-bezier
```

## Usage Examples

### Basic Animation Sequence

```javascript
const behavior = [
    {type: "appear", animation: "fade-in", duration: 300},
    {type: "wait", duration: 1000},
    {type: "disappear", animation: "fade-out", duration: 300}
];

const sequencer = new AnimationSequencer(domElement, behavior);
sequencer.build().play();
```

### Property Animation

```javascript
const behavior = [
    {type: "appear", animation: "fade-in", duration: 500},
    {
        type: "animate_property",
        properties: [
            {property: "opacity", from: 0, to: 1, duration: 1000, modulation: "ease-in"},
            {property: "transform", from: "scale(0)", to: "scale(1)", duration: 1000}
        ]
    },
    {type: "wait", duration: 2000},
    {type: "disappear", animation: "fade-out", duration: 500}
];

const sequencer = new AnimationSequencer(domElement, behavior);
sequencer.build().play();
```

### Animation Control

```javascript
const sequencer = new AnimationSequencer(domElement, behavior);
sequencer.build();

// Play
sequencer.play();

// Pause
sequencer.pause();

// Stop and reset
sequencer.stop();

// Restart from beginning
sequencer.restart();

// Query status
const status = sequencer.getStatus();
console.log(status);
// {
//   isPlaying: true,
//   duration: 3.5,
//   progress: 0.5,
//   elementId: "element-123",
//   stepCount: 5
// }
```

## Overlay Integration

### renderElement() Function

The overlay's `renderElement()` function automatically initializes AnimationSequencer:

```javascript
if (element.playing) {
    elementDiv.classList.add('playing');
    
    if (Array.isArray(element.behavior) && element.behavior.length > 0) {
        try {
            const sequencer = new AnimationSequencer(elementDiv, element.behavior);
            sequencer.build().play();
            elementDiv.sequencer = sequencer;  // Store for later updates
        } catch (err) {
            console.error(`Animation failed:`, err);
        }
    }
} else {
    elementDiv.classList.add('stopped');
    
    if (elementDiv.sequencer) {
        elementDiv.sequencer.stop();
        delete elementDiv.sequencer;
    }
}
```

### CSS State Classes

```css
/* Element is executing animation */
.element.playing {
    /* Visibility and opacity controlled by GSAP timeline */
}

/* Element is stopped and hidden */
.element.stopped {
    opacity: 0;
    pointer-events: none;
}
```

## Broadcasting Pattern

From Python backend (widgets):

```python
async def my_feature(self):
    element = self.get_element("my_element")
    
    # Update behavior
    element.behavior = [
        {type: "appear", animation: "explosion", duration: 500},
        {type: "wait", duration: 2000},
        {type: "disappear", animation: "fade-out", duration: 300}
    ]
    
    # Start playing
    element.playing = True
    
    # CRITICAL: Commit BEFORE broadcasting
    await self.db.commit()
    
    # Now broadcast to overlay
    await self.broadcast_element_update(element)
```

The overlay receives the update and:
1. Detects `playing: true`
2. Checks if behavior is a non-empty array
3. Creates and builds new AnimationSequencer
4. Executes the animation sequence

## Error Handling

AnimationSequencer includes graceful degradation:

- **Unknown step type:** Logged as warning, skipped
- **Invalid animation name:** Logged as warning, skipped
- **Missing properties:** Logged with details, step skipped
- **Malformed step object:** Caught, logged, execution continues to next step

Console will show:
```
Step 2: unknown animation 'invalid-name'
Step 3: Error processing step ...
Animation complete for element: element-123
```

## Performance Considerations

**GSAP Timeline Efficiency:**
- Each element gets its own timeline
- Timeline built once, can be reused if behavior doesn't change
- Multiple concurrent animations supported (no blocking)

**Memory:**
- Sequencer attached to DOM element as `element.sequencer`
- Cleaned up when `playing: false` (sequencer.stop() called)
- No memory leaks from lingering timelines

**Animation Budget:**
- GSAP uses requestAnimationFrame (60fps max)
- Multiple elements animate smoothly on modern hardware
- Complex easing functions calculate per-frame (CPU overhead)

## Debugging

Enable console logging (default enabled):

```javascript
// In renderElement():
console.log(`Started animation for element ${element.id} with ${element.behavior.length} steps`);

// In AnimationSequencer._addStep():
console.log(`Step ${stepIndex}: appear animation '${animation}' (${duration}s)`);

// Sequencer lifecycle:
console.log(`Playing animation for element: ${this.domElement.id}`);
console.log(`Animation complete for element: ${this.domElement.id}`);
```

Browser DevTools:
```javascript
// Query animation status
const div = document.getElementById('element-123');
console.log(div.sequencer?.getStatus());

// Control animation
div.sequencer?.pause();
div.sequencer?.setProgress(0.5);  // Jump to 50%
div.sequencer?.play();
```

## Future Enhancements

1. **Property Update During Animation:** Detect when `element.properties` changes while `playing=true`, apply only changed properties without restarting
2. **Behavior Hot-Reload:** Update behavior while animation plays, smoothly transition to new sequence
3. **Animation Event Callbacks:** Hook into step completion, element visibility changes
4. **Animation Library Export:** Save/replay animation sequences
5. **Keyframe Preview:** Overlay timeline showing animation steps in admin UI

## Technical References

- **GSAP Documentation:** https://gsap.com/docs/
- **Animation Framework Spec:** `2025-12-14 animation framework.md`
- **Element Model:** `app/models/element.py` (behavior field, playing flag)
- **Behavior Validation:** `app/services/behavior_service.py` (step validation)
- **Overlay HTML:** `frontend/overlay/index.html` (renderElement integration)


## Key feedback and notes

1: sequencer does not need to track progress.

2: properties in a single animate_property step have different durations each

play() should always restart from step 0 when bahviour is updated.

updateProperties() should be called automatically from overlay when properties change

only explicit css properties can be updated mid-animation

yes, it should validate that only certain properties are updateable.