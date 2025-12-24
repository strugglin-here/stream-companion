# Development Status & Next Steps - 2025-12-24

## Current State Summary

### ✅ Completed Foundation
- **Animation Framework (Complete):** Step-based animation system with GSAP integration
- **Media System (Complete):** Database-backed media storage with ElementAsset junction table
- **Element System (Complete):** Multi-asset support, roles, media relationships
- **Widget Base Architecture (Complete):** Feature decorator, element management, broadcasting
- **Overlay (Complete):** Real-time element rendering with AnimationSequencer integration
- **Admin UI (Complete):** Dashboard/widget management, element editor with multi-asset support
- **Alert Widget (Complete):** Reference implementation demonstrating widget patterns

### 📋 Current Task: Friendly Feud Widget Implementation

The **Card Element** (CARD type) is the critical blocker. All features depend on it. Once CARD is implemented, the FriendlyFeudWidget can be built on top.

---

## Next Steps for Friendly Feud Implementation

### Phase 1: Card Element Foundation (BLOCKING - Required)

#### 1.1 Add CARD ElementType to Model
**File:** `app/models/element.py`
- Add `CARD = "card"` to `ElementType` enum (line 13)
- Document: card has front/back sides with independent background + content

#### 1.2 Define Card Properties Schema
**File:** `app/models/element.py` (documentation/reference)
- Define standard card properties structure:
  ```python
  {
    "width": 200,           # Card width in pixels
    "height": 300,          # Card height in pixels
    "media_roles": [        # Define available media roles per card
      "front_background",   # Background image for face-down side
      "back_background",    # Background image for face-up side
      "back_content"        # Text content on back side (stored as text)
    ],
    "front_text": "?",      # Display text on front side (default "?")
    "back_text": "ANSWER",  # Display text on back (set dynamically by widget)
    "revealed": False       # Current face-up/face-down state
  }
  ```
- Note: Media roles use ElementAsset table; `back_text` stored in properties JSON

#### 1.3 Overlay Card Rendering
**File:** `frontend/overlay/index.html` + `frontend/shared/js/AnimationSequencer.js`

**Add card rendering logic to `renderElement()`:**
- Create card HTML structure: `<div class="card"><div class="front"></div><div class="back"></div></div>`
- Front side: background image + "?" text
- Back side: background image + answer text
- Apply CSS 3D transforms: `perspective`, `transform-style: preserve-3d`
- Store `revealed` state in card properties

**Card flip animation:**
- Add `'flip'` animation to AnimationSequencer catalog (if not present)
- Use GSAP `rotationY` property for 3D flip effect
- Example: `{type: "animate", animation: "flip", duration: 500}` to flip to back

**CSS for card element:**
```css
.element.card {
    perspective: 1000px;
}

.element.card .card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s;
    transform-style: preserve-3d;
}

.element.card .card-front,
.element.card .card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
}

.element.card .card-back {
    transform: rotateY(180deg);
}
```

#### 1.4 Card Element Testing
- Create manual test card elements in admin UI
- Verify rendering (front side shows "?", back shows answer)
- Test flip animation via element edit → behavior update
- Verify card state persists with `revealed` flag

---

### Phase 2: FriendlyFeudWidget Implementation

#### 2.1 Create FriendlyFeudWidget Class
**File:** `app/widgets/friendlyfeud.py` (new)

**Structure:**
```python
@register_widget
class FriendlyFeudWidget(BaseWidget):
    widget_class = "FriendlyFeudWidget"
    display_name = "Friendly Feud"
    
    @classmethod
    def get_default_parameters(cls):
        return {
            "max_strikes": 3,
            "guess_eval_frequency": 1.5,
            "guess_eval_jitter": 0.5,
            "fuzzy_match_threshold": 95,
            "fade_round_after_end": True
        }
    
    async def create_default_elements(self):
        # Create 10 CARD elements
        # Create 1 TEXT element for score display
        # Create 1 TEXT element for strike X's
        # Create 3 AUDIO elements (ding, buzzer, start, end)
```

