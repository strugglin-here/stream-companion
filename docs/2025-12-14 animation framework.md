# Element Behaviour (aka Animation Framework)

# Implementation approach

No backwards compatibility is required.

We do not need to sandbox user-defined modulation functions, since widgets are also internal to our system.

## Animation ownership: the **playing** state
Widgets (Python) are responsible for defining element behaviour in a list of steps, as well as managing/invoking the **playing** state of the element.
- When element.playing = FALSE, the overlay hides the element and waits for the state to change before continuing animation/behaviours.
- When element.playing is toggled from FALSE to TRUE, steps in the behaviour list are taken sequentially from start to finish.
- Toggling .playing from TRUE to FALSE stops all animations and hides the element

The overlay JavaScript is responsible for running all time based animated behaviors, implementing the .playing property of elements, and for rendering the list of steps defined in the behaviour.

If an element's behaviours are updated while playing=TRUE, the overlay must 
- stop existing element bahaviour 
- begin executing updated list of behaviours 

Dissimilarly, when element **properties** are updated while playing=TRUE, the properties are applied without interrupting the existing element behaviour being rendered in the overly.
This includes color, position, and all other properties.


## Steps: Elements animate as defined in behaviour
Define a set of step types, e.g.:

"appear": make the element visible, trigger entrance animation (does nothing if the element is already visible). Optional parameters for animation and duration.
"animate_property": Animate one or more properties (opacity, transform, etc.) Optional modulation parameter.
"animate": Execute predefined animations From the imported animation libraries (anime.js and GSAP). (spin, flip, zoom, fly, swipe, etc.)
"wait": Pause for a duration
"set": Instantly set one or more properties. Can set a single property or a list of properties.
"disappear": trigger exit animation, set the element not visible (does nothing if the element is already not visible). Optional parameter for animation and duration.

Each step should have a type and parameters, e.g.:

```
"behavior": [
  {"type": "appear", "animation": "fade-out", "duration": 400}
  {
  "type": "animate_property",
  "properties": [
    {"property": "opacity", "from": 0, "to": 1, "duration": 500, "modulation": "easeInOut"},
    {"property": "scale", "from": 1, "to": 1.2, "duration": 300, wait=200}
    ] }
  {"type": "animate", "animation": "flip", "duration": 500},
  {"type": "wait", "duration": 1000},
  {"type": "disappear", "animation": "fade-out", "duration": 400}
]
```

Steps are executed in sequence, first to last, each step waiting serially until the completion of the previous step.
Appear needn't be the first command, as the element's pre-existing state will govern what is shown.
Disappear needn't be the last command, as subsetquent steps will govern the later state of the element.

Wait always waits for a fixed duration.
Many other steps may contain optional waits at the property level, which delays the property's animation within the step.

animate_property can take a list of properties or a single property. 
Whether single or multiple, all properties in the animate_property instance are applied in parallel. 
Properties can be a single object or an array of properties to animate.

For error handling:
- keeps visual output to a minimum, using the console to log errors whenever syntax isn't recognized.
- If a step is invalid or unsupported, the interface will skip the step, warn in the console, and move onto the next step.
- If an animation is invalid, log the error in the console and fail gracefully by moving onto the next animation.

Properties can be modulated according to a modulation function.
Modulation functions are pre-defined or can be customized. 
We expose as many functions from anime.js and GSAP as possible.



## Trigger support
No explicit trigger support in the overlay itself. 
Triggers are used inside widgets, and they lead the widget to modify the element behaviours when the trigger is received.
This way, no extra comunnication apparatus is needed aside from element rendering, which includes:
- element API (where behaviours are communicated and updates), and the
- media API (for multimedia assets)


## Element updates through the admin overlay

Behaviours and animation parameters can be edited with `instant' overlay feedback. Specifically, saving element in the element modal dialog triggers an element update.  As described above,
- If the element properies are changed, they are immediately applied in the overlay
- If the behaviours of the element are changed, the list steps in the behaviour list are restarted

__Reminder__: If the properies change but the behaviours are unchanged, the behaviour of the element in the overlay is unaffected.


## Other details

Overlays aren't synchronized directly, so minor drift between overlay clients is possible.

We vestige the old implementation of 'visible' and 'not visible' ideas which are now replaced by 'playing' flag. In the old paradigm, we set 'visible' to start playing, and 'not visible' to stop playing. Now, there is no visibility notion. When elements are not playing, they are invisible. When elements are playing, they are executing their behaviours, which can make them visible or invisible.

Properties meant to be Dynamic (widget continuously updates them, overlay must sync constantly) and Element-specific (each element type has its own property schema - IMAGE has opacity, width, height; TEXT has font properties, CARD has width and height; etc.)

1. properties could have a schema, since they are based on elements.

2. the element itself defines what properties are valid, and these are based on the element's type.

3. All properties are element specific

4. Each element type has a different set of allowed properties

5. all properties shoudl update mid animation

We also need to vestige the visible and not visible ideas which are now replaced by 'playing' flag. In the old paradigm, we set 'visible' to start playing, and 'not visible' to stop playing. Now, there is no visibility notion. When elements are not playing, they are invisible. When elements are playing, they are executing their behaviours, which can make them visible or invisible.