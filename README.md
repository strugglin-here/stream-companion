# Stream Companion - OBS Web Overlay System

Project is under development. Join me, strugglin_here, on twitch and youtube on Wednesdays sometime around 10AM PST:

[youtube.com/@strugglin_here](https://www.youtube.com/@strugglin_here/streams)

[twitch.tv/strugglin_here](https://www.twitch.tv/strugglin_here)


## Project Overview
This project creates a web overlay, hosted locally, which can be used as an OBS browser source.  The project also creates a web admin web portal where the overlay can be managed and controlled live.

A variety of visual/effect sequences can be crafted using the building blocks in the system.


### Design Principles and Core Concepts
Simplicity, ease of use, power, and fun.

Stream Companion is built from four connected layers: **Elements**, **Widgets**, **Features**, and **Dashboards**.
Together, they form a flexible system for creating, organizing, and controlling your stream overlay. These layers are stored in a local database and managed through an intuitive admin interface.

#### Elements
Elements are the fundamental building blocks owned by Widgets. Each Element represents a single media asset or display component:
- **Images** - Static or animated graphics (PNG, JPEG, GIF, WebP)
- **Videos** - Video clips with audio (MP4, WebM)
- **Audio** - Sound effects or background music (MP3, WAV, OGG)
- **Text** - Dynamic text displays with custom styling
- **Timers** - Countdown or countup displays
- **Counters** - Numeric displays that increment/decrement
- **Animations** - Complex animated sequences
- **Canvas** - HTML5 canvas for custom rendering (particles, drawing, effects)

**Key Properties:**
- Each Element belongs to exactly **one Widget** (ownership model)
- Element names are **immutable** after creation and must be **unique within each Widget**
  - Widget features reference elements by name (e.g., `get_element("confetti_particle")`)
  - Database enforces uniqueness via `UniqueConstraint('widget_id', 'name')`
  - Names cannot be changed through the admin interface or API
- Elements have `properties` (position, size, opacity, CSS styling) and `behavior` (entrance/exit animations, triggers)
- Elements can be `visible` (currently displayed on overlay) - this is the only state flag needed
- Elements are created automatically when a Widget is instantiated, with sensible defaults
- Users configure Elements through the admin interface (e.g., selecting media files from the library)

**Element Lifecycle:**
1. Widget is instantiated → Widget creates default Elements with **permanent names**
2. User optionally configures Element properties (upload custom media, adjust position)
   - **Note:** Element names cannot be changed after creation
3. Widget Features manipulate Element visibility and properties at runtime
4. Overlay renders Elements based on their current state

#### Widgets
Widgets are reusable, configurable components that orchestrate Elements to create rich overlay experiences. Each Widget is a Python class that defines its own behavior, features, and default elements.

**Widget Characteristics:**
- **Ownership:** Widgets own their Elements (one-to-many relationship)
- **Reusability:** The same Widget instance can appear on multiple Dashboards simultaneously
- **Instantiation:** Widgets can be instantiated multiple times, each with its own configuration
- **Shared State:** A Widget instance maintains one configuration across all Dashboards it appears on
- **Self-Contained:** Each Widget knows how to create its default Elements and expose its Features

**Widget Parameters:**
Widget-wide settings that control internal behavior (stored as JSON in database):
- Animation durations and easing curves
- Default colors and styling
- Particle counts, velocities, physics settings
- Timing intervals for automatic actions
- Any configuration that affects multiple Features or Elements

**Example Widgets:**
- **Confetti Alert Widget** - Celebratory particle explosion with sound
  - Elements: confetti_particle.png, pop.mp3
  - Parameters: blast_duration (2.5s), particle_count (100), default_color (#FF5733)
  
- **Donation Goal Widget** - Progress bar with dynamic text
  - Elements: progress_bar.png, goal_text, current_amount_text, donor_name_text
  - Parameters: goal_amount ($500), update_interval (1s), bar_color (#4CAF50)
  
- **Poll Widget** - Display chat poll results in real-time
  - Elements: poll_question_text, option_1_bar, option_2_bar, option_3_bar, timer_text
  - Parameters: poll_duration (60s), max_options (5), auto_close (true)

#### Features
Features are **executable actions** provided by Widgets. Each Feature is a method decorated with metadata that defines user-triggerable behavior.

**Feature Characteristics:**
- **Owned by Widgets:** Features belong to a specific Widget class
- **Fixed per Widget Type:** Each Widget class defines its own set of Features (not user-customizable)
- **Parameter-Driven:** Features accept parameters provided by the user at execution time
- **Element Manipulation:** Features modify Element properties and visibility to create effects
- **Widget Parameter Access:** Features use Widget Parameters for internal timing/behavior

**Feature Parameters:**
Runtime inputs provided by the user when executing a Feature:
- **Parameter Types:** dropdown, multiselect, checkbox, text input, color picker, number slider
- **Optional/Required:** Parameters can have defaults or be mandatory
- **Validation:** Parameter types ensure correct input (e.g., valid hex color, number in range)

**Feature vs Widget Parameters:**
- **Widget Parameters** = Configuration (set once, affects all Features): animation speeds, default colors
- **Feature Parameters** = Runtime Arguments (provided each execution): intensity level, custom text

**Example Features:**
```
Widget: ConfettiAlertWidget
  Feature: trigger_blast
    - Feature Parameter: intensity (dropdown: Low/Medium/High) [required]
    - Feature Parameter: color (color-picker) [optional, default: #FF5733]
    - Uses Widget Parameter: blast_duration for animation timing
    - Manipulates Elements: sets confetti_particle visible, updates behavior properties

Widget: DonationGoalWidget
  Feature: add_donation
    - Feature Parameter: amount (number) [required]
    - Feature Parameter: donor_name (text) [optional]
    - Uses Widget Parameter: goal_amount to calculate percentage
    - Manipulates Elements: updates current_amount_text, animates progress_bar

  Feature: reset_goal
    - No Feature Parameters
    - Uses Widget Parameter: goal_amount to reset state
    - Manipulates Elements: resets progress_bar to 0%, clears donor list
```

**Feature Execution:**
1. User provides Feature Parameters (if any)
2. User clicks Feature button in Dashboard
3. System calls Widget method with parameters
4. Feature method manipulates Widget's Elements (properties, visibility, behavior)
5. Changes are persisted to database and broadcast via WebSocket
6. Overlay receives Element updates and re-renders

**Feature Triggers:**
While Dashboards provide standard button-based triggers, Features are designed to be triggered from multiple sources:
- **Dashboard Buttons** - Primary UI mechanism (implemented in this system)
- **Chat Commands** - Future: `!confetti high red` executes feature with parameters
- **WebSocket Events** - Future: External apps can trigger features
- **Scheduled Tasks** - Future: Time-based feature execution
- **Platform Events** - Future: Trigger on new follower, donation, etc.

This generalized Feature model ensures extensibility beyond the current dashboard-based implementation.

#### Dashboards
Dashboards are organizational tabs in the admin interface that group related Widgets together. They provide the primary user interface for managing and triggering overlay content during a stream.

**Dashboard Characteristics:**
- **Tab-Based UI:** Each Dashboard appears as a tab in the admin interface
- **Active State:** Only one Dashboard is active at a time
- **Widget Management:** Dashboards display all Widgets added to them, with controls for each
- **Shared Widgets:** A single Widget instance can appear on multiple Dashboards (shared state)
- **Scene Organization:** Dashboards typically correspond to stream scenes (e.g., "Starting Soon", "Main Stream", "Break Screen", "End Screen")

**Dashboard Activation:**
When a Dashboard is activated:
1. Previous active Dashboard is deactivated
2. All Widgets from previous Dashboard disabled
3. Widgets send WebSocket notification to overlay to stop the rendering of their elements
4. New Dashboard becomes active and that dashboard's Widgets are enabled, set with their previous state
5. User can then enable/trigger individual Widget Features as needed

**Widget Display on Dashboard:**
Each Widget on a Dashboard is displayed as a management panel containing:

```
┌────────────────────────────────────────────────┐
│ Widget Name: "My Confetti Alert"               │
│ Type: ConfettiAlertWidget                      │
├────────────────────────────────────────────────┤
│ [📋 Widget Parameters] [🎨 Elements]          │
├────────────────────────────────────────────────┤
│ Features:                                      │
│                                                │
│ ▸ Trigger Confetti Blast                       │
│   Intensity: [Low ▼]                           │
│   Color: [🎨 #FF5733]                         │
│   [▶ Execute]                                 │
│                                                │
│ ▸ Stop Confetti                                │
│   [▶ Execute]                                 │
└────────────────────────────────────────────────┘
```

- **Widget Parameters Button:** Opens dialog to edit Widget-wide configuration (blast_duration, particle_count, etc.)
- **Elements Button:** Opens dialog showing all Elements owned by the Widget (configure media files, positions, etc.)
- **Feature List:** Each Feature displayed with its parameter inputs and Execute button
- **Feature Parameters:** Input fields above each Execute button (dropdowns, color pickers, text inputs, etc.)

**User Workflow:**
1. **Create Dashboard** → Name it "Main Stream"
2. **Add Widget** → Select from the list of existing widgets, or instantiate a widget from the library (e.g. "ConfettiAlertWidget")
3. **(if new widget instantiated) Widget Auto-Creates Elements** → uses existing known assets: confetti_particle.png, pop.mp3 (defaults)
4. **Configure Widget** (optional):
   - Click "Widget Parameters" → Set blast_duration: 3.0s, particle_count: 150
   - Click "Elements" → Upload custom confetti.png, select different sound file
5. **Execute Features** → Click "Trigger Blast", set intensity to "High", click Execute
6. **Overlay Updates** → WebSocket broadcasts Element changes, overlay renders confetti explosion

**Dashboard Scenarios:**
- **"Starting Soon" Dashboard:** Countdown timer Widget, background music Widget, social media Widget
- **"Main Stream" Dashboard:** Alerts Widget, donation goal Widget, chat poll Widget, confetti Widget
- **"Break Screen" Dashboard:** BRB text Widget, timer Widget, playlist Widget
- **"Ending" Dashboard:** Thank you message Widget, highlight reel Widget, raid Widget

#### Architecture Summary

**Data Flow:**
```
Dashboard (UI Tab)
  └─ Contains Widget Instances (many-to-many)
      ├─ Widget Parameters (JSON config: durations, counts, defaults)
      ├─ Owns Elements (one-to-many)
      │   ├─ Element Properties (position, size, opacity, CSS)
      │   └─ Element Behavior (animations, triggers)
      └─ Provides Features (methods in Python class)
          └─ Feature Parameters (runtime inputs: dropdown, color-picker, etc.)

User executes Feature → Feature manipulates Elements → WebSocket broadcasts → Overlay renders
```

**Relationships:**
- **Dashboard ↔ Widget:** Many-to-many (same Widget instance on multiple Dashboards)
- **Widget → Element:** One-to-many (Widget owns Elements exclusively)
- **Widget → Feature:** One-to-many (Widget class defines Features as methods)
- **Element → Widget:** Many-to-one (each Element belongs to exactly one Widget)

**Key Design Decisions:**
1. **Element Ownership:** Elements cannot be shared between Widgets (prevents state conflicts)
2. **Element Name Immutability:** Element names are permanent and unique within each Widget
   - Widget features use hardcoded element names for reliability
   - Database constraint enforces `UniqueConstraint('widget_id', 'name')`
   - Admin UI prevents name editing (read-only display)
3. **Widget Reusability:** Same Widget instance can appear on multiple Dashboards (convenience without duplication)
4. **Widget Instantiation:** Users can create multiple instances of same Widget type (separate configurations)
5. **Feature Immutability:** Features are defined in code, not configurable by users (ensures reliability)
6. **Parameter Separation:** Widget Parameters (config) vs Feature Parameters (runtime) - clear distinction
7. **Backward Compatibility:** Existing Elements in database are orphaned (delete or manually associate with Widgets)


### Use Cases
The Widget/Feature system enables a wide variety of stream overlay scenarios:

**Alert Widgets:**
- **Follower Alert** - Shows animated graphic and plays sound when someone follows
  - Features: trigger_alert (params: follower_name)
- **Donation Alert** - Displays donor name, amount, and custom message
  - Features: show_donation (params: donor_name, amount, message, duration)
- **Subscriber Alert** - Celebrates new subscriptions with confetti and sound
  - Features: trigger_sub (params: subscriber_name, tier, months)

**Interactive Widgets:**
- **Poll Widget** - Display live poll results from chat
  - Features: start_poll (params: question, options), end_poll, reset_poll
- **Wheel Spinner** - Random selection wheel for giveaways
  - Features: add_option (params: text), spin_wheel, reset_wheel
- **Goal Tracker** - Visual progress bar for donation/follower goals
  - Features: add_progress (params: amount), set_goal (params: target), reset_goal

**Media Widgets:**
- **Image Sequence** - Animate through a series of images
  - Features: start_sequence, pause_sequence, next_image, previous_image
- **Video Player** - Play video clips on overlay
  - Features: play_video (params: video_file), stop_video, pause_video
- **Sound Board** - Trigger sound effects
  - Features: play_sound (params: sound_file, volume), stop_all_sounds

**Information Widgets:**
- **Countdown Timer** - Display countdown to stream start or event
  - Features: start_timer (params: duration), pause_timer, reset_timer
- **Text Ticker** - Scrolling text announcements
  - Features: set_text (params: message), start_scroll, stop_scroll
- **Social Media Display** - Show latest tweet, Discord message, etc.
  - Features: update_content (params: platform, content), cycle_platforms

**Game Integration Widgets:**
- **Current Game Display** - Show game title and box art
  - Features: set_game (params: game_name, image), clear_game
- **Death Counter** - Track in-game deaths
  - Features: increment_deaths, decrement_deaths, reset_counter
- **Split Timer** - Speedrun split display
  - Features: start_splits, next_split, reset_splits

**Example Workflow - Setting Up Stream Alerts:**
1. Create Dashboard: "Main Stream"
2. Add Widget: ConfettiAlertWidget → "Birthday Confetti"
   - Configure Elements: Upload custom birthday_confetti.png, birthday_song.mp3
   - Configure Widget Parameters: blast_duration=3.0s, particle_count=200
3. Add Widget: DonationGoalWidget → "Monthly Goal"
   - Configure Widget Parameters: goal_amount=500, bar_color="#4CAF50"
4. During Stream:
   - Viewer donates $50 → Click "Add Donation" feature, enter amount=50, donor_name="CoolViewer"
   - Widget updates progress bar, displays donor name
   - Goal reached → Click confetti "Trigger Blast" feature with intensity="High"

## Technical Architecture

### Core Technologies
- **Backend**: FastAPI ASGI web server (local-first)
  - Python 3.12+ with async/await
  - SQLAlchemy 2.0+ for async database access
  - SQLite for local data storage
  - Pydantic v2 for data validation
- **Real-time Communication**: 
  - FastAPI native WebSocket for real-time connections
  - Async broadcast to overlay clients
  - Element update streaming
- **Frontend Admin Interface**: Vue 3 Single-Page Application
  - Vue 3 (CDN) with vanilla JavaScript
  - Tailwind CSS for styling
  - Reactive state management
  - Real-time WebSocket connection
- **Frontend Overlay System**:
  - Vanilla JavaScript (HTML + JS)
  - WebSocket client for live updates
  - GSAP/Anime.js for advanced animations
  - Efficient DOM rendering
- **OBS Integration**: 
  - Browser Source pointing to local overlay endpoint
  - 1920x1080 canvas (configurable)
  - Transparent background support
  - Hardware acceleration compatible

#### System Architecture

**Component Interaction:**
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Dashboard     │  HTTP   │   FastAPI        │  WS     │   Overlay       │
│   (Vue Admin)   │◄───────►│   Backend        │◄───────►│   (Browser)     │
│                 │         │                  │         │                 │
│ - Create Widgets│         │ - Widget Classes │         │ - Render        │
│ - Execute Feats │         │ - Feature Methods│         │   Elements      │
│ - Configure     │         │ - DB Management  │         │ - Animations    │
└─────────────────┘         │ - WebSocket Hub  │         └─────────────────┘
                            │                  │
                            │  ┌────────────┐  │
                            │  │  SQLite    │  │
                            │  │  Database  │  │
                            │  │            │  │
                            │  │ - Dashboards│ │
                            │  │ - Widgets   │ │
                            │  │ - Elements  │ │
                            │  └────────────┘  │
                            └──────────────────┘
```

**Data Models:**

```python
# Core Database Models

class Dashboard(Base):
    """Organizational tab in admin interface"""
    id: int
    name: str
    is_active: bool  # Only one active at a time
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    widgets: List[Widget]  # Many-to-many

class Widget(Base):
    """Instantiated widget with configuration"""
    id: int
    widget_class: str  # "ConfettiAlertWidget", "DonationGoalWidget"
    name: str  # User-given name: "My Birthday Confetti"
    widget_parameters: dict  # JSON: {blast_duration: 2.5, particle_count: 100}
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    dashboards: List[Dashboard]  # Many-to-many (shared state)
    elements: List[Element]  # One-to-many (owned)

class Element(Base):
    """Media asset or display component owned by Widget"""
    id: int
    widget_id: int  # Foreign key (belongs to one Widget)
    element_type: ElementType  # IMAGE, VIDEO, AUDIO, TEXT, TIMER, COUNTER, ANIMATION
    name: str  # Identifier within widget: "confetti_particle", "pop_sound" (immutable after creation)
    properties: dict  # JSON: {media_roles: ["image", "sound"], position: {x, y, z_index}, size: {width, height}, opacity: 1.0}
    behavior: dict  # JSON: {entrance: {type, duration}, exit: {type, duration}}
    visible: bool  # Whether element is currently displayed
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    media_assets: List[ElementAsset]  # Many-to-many with Media (role-based)
```

**Widget Class Structure:**

```python
# Base widget class that all widgets inherit from

class BaseWidget(ABC):
    """Abstract base for all widget types"""
    
    # Class metadata (overridden by subclasses)
    widget_class: str  # Unique identifier
    display_name: str  # Human-readable name
    description: str  # Description for widget library
    
    # Instance data
    db_widget: Widget  # Database record
    widget_parameters: dict  # Configuration
    elements: Dict[str, Element]  # Owned elements by name
    
    @classmethod
    async def create(cls, db: Session, name: str, 
                     widget_parameters: dict = None) -> 'BaseWidget':
        """Create new widget instance with default elements"""
        pass
    
    @abstractmethod
    async def create_default_elements(self):
        """Subclasses define which elements to create"""
        pass
    
    @classmethod
    def get_features(cls) -> List[dict]:
        """Extract feature metadata from decorated methods"""
        pass
    
    async def execute_feature(self, feature_name: str, 
                              feature_params: dict):
        """Execute a named feature with parameters"""
        pass

# Feature decorator for marking widget methods
@feature(
    display_name="Trigger Confetti Blast",
    parameters=[
        {"name": "intensity", "type": "dropdown", 
         "options": ["Low", "Medium", "High"], "optional": False},
        {"name": "color", "type": "color-picker", 
         "optional": True, "default": "#FF5733"}
    ]
)
async def trigger_blast(self, intensity: str, color: str = "#FF5733"):
    """Feature implementation"""
    # Manipulate self.elements
    # Broadcast updates via WebSocket
    pass
```

**Widget Registry:**

All widget classes are registered in a central registry for discovery:

```python
# Widget classes are registered at import time
WIDGET_REGISTRY = {
    "ConfettiAlertWidget": ConfettiAlertWidget,
    "DonationGoalWidget": DonationGoalWidget,
    "PollWidget": PollWidget,
    # ... more widgets
}

# API can list available widgets
GET /api/widget-types/ 
→ Returns list of all widget classes with metadata

# API can create widget instances
POST /api/widgets/
{
    "widget_class": "ConfettiAlertWidget",
    "name": "My Confetti",
    "widget_parameters": {...},
    "dashboard_ids": [1, 3]
}
```

#### Web Server (FastAPI Application)
- Serves admin interface (Dashboard UI) and overlay endpoints
- RESTful API with OpenAPI documentation at `/api/docs`
- WebSocket server for real-time Element updates
- Async media file serving with range request support (video streaming)
- Multi-route system:
  - `/` - API status and health checks
  - `/api/dashboards/*` - Dashboard CRUD operations
  - `/api/widgets/*` - Widget instance management
  - `/api/widget-types/*` - List available widget classes
  - `/api/media/*` - Media library upload/list/delete
  - `/ws` - WebSocket connection for overlay updates
  - `/admin` - Admin interface (Vue 3 SPA)
  - `/overlay` - Overlay display (HTML/JS)
  - `/shared` - Shared frontend components
  - `/uploads` - User-uploaded media files

**Key API Endpoints:**

```
# Dashboard Management
GET    /api/dashboards/              List all dashboards
POST   /api/dashboards/              Create new dashboard
GET    /api/dashboards/{id}          Get dashboard details
PATCH  /api/dashboards/{id}          Update dashboard
DELETE /api/dashboards/{id}          Delete dashboard
POST   /api/dashboards/{id}/activate Set as active dashboard

# Widget Management
GET    /api/widget-types/            List available widget classes with metadata
POST   /api/widgets/                 Create widget instance
GET    /api/widgets/{id}             Get widget details (includes elements, features)
PATCH  /api/widgets/{id}             Update widget parameters
DELETE /api/widgets/{id}             Delete widget (and owned elements)
POST   /api/widgets/{id}/execute     Execute a widget feature
POST   /api/widgets/{id}/elements    Create/update elements for this widget

# Elements are owned and managed by Widgets
# Element data is included in Widget responses
# Element updates happen through Widget configuration and Feature execution

# Element Management
# Elements are managed exclusively through their owning Widgets
# Use Widget endpoints to view/configure Elements

# Media Library
POST   /api/media/upload             Upload image/video/audio file
GET    /api/media/                   List uploaded media with filtering
GET    /api/media/{filename}         Serve media file
DELETE /api/media/{filename}         Delete media file

# WebSocket Events
Connection: /ws?client_type=overlay
Events:
  - element_update: Element visibility/properties changed
  - dashboard_activated: New dashboard set as active
  - dashboard_deactivated: Previous dashboard deactivated
```

**WebSocket Protocol:**

Overlay clients connect via WebSocket to receive real-time updates:

```javascript
// Overlay connects
const ws = new WebSocket('ws://localhost:8002/ws?client_type=overlay');

// Server sends element updates when features execute
{
    "type": "element_update",
    "action": "update",  // or "show", "hide", "delete"
    "element": {
        "id": 42,
        "widget_id": 5,
        "element_type": "image",
        "name": "confetti_particle",
        "media_assets": [{"media_id": 7, "role": "image"}],
        "media_details": [{
            "id": 7,
            "filename": "confetti.png",
            "url": "/uploads/confetti.png",
            "role": "image",
            "mime_type": "image/png"
        }],
        "properties": {
            "media_roles": ["image"],  // Defines allowed media roles
            "position": {"x": 100, "y": 100, "z_index": 10},
            "size": {"width": 50, "height": 50},
            "opacity": 1.0
        },
        "behavior": {
            "entrance": {"type": "explosion", "duration": 2.5},
            "exit": {"type": "fade", "duration": 0.5}
        },
        "visible": true
    }
}

// Dashboard activation events
{
    "type": "dashboard_activated",
    "dashboard_id": 3
}
{
    "type": "dashboard_deactivated",
    "dashboard_id": 1
}
```
#### Overlay Rendering System

The overlay is a lightweight web page (HTML + JavaScript) that connects to the backend via WebSocket and renders Elements based on their current state.

**Overlay Responsibilities:**
- Maintain WebSocket connection to `/ws?client_type=overlay`
- Listen for `element_update` events
- Render Elements according to their `properties` and `behavior`
- Handle element animations (entrance/exit effects)
- Provide standard library for media playback:
  - Image rendering with transforms
  - Video playback with controls
  - Audio playback (background or triggered)
  - Text rendering with custom fonts/styling
  - Timer/counter displays
  - Particle effects and animations

**Overlay Requirements:**
- Must handle Elements with no media assigned (unconfigured) without errors
- Must support role-based media rendering (multiple media per element)
- Must respect `visible` flag for rendering
- Must apply `properties` (position, size, opacity, CSS)
- Must execute `behavior` animations (entrance, exit, loops)
- Must efficiently update only changed Elements (not full re-render)
- Must eagerly load all media for snappy playback (no lazy loading)

**Overlay Implementation:**

```javascript
// overlay.html - Simple example

const elements = new Map(); // element_id -> {element, domNode}
const ws = new WebSocket('ws://localhost:8002/ws?client_type=overlay');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'element_update') {
        handleElementUpdate(data.element, data.action);
    }
    
    if (data.type === 'dashboard_deactivated') {
        // Hide all elements efficiently
        elements.forEach(({domNode}) => domNode.classList.add('hidden'));
    }
};

function handleElementUpdate(element, action) {
    if (action === 'delete') {
        removeElement(element.id);
        return;
    }
    
    if (!elements.has(element.id)) {
        createElement(element);
    } else {
        updateElement(element);
    }
    
    // Handle visibility
    const {domNode} = elements.get(element.id);
    if (element.visible && element.enabled) {
        showElement(domNode, element.behavior.entrance);
    } else {
        hideElement(domNode, element.behavior.exit);
    }
}

function createElement(element) {
    const container = document.createElement('div');
    container.className = 'element';
    container.id = `element-${element.id}`;
    
    // Get media from media_details array
    const mediaUrls = element.media_details || [];
    
    switch (element.element_type) {
        case 'image':
            const imageMedia = mediaUrls.find(m => m.mime_type?.startsWith('image/'));
            if (imageMedia) {
                const img = document.createElement('img');
                img.src = imageMedia.url;
                img.dataset.role = imageMedia.role;
                container.appendChild(img);
            }
            break;
        case 'video':
            const videoMedia = mediaUrls.find(m => m.mime_type?.startsWith('video/'));
            if (videoMedia) {
                const video = document.createElement('video');
                video.src = videoMedia.url;
                video.dataset.role = videoMedia.role;
                video.autoplay = element.properties?.autoplay !== false;
                container.appendChild(video);
            }
            break;
        case 'audio':
            const audioMedia = mediaUrls.find(m => m.mime_type?.startsWith('audio/'));
            if (audioMedia) {
                const audio = document.createElement('audio');
                audio.src = audioMedia.url;
                audio.dataset.role = audioMedia.role;
                audio.volume = element.properties?.volume ?? 1.0;
                container.appendChild(audio);
            }
            break;
        case 'text':
            const textDiv = document.createElement('div');
            textDiv.className = 'element-text';
            textDiv.textContent = element.properties?.text || '';
            container.appendChild(textDiv);
            break;
        // ... more types
    }
    
    return container;
    
    applyProperties(domNode, element.properties);
    document.body.appendChild(domNode);
    elements.set(element.id, {element, domNode});
}

function applyProperties(domNode, properties) {
    // Apply position
    domNode.style.position = 'absolute';
    domNode.style.left = properties.position?.x + 'px' || '0px';
    domNode.style.top = properties.position?.y + 'px' || '0px';
    domNode.style.zIndex = properties.position?.z_index || 1;
    
    // Apply size
    if (properties.size) {
        domNode.style.width = properties.size.width + 'px';
        domNode.style.height = properties.size.height + 'px';
    }
    
    // Apply opacity
    domNode.style.opacity = properties.opacity ?? 1.0;
    
    // Apply custom CSS
    if (properties.css) {
        Object.assign(domNode.style, properties.css);
    }
}

function showElement(domNode, entrance) {
    // Use GSAP/Anime.js or CSS animations based on entrance.type
    if (entrance?.type === 'fade') {
        domNode.style.transition = `opacity ${entrance.duration}s`;
        domNode.style.opacity = 1;
    }
    // ... more animation types
}
```

**Overlay Does NOT Need to Know:**
- Widget structure or configuration
- Feature definitions or parameters
- Dashboard organization
- Business logic

**Overlay ONLY Knows:**
- Elements and their properties
- How to render different element types
- How to animate based on behavior definitions

#### Chat Platform Integration (Future Enhancement)

Chat integration will extend the Feature execution model to support triggers from multiple platforms.

**Planned Architecture:**
- **Multi-Platform Support**:
  - Unified chat interface layer
  - Platform-specific adapters (Twitch, YouTube, Discord)
  - Extensible platform registration
  - Cross-platform event normalization
- **Feature Execution from Chat**:
  - Chat commands map to Widget Features
  - Example: `!confetti high red` → executes `ConfettiAlertWidget.trigger_blast(intensity="High", color="#FF0000")`
  - Permission system (mod-only features, subscriber features, etc.)
- **Event Triggers**:
  - Platform events (new follower, donation, subscription) automatically execute Features
  - Example: New follower → DonationGoalWidget.add_progress(amount=1)
- **Integration Layer**:
  - Async platform clients (twitchio, discord.py, YouTube Chat API)
  - Unified event bus connecting chat platforms to Widget Feature execution
  - State tracking across platforms

This design keeps the Feature model platform-agnostic while enabling rich chat integration.

### System Requirements 
#### Deployment and development
- Local Python environment (3.12+)
- Local storage for media assets (SSD recommended)
- Network access for localhost WebSocket connections
- Modern web browser support in OBS (Chromium-based)

#### Backend
Core Framework
- Python 3.12+ (recommended for production stability and async performance)
- FastAPI (ASGI web framework with OpenAPI docs and WebSocket support)
- Uvicorn (ASGI server for running FastAPI applications)
- Pydantic v2 (data validation and settings management)

Database & Storage
- SQLAlchemy 2.0+ (async ORM)
- aiosqlite (async SQLite driver)
- SQLite (local database for configurations and state)
- aiofiles (async file I/O for media assets)

Real-time Communication
- FastAPI WebSocket (native async WebSocket support)

Media Processing
- Pillow (image manipulation and optimization)
- ffmpeg-python (video/audio processing via FFmpeg) [optional]

Development Tools (optional)
- pytest + pytest-asyncio (async testing framework)
- ruff (fast linter and formatter)
- mypy (static type checking)

### Feature Specifications

#### Media Library
- Upload and manage media assets (images, videos, audio)
- File type validation (PNG, JPEG, GIF, WebP, SVG, MP4, WebM, MOV, MP3, WAV, OGG)
- File size limits (100MB default)
- Automatic unique filename generation
- Media browser with filtering by type
- Drag-and-drop upload interface
- Integration with Element configuration (select media for Elements)

#### Media Rendering
- Support for common image formats (PNG, JPEG, GIF, WebP, SVG)
- Video playback with streaming support (MP4, WebM, MOV)
- Audio playback with volume control (MP3, WAV, OGG)
- Media preloading for smooth transitions
- Role-based media assignment (elements can have multiple media with different roles)
- Fallback rendering for unconfigured Elements (no media assigned)
- Eager loading philosophy: All media loaded proactively for snappy playback

#### Animation Features
- Element-level animations via `behavior` property
- Entrance effects (fade, slide, scale, explosion, etc.)
- Exit effects (fade, slide, shrink, etc.)
- CSS transition support
- GSAP/Anime.js integration for advanced sequences
- Timing control via Widget Parameters
- Custom animation sequences defined in Widget Features

#### Management Interface (Dashboard UI)
- Modern Vue 3 (CDN) + Tailwind CSS interface
- Tab-based Dashboard organization
- Widget management panels:
  - Feature execution with parameter inputs
  - Widget Parameter configuration dialog
  - Element list and configuration dialog
- Media library browser
- Live preview of overlay
- Real-time WebSocket connection status
- Drag-and-drop Widget organization

#### Widget Library
- Pre-built Widgets for common use cases:
  - Alert Widgets (follower, donation, subscription)
  - Interactive Widgets (polls, wheels, timers)
  - Media Widgets (image sequences, video players, sound boards)
  - Information Widgets (goals, tickers, social media displays)
- Custom Widget creation via Python classes
- Widget metadata (display name, description, default parameters)
- Feature discovery via decorators
- Automatic Element creation with defaults

## Technical Requirements

### System Requirements
- Python 3.12+ (recommended for production stability and async performance)
- Modern web browser support in OBS (Chromium-based, Edge/Chrome recommended)
- Local storage for media assets (SSD recommended, minimum 10GB)
- Network access for WebSocket connections (localhost)
- Optional: Docker for isolated deployment

### Dependencies

#### Backend (Python)
- FastAPI 0.121+ (ASGI web framework)
- Uvicorn 0.38+ (ASGI server with hot reload)
- SQLAlchemy 2.0+ (async ORM)
- aiosqlite 0.21+ (async SQLite driver)
- Pydantic 2.12+ (data validation and settings)
- python-multipart 0.0.20+ (file upload handling)
- aiofiles 25.1+ (async file I/O)

#### Frontend Admin Interface
- Vue 3 (CDN)
- Tailwind CSS (CDN)
- Native WebSocket API

#### Frontend Overlay
- Vanilla JavaScript or lightweight Vue 3
- GSAP or Anime.js for animations
- WebSocket API (native browser support)

### Backend Application Architecture

The application follows a **layered architecture** that separates concerns and promotes maintainable, testable code:

```
┌──────────────────────────────────────────────────────────┐
│                        Clients                           │
│           (Admin UI, Overlay, External Apps)             │
└────────────┬─────────────────────────────────────────────┘
             │ HTTP/WebSocket
┌────────────▼─────────────────────────────────────────────┐
│                     API Layer (FastAPI)                  │
│  - Request/response handling                             │
│  - Input validation (Pydantic schemas)                   │
│  - Authentication/authorization (future)                 │
│  - Serialization (centralized in serializers.py)         │
│  - WebSocket connection management                       │
└────────────┬─────────────────────────────────────────────┘
             │ Orchestrates
┌────────────▼─────────────────────────────────────────────┐
│                   Service Layer                          │
│  - Business logic orchestration                          │
│  - Cross-model validation                                │
│  - Complex operations (media assignment, etc.)           │
│  - DOES NOT commit transactions (caller controls)        │
└────────────┬─────────────────────────────────────────────┘
             │ Uses
┌────────────▼─────────────────────────────────────────────┐
│                 Repository Layer                         │
│  - Pure data access (queries, creates, updates)          │
│  - Automatic eager loading (no N+1 queries)              │
│  - Entity-level validation (e.g., role validation)       │
│  - DOES NOT commit transactions (caller controls)        │
└────────────┬─────────────────────────────────────────────┘
             │ Uses
┌────────────▼─────────────────────────────────────────────┐
│                   Widget Layer                           │
│  - Widget-first programming model                        │
│  - Direct ORM access for element creation                │
│  - Feature execution and element manipulation            │
│  - Uses service layer for shared operations              │
│  - Broadcasts WebSocket events (after committing)        │
└────────────┬─────────────────────────────────────────────┘
             │ Interacts with
┌────────────▼─────────────────────────────────────────────┐
│               Database Layer (SQLAlchemy)                │
│  - ORM models (Dashboard, Widget, Element, Media, etc.)  │
│  - Async session management                              │
│  - Relationship definitions with eager loading           │
└──────────────────────────────────────────────────────────┘
```

#### Layer Responsibilities

**API Layer** (`app/api/`)
- **Purpose**: HTTP/WebSocket interface for clients
- **Responsibilities**:
  - Route definitions and request handling
  - Input validation using Pydantic schemas
  - Calling services and repositories
  - Controlling transactions (commits)
  - Error handling and HTTP responses
  - Serialization via `serializers.py` (single source of truth)
  - WebSocket event broadcasting
- **Key Files**:
  - `dashboards.py` - Dashboard CRUD and activation
  - `widgets.py` - Widget CRUD and feature execution  
  - `media.py` - Media upload/list/serve/delete
  - `serializers.py` - Centralized ORM→dict conversion
  - `websocket.py` - WebSocket connection management

**Service Layer** (`app/services/`)
- **Purpose**: Business logic orchestration
- **Responsibilities**:
  - Complex operations requiring multiple models
  - Cross-entity validation (e.g., media role validation)
  - Shared logic used by both API and widgets
  - Does NOT commit transactions (caller controls)
- **Key Files**:
  - `element_service.py` - Media assignment with validation
- **Example**:
  ```python
  # Service does NOT commit - caller controls transaction
  async def assign_media(
      self, element: Element, media_id: int, 
      role: str, db: AsyncSession
  ) -> ElementAsset:
      # Validate role exists in element's media_roles
      # Check media exists in database
      # Clear old assignment for this role
      # Create new ElementAsset
      # DO NOT commit - caller will commit
      return element_asset
  ```

**Repository Layer** (`app/repositories/`)
- **Purpose**: Pure data access with automatic eager loading
- **Responsibilities**:
  - Database queries (get, list, create, update, delete)
  - Automatic eager loading of relationships (no N+1 queries)
  - Entity-level validation (e.g., valid media roles)
  - Does NOT commit transactions (caller controls)
- **Philosophy**: RAM over latency - proactively load relationships for snappy interfaces
- **Key Files**:
  - `element_repository.py` - Element queries with auto-loaded media
  - `widget_repository.py` - Widget queries
  - `media_repository.py` - Media queries
- **Example**:
  ```python
  # Repository always eager loads relationships
  async def get_by_id(self, element_id: int, db: AsyncSession) -> Element:
      result = await db.execute(
          select(Element)
          .options(
              selectinload(Element.media_assets)
              .selectinload(ElementAsset.media)
          )
          .where(Element.id == element_id)
      )
      return result.scalar_one_or_none()
  ```

**Widget Layer** (`app/widgets/`)
- **Purpose**: Widget-first programming model for extensibility
- **Responsibilities**:
  - Element lifecycle management (`create_default_elements()`)
  - Feature definitions using `@feature` decorator
  - Feature execution (manipulate elements)
  - Uses service layer for shared operations (media assignment)
  - Direct ORM access for element creation (widget-first design)
  - Broadcasts WebSocket events AFTER committing
- **Philosophy**: Widgets are the primary extension point - developers add functionality by creating widgets
- **Key Files**:
  - `base.py` - BaseWidget abstract class
  - `alert.py` - Example AlertWidget implementation
- **Example**:
  ```python
  class AlertWidget(BaseWidget):
      async def create_default_elements(self):
          """Direct ORM - widget owns element lifecycle"""
          image = Element(
              widget_id=self.db_widget.id,
              name="alert_image",  # Immutable after creation
              element_type=ElementType.IMAGE,
              properties={"media_roles": ["image"]},
              behavior={"entrance": {"type": "fade", "duration": 1.0}}
          )
          self.db.add(image)
          self.elements["alert_image"] = image
          # DO NOT commit - BaseWidget.create() handles it
      
      @feature(display_name="Show Alert", parameters=[...])
      async def show_alert(self, message: str):
          """Feature execution - commit BEFORE broadcast"""
          alert = self.get_element("alert_image")
          alert.visible = True
          alert.properties["text"] = message
          
          # Commit FIRST to ensure database consistency
          await self.db.commit()
          
          # Broadcast AFTER commit
          await self.broadcast_element_update(alert, action="show")
  ```

**Database Layer** (`app/models/`)
- **Purpose**: SQLAlchemy ORM models and relationships
- **Responsibilities**:
  - Model definitions with declarative base
  - Relationship configurations (eager loading strategy)
  - Cascade delete rules
  - Database constraints (uniqueness, foreign keys)
- **Key Files**:
  - `base.py` - Declarative base
  - `dashboard.py` - Dashboard model
  - `widget.py` - Widget model
  - `element.py` - Element model with media_assets relationship

#### Critical Patterns

**Transaction Control**
- **Rule**: Caller controls commits (repositories and services do NOT commit)
- **Rationale**: Enables atomic multi-step operations
- **Pattern**:
  ```python
  # API endpoint controls commit
  @router.patch("/widgets/{widget_id}/elements/{element_id}")
  async def update_element(element_id: int, updates: ElementUpdate):
      element = await element_repo.get_by_id(element_id, db)
      await element_service.assign_multiple_media(element, updates.media, db)
      # Commit BEFORE broadcasting to prevent race conditions
      await db.commit()
      await websocket_manager.broadcast_element_update(element, "update")
      return serialize_element_detail(element)
  ```

**Commit Before Broadcast**
- **Rule**: Always commit database changes BEFORE broadcasting WebSocket events
- **Rationale**: Prevents race conditions where overlay queries database before commit
- **Pattern**: Update → Commit to DB → Broadcast to overlay

**Eager Loading Philosophy**
- **Rule**: Always eager load relationships (RAM over latency)
- **Rationale**: Prevents N+1 queries, enables snappy UI, simplifies code
- **Implementation**: Repositories use `selectinload()` automatically
- **Critical for Elements**: Must load `media_assets` → `media` to prevent greenlet errors

**Centralized Serialization**
- **Rule**: Single source of truth in `api/serializers.py`
- **Rationale**: Prevents duplication, ensures consistency
- **Usage**: Used by both API endpoints and WebSocket manager
- **Helper**: `_build_media_arrays()` extracts `media_assets` and `media_details`

**Widget-First Development**
- **Rule**: Widgets are the primary extension point for functionality
- **Rationale**: Developers focus on widget development to expand capabilities
- **Pattern**: Widgets use direct ORM for element creation, service layer for shared operations
- **Element Names**: Immutable after creation - widgets rely on stable names

### Performance Considerations
- **WebSocket Efficiency**: Binary protocol for large payloads, JSON for control messages
- **Media Optimization**: 
  - Pre-loading of media assets for instant rendering
  - Range request support for video streaming
  - Image compression and format optimization (WebP recommended)
- **Memory Management**:
  - Inactive Dashboard widgets stay in memory but with hidden Elements
  - Overlay efficiently updates only changed Elements (differential updates)
  - DOM element reuse when possible
  - Eager loading trades memory for latency (snappy interfaces)
- **Rendering Optimization**:
  - CSS transforms for animations (GPU acceleration)
  - RequestAnimationFrame for smooth animations
  - Virtual DOM or efficient DOM diffing
  - Debounced WebSocket handlers
- **Query Optimization**:
  - Repository pattern eliminates N+1 queries
  - Automatic eager loading of relationships
  - Centralized query logic for consistency


## Security Considerations
- **Local-Only Design**: Server binds to 127.0.0.1 by default (no external access)
- **File Upload Validation**: 
  - MIME type verification
  - File extension whitelist
  - Size limits (100MB default)
  - Directory traversal prevention
- **Input Sanitization**:
  - Pydantic validation for all API inputs
  - SQL injection protection via SQLAlchemy ORM
  - XSS prevention in overlay rendering
- **Future Enhancements**:
  - API key authentication for external feature triggers
  - Rate limiting for chat-triggered features
  - User permissions system for multi-streamer setups

## Development Setup

### Prerequisites
- Python 3.12 or higher
- uv package manager (recommended) or pip
- Modern web browser (Chrome, Edge, Firefox)

### Installation

```powershell
# Clone repository
git clone https://github.com/strugglin-here/stream-companion.git
cd stream-companion

# Install uv (if not already installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work for local development)
```

### Running the Server

```powershell
# Using uv (recommended)
uv run python run.py

# Or activate virtual environment manually
.venv\Scripts\Activate.ps1
python run.py
```

Server will start at http://127.0.0.1:8002

**Available Endpoints:**
- http://127.0.0.1:8002/api/docs - Interactive API documentation
- http://127.0.0.1:8002/admin/ - Admin interface
- http://127.0.0.1:8002/overlay/ - Main overlay (add to OBS)
- http://127.0.0.1:8002/overlay/test-overlay.html - WebSocket test client

### Development Tools

```powershell
# Run with hot reload (watches app/ and data/ directories)
uv run python run.py

# Run tests (when implemented)
uv run pytest

# Lint code
uv run ruff check app/

# Format code
uv run ruff format app/

# Type checking (optional)
uv run mypy app/
```

### Adding a New Widget

1. Create widget class in `app/widgets/`:

```python
# app/widgets/my_widget.py
from app.widgets.base import BaseWidget, feature, register_widget
from app.models.element import Element, ElementType

@register_widget
class MyCustomWidget(BaseWidget):
    widget_class = "MyCustomWidget"
    display_name = "My Custom Widget"
    description = "Does something cool"
    
    @classmethod
    def get_default_parameters(cls) -> dict:
        return {
            "duration": 2.0,
            "color": "#FF5733"
        }
    
    async def create_default_elements(self):
        # Create elements with defaults
        element = Element(
            widget_id=self.db_widget.id,
            element_type=ElementType.IMAGE,
            name="my_image",
            properties={
                "media_roles": ["image"],  # Define allowed media roles
                "position": {"x": 100, "y": 100}
            },
            behavior={},
            visible=False
        )
        self.db.add(element)
        self.elements["my_image"] = element
        # DO NOT commit - parent BaseWidget.create() handles it
    
    @feature(
        display_name="Do Something Cool",
        parameters=[
            {"name": "intensity", "type": "dropdown", 
             "options": ["Low", "High"], "optional": False}
        ]
    )
    async def do_something(self, intensity: str):
        # Manipulate elements
        element = self.elements['my_image']
        element.visible = True
        await self.db.commit()
        await self.broadcast_element_update(element)
```

2. Import in `app/widgets/__init__.py`:
```python
from .my_widget import MyCustomWidget
```

3. Widget is now available via API at `/api/widget-types/`

## Deployment

### Single-Instance Local Deployment

The application is designed to run on the streamer's local machine:

```powershell
# Production mode (no hot reload)
$env:DEBUG="false"
uv run python run.py
```

### Backup Strategy

**Critical Data:**
- `data/stream_companion.db` - All Dashboards, Widgets, Elements
- `data/media/` - Uploaded media files


### OBS Setup

1. Add Browser Source in OBS
2. URL: `http://127.0.0.1:8002/overlay/`
3. Width: 1920, Height: 1080
4. Custom CSS (optional): `body { background-color: transparent; }`
5. Check "Shutdown source when not visible" for performance

## Roadmap

### Current Status (MVP)
- ✅ Element CRUD with properties/behavior
- ✅ WebSocket real-time updates
- ✅ Media upload and library
- ✅ Simple overlay renderer

### Phase 1: Widget System
- ⏳ Dashboard model and API
- ⏳ Widget base class and registry
- ⏳ Feature decorator and execution
- ⏳ Example widgets (Confetti, Donation Goal, Poll)
- ⏳ Enhanced overlay with element type rendering

### Phase 2: Admin Interface
- ⏳ Vue 3 + Vuetify dashboard UI
- ⏳ Widget management panels
- ⏳ Feature execution with parameter inputs
- ⏳ Media library integration
- ⏳ Live overlay preview

### Phase 3: Advanced Features
- ⏳ GSAP animation integration
- ⏳ Complex widget behaviors
- ⏳ Widget import/export
- ⏳ Dashboard templates

### Phase 4: External Integration
- ⏳ Chat platform integration (Twitch, YouTube, Discord)
- ⏳ Feature execution via chat commands
- ⏳ Platform event triggers
- ⏳ OBS WebSocket integration

## Contributing

This project is under active development. Join the stream on Wednesdays ~10AM PST to contribute ideas and watch development live!

- YouTube: [@strugglin_here](https://www.youtube.com/@strugglin_here/streams)
- Twitch: [twitch.tv/strugglin_here](https://www.twitch.tv/strugglin_here)
- GitHub: [github.com/strugglin-here/stream-companion](https://github.com/strugglin-here/stream-companion)

## License

[To be determined]
