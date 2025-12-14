# Element Behaviour (aka Animation Framework)

## Animation ownership 
Widgets are responsible for defining element behaviour in a list of steps which are taken sequentially from start to finish.

The overlay JavaScript is responsible for running all time based animated behaviors and for rendering the list of steps defined in the behaviour.

When an element behaviour is changed by a widget and committed to the database, the overlay must 
- stop existing element bahaviour 
- begin executing new list of behaviours from start to finish


## Elements animate as defined in behaviour
Define a set of step types, e.g.:

"appear": trigger entrance animation (does nothing if the element is already visible)
"animate": Animate one or more properties (opacity, transform, etc.)
"wait": Pause for a duration or until a trigger
"loop": Repeat a set of steps (with optional count/infinite)
"trigger": Wait for an external event (e.g., user action, feature call)
"set": Instantly set a property
"disappear": trigger exit animation (does nothing if the element is already not visible)

Each step should have a type and parameters, e.g.:

```
"behavior": [
  {"type": "animate", "property": "opacity", "from": 0, "to": 1, "duration": 500},
  {"type": "wait", "duration": 1000},
  {"type": "animate", "property": "scale", "from": 1, "to": 1.2, "duration": 300, "loop": 3},
  {"type": "exit", "animation": "fade-out", "duration": 400}
]
```

If a step is invalid or unsupported, the interface will skip the step, warn in the console, and fail gracefully.


## Trigger support
No explicit trigger support in the overlay itself. 
Triggers are used inside widgets, and they lead the widget to modify the element behaviours when the trigger is received.
This way, no extra comunnication apparatus is needed aside from element rendering, which includes:
- element API (where behaviours are communicated and updates), and the
- media API (for multimedia assets)