#### 2.2 Element Creation
Create 13 default elements:
- **10 CARD elements:** `card_1` through `card_10` (positioned in 2 columns)
- **1 TEXT element:** `score_counter` (bottom-right, large font, styled box)
- **1 TEXT element:** `strike_display` (huge red X's, 30% of screen)
- **3 AUDIO elements:** `ding_sound`, `buzzer_sound`, `round_end_sound`

Cards should start with:
- `properties["revealed"] = False`
- `behavior = []` (no animation until round starts)
- `playing = False` (hidden)

#### 2.3 Features - Phase A (Basic)

**Feature 1: `start_new_round`**
- Input: List of dicts `[{"answer": str, "synonyms": [str], "points": int}, ...]` (1-10 items)
- Logic:
  1. Sort answers by points (descending)
  2. Arrange in 2 columns (col1: high→low, col2: high→low)
  3. Reset card states (unrevealed)
  4. Show only active cards, hide unused ones
  5. Reset scores to 0
  6. Start guess buffer loop

**Feature 2: `make_guess`**
- Input: `guess` (str), `player` (str)
- Logic:
  1. Buffer guess (add to internal queue)
  2. On evaluation interval, check guess against answers + synonyms
  3. If match: reveal card, play ding, increment scores
  4. If no match: increment strikes, play buzzer, show X's
  5. If max strikes reached: auto-trigger `reveal_all`

**Feature 3: `reveal_one`**
- Logic: Flip unrevealed card with lowest points, play ding

**Feature 4: `reveal_all`**
- Logic: Reveal all unrevealed cards sequentially with delay, play end sound

#### 2.4 State Management
- **Active round data:** `self.active_round` dict with answers, card→answer mapping
- **Guess buffer:** `self.guess_buffer` (queue of guesses)
- **Player scores:** `self.player_scores` dict (per-round tracking)
- **Guess evaluation loop:** Background task checking buffer at configured frequency
- **Finished flag:** `self.round_finished` to break evaluation loop

#### 2.5 Fuzzy Matching Integration
- Install `rapidfuzz` package: `pip install rapidfuzz`
- Use in guess evaluation:
  ```python
  from rapidfuzz.fuzz import token_set_ratio
  
  threshold = self.widget_parameters["fuzzy_match_threshold"]
  for answer in answers:
      if token_set_ratio(guess, answer) >= threshold:
          # Match found
  ```

---

### Phase 3: Advanced Features (After Phase 2)

#### 3.1 Admin UI Enhancements
- **Add "Friendly Feud" preset data:** Pre-populated example round (TV show questions)
- **Feature param UI:** Better input for complex data (answer list editor)
- **Player score display:** Show per-player scores during round

#### 3.2 Player Module (Mentioned in friendlyfeud.md)
- Create `app/models/player.py` with Player model
- Track player stats, cumulative scores across rounds
- Link to FriendlyFeud rounds

#### 3.3 Documentation Improvements
**Files to create/improve:**
- `docs/2025-12-24 friendly-feud-widget.md` - Complete FriendlyFeudWidget guide
  - Architecture overview
  - Feature specifications
  - Player model integration
  - Usage examples
  
- Update `docs/2025-12-07 card element.md` → Phase 3 completion notes

---

## Documentation Recommendations

### High Priority
1. **Card Element Rendering Guide** (`docs/card-element-rendering.md`)
   - CSS 3D transforms for cards
   - GSAP flip animation examples
   - Debugging card state issues

2. **FriendlyFeudWidget Architecture** (`docs/friendly-feud-design.md`)
   - Async guess buffering pattern
   - Fuzzy matching algorithm choice
   - Player score tracking design

### Medium Priority
3. **Element Types Reference** (update `README.md`)
   - Add CARD to element type documentation
   - Properties schema for each type
   - Multi-asset roles explanation

4. **Widget Development Guide**
   - Copy AlertWidget as template
   - Explain feature decorator parameters
   - Broadcasting pattern best practices

---

## Code Review Findings

### ✅ Strengths
- **Clean separation:** Widgets own elements, API doesn't expose elements directly
- **Animation framework:** GSAP integration is solid, graceful error handling
- **Admin UI:** Multi-asset editing works well, role-based asset management
- **Database patterns:** Proper eager loading, cascade deletes, constraints

### 🔧 Improvements to Consider

#### 1. AnimationSequencer.js Documentation
- Add JSDoc comments to public methods (`.build()`, `.play()`, `.pause()`, etc.)
- Current: Excellent inline comments but public API not clearly documented
- Impact: Easier for new features to extend animation types

#### 2. Widget Feature Parameter Types
- Current: Supports dropdown, text, color-picker, number, checkbox, multiselect
- Missing: Date picker, time picker, complex nested objects
- For FriendlyFeud: Need structured "answer list" input (array of objects)
- Recommendation: Add `structured` type or extend parameter system

#### 3. Behavior Service Validation
- Current: Validates step syntax but only at API level
- Missing: Widget-level validation before persist
- Risk: Invalid behavior could be stored if widget bypasses service
- Recommendation: Widgets should call `validate_behavior_array()` before commit

#### 4. WebSocket Message Types
- Current: `element_update`, `dashboard_activated`, `dashboard_deactivated`
- Missing: `round_started`, `player_scored`, `player_eliminated` (game-specific)
- Option 1: Keep generic element_update (current approach)
- Option 2: Add specific event types for richer overlay interactivity
- Recommendation: Stay with Option 1 (element_update) for consistency

#### 5. Fuzzy Matching Selection
- Current: No fuzzy matching logic exists yet
- Choice: `rapidfuzz` vs `fuzzywuzzy`
- Recommendation: Use `rapidfuzz` (faster, better maintained, same API)
- Include: Threshold as widget parameter (configurable, default 95%)

---

## File Structure Impact

New/Modified files:
```
app/
  widgets/
    friendlyfeud.py          (NEW)
    __init__.py              (UPDATE: register FriendlyFeudWidget)
  models/
    element.py               (UPDATE: Add CARD ElementType)

frontend/
  overlay/
    index.html               (UPDATE: Card rendering logic)
  shared/
    js/AnimationSequencer.js (UPDATE: Ensure flip animation works)
    
docs/
  2025-12-24 development-status.md (NEW - this file)
  card-element-rendering.md  (NEW)
  friendly-feud-design.md    (NEW)

pyproject.toml               (UPDATE: Add rapidfuzz dependency)
```

---

## Dependency Additions

```toml
# pyproject.toml
dependencies = [
    # ... existing deps ...
    "rapidfuzz>=2.15.0",  # Fuzzy string matching for answer comparison
]
```

---

## Risk Mitigation

### Card Element Complexity
- **Risk:** 3D CSS transforms may have browser compatibility issues
- **Mitigation:** Test on Chrome, Firefox, Edge; fallback to 2D if needed
- **Fallback:** Use rotation instead of rotationY for 2D cards

### Async Guess Buffer
- **Risk:** Race conditions in guess evaluation loop
- **Mitigation:** Use asyncio.Queue, proper locking on card state
- **Testing:** Unit tests for concurrent guess handling

### Fuzzy Matching Performance
- **Risk:** Many synonyms + many guesses could be slow
- **Mitigation:** Cache compiled regex patterns, limit synonym list size
- **Optimization:** Profile with 100+ answers, optimize if needed

---

## Success Criteria

### Card Element Implementation ✓
- [ ] CARD ElementType added and enum includes it
- [ ] Card renders front/back with background images
- [ ] Flip animation works via behavior steps
- [ ] Card state persists correctly (`revealed` flag)
- [ ] Admin UI can edit card media and text

### FriendlyFeudWidget Phase 1 ✓
- [ ] Widget creates 10 card + 3 text + 3 audio elements
- [ ] `start_new_round` feature works with answer list input
- [ ] Cards display in 2-column grid, sorted by points
- [ ] `make_guess` feature buffers and evaluates guesses
- [ ] Fuzzy matching works (95% threshold, case-insensitive)
- [ ] Strike counter works, max_strikes ends round
- [ ] All audio plays (ding, buzzer, end)
- [ ] Player scores tracked per round
- [ ] Round end fade out works (if enabled)

### Documentation ✓
- [ ] This status file committed
- [ ] Card rendering guide created
- [ ] FriendlyFeud architecture guide created
- [ ] Element types reference updated

---

## Estimated Timeline

- **Phase 1 (Card Element):** 4-6 hours
  - Element type (30 min)
  - Overlay rendering + CSS (2 hours)
  - GSAP flip animation (1 hour)
  - Testing (1.5 hours)

- **Phase 2 (FriendlyFeudWidget Core):** 6-8 hours
  - Widget scaffold (1 hour)
  - Element creation (1 hour)
  - start_new_round feature (1.5 hours)
  - Guess buffer + evaluation loop (2 hours)
  - Testing & debugging (1.5-2 hours)

- **Phase 3 (Advanced):** 4-6 hours (lower priority, can iterate)

---

## Quick Start Commands

Once phases complete, test with:

```bash
# Terminal 1: Run backend
python run.py

# Terminal 2 (browser): Admin UI
http://localhost:8000/admin

# Terminal 3 (browser): Overlay
http://localhost:8000/overlay

# Test FriendlyFeud:
# 1. Create new widget (FriendlyFeudWidget type)
# 2. Add to active dashboard
# 3. Execute "start_new_round" with sample data
# 4. Execute "make_guess" with test guesses
```

---

## Notes for Future Reviewer

This review was conducted 2025-12-24 after:
- Animation framework complete (GSAP + step-based model)
- Media system migrated to database
- Element multi-asset support implemented
- Alert widget as reference implementation

The project is well-structured and ready for widget development. The main blocker is the CARD element type - once that's added to the model and rendering logic implemented, FriendlyFeudWidget can proceed with minimal friction.

Code quality is high:
- Type hints throughout
- Async/await properly used
- Error handling graceful
- Architecture follows widget-first philosophy

Recommend prioritizing Phase 1 (Card Element) as the foundation for all future card-based games/widgets.
