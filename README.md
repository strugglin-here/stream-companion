# Stream Companion - OBS Web Overlay System

## Project Overview
This project creates a web overlay, hosted locally, which can be used as an OBS browser source to enhance the panache of your stream.

The project also cerates a web admin portal where the overlay can be managed and controlled live.

### Design principles
Simplicity, ease of use, power, and fun.

### Use cases
One or more of the following, possibly chained in sequence together:
- creating a sequence of images animated across the screen
- playing predefined sounds, or capturing from the mic and using that as a source
- triggering any sequence by a chat event or a button press in the admin panel

## Technical Architecture

### Core Technologies
- **Backend**: FastAPI ASGI web server (local-first)
- **Frontend**: Vue 3 Single-App Architecture
  - Base Layer: Vue 3 + Vite + TypeScript
  - State Management: Pinia for reactive state
  - Real-time Updates: socket.io-client (async)
  - Advanced Animations: GSAP/Anime.js
- **WebSocket**: Native ASGI WebSocket (python-socketio async)
- **Database**: SQLite (local) with async access
- **OBS Integration**: Leverage OBS 'browser source' to point at the local overlay endpoint
  - Real-time Updates: socket.io-client
  - Advanced Animations: GSAP/Anime.js

#### Web Server (FastAPI Application)
- Serves dynamic web content for OBS browser sources via ASGI
- Serves a local management interface for component configuration and live operation
- Native WebSocket support for real-time overlay updates
- Async asset serving (images, videos, sounds) for low-latency previews
- OpenAPI-documented REST endpoints with Pydantic validation
- Multi-route system:
  - `/overlay/*` - OBS-facing overlay endpoints
  - `/manage/*` - Component management interface
  - `/api/*` - REST API endpoints for external control
- Handles WebSocket connections for real-time updates
- Manages asset serving (images, videos, sounds)
#### Chat Platform Integration
- **Multi-Platform Support**:
  - Unified chat interface layer
  - Platform-specific adapters (Twitch, YouTube, Discord)
  - Extensible platform registration
  - Cross-platform event normalization
- **Message Processing**:
  - Unified message queue
  - Platform-agnostic command system
  - Common emote/badge handling
  - Cross-platform user identity
- **Event Architecture**:
  - Standardized event system
  - Platform-specific event adapters
  - Unified alert triggers
  - Common reward mapping
- **Integration Layer**:
  - Async platform clients
  - Platform connection management
  - Unified state tracking
  - Shared resource handling

### System Requirements 
#### Deployment and development
- Docker for isolated local deployment
  - `/api/*` - REST API endpoints for external control
- Local storage for media assets (SSD recommended)
- Network access for Twitch integration (for chat/events)
- Modern web browser support in OBS (Chromium-based)

#### Development also requires
- Python 3.11+ (recommended for modern async features)


### Dependencies
#### Backend
- FastAPI
- Uvicorn (ASGI server)
- python-socketio[async] (async WebSocket support)
- twitchio (async Twitch integration)
- Pillow (Python Imaging Library)
- aiosqlite or SQLModel (async SQLite access)
- aiofiles (async file operations)
- Pydantic (data validation)
- Optional: fastapi-admin (optional admin UI)
  - Video file handling
  - Sound effect library
- Media queue system
## Development Setup
### Local Development (single-instance)
- Use Poetry or pip + venv for dependency management
- Pre-commit hooks for code quality (ruff, isort, black)
- Ruff for fast linting
- Pytest with pytest-asyncio for async tests
- Type checking with mypy (optional)
- Run the app locally with Uvicorn (hot reload during development)
- Use Docker Compose for optional isolation of services

### Quick local run (PowerShell)
```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
- Format validation and optimization

#### 4. Animation System
## Deployment (single-instance)
- The project is designed to run as a single process on the streamer machine.
- Recommended options:
  - Run as a systemd service (Linux) or Windows service / scheduled task.
  - Use Docker for isolation and portability; a single-container deployment is sufficient.
  - Keep backups of `data/` (SQLite DB) and `media/` (local assets).
- Vue Transition System:
  - Vue transition components for simple effects
  - CSS animations and transitions via Vue classes
  - Vue composition API hooks for animation control
- Timeline Animations:
  - GSAP/Anime.js integration for complex sequences
  - Synchronized audio/visual effects
  - Programmatic animation control via Vue refs
- Performance Optimizations:
  - Efficient state-driven animations
  - Debounced/throttled animation triggers

### Feature Specifications

#### Chat Integration
- **Platform Support**
  - Multi-platform chat aggregation (Twitch, YouTube, Discord)
  - Individual platform enabling/disabling
  - Platform-specific features when available
  - Easy addition of new platform support
- **Chat Display**
  - Real-time unified chat feed
  - Platform-aware message styling
  - Cross-platform emote support
  - Unified badge system
- **Command System**
  - Platform-agnostic command framework
  - Per-platform command customization
  - Permission system across platforms
  - Custom command creation interface
- **Moderation**
  - Cross-platform user tracking
  - Unified moderation actions
  - Platform-specific timeout/ban support
  - Shared block/allow lists
- **Event Handling**
  - Normalized subscription events
  - Cross-platform donation tracking
  - Unified reward system
  - Platform-agnostic alerts

#### Media Rendering
- Support for common image formats (PNG, JPEG, GIF, WebP)
- Video playback (MP4, WebM)
- Audio playback with volume control
- Media preloading for smooth transitions

#### Animation Features
- Text animations (fade, scroll, bounce, etc.)
- Image transforms (scale, rotate, move)
- Color effects (gradient, pulse, rainbow)
- Custom animation sequences
- Transition timings and easing functions

#### Dynamic Overlay System
- Single Vue Application Architecture:
  - One dynamic overlay instance
  - Template-driven configuration via JSON manifests
  - Real-time state updates via WebSocket
- Vue Component Types:
  - Alert Components
  - Text Display Components
  - Media Player Components
  - Chat Integration Components
  - Effect Sequence Components
- Template Manifest System:
  - JSON Schema Definition:
    - Layout and positioning
    - Component configurations
    - Animation timelines
    - Trigger mappings
  - Parameter Types:
    - Text parameters (content, fonts, styles)
    - Media parameters (files, paths, constraints)
    - Animation parameters (durations, curves)
    - Event parameters (triggers, conditions)
  - Asset Management:
    - File path validation
    - Media library integration
    - Local file system support
- Template Lifecycle:
  - Create/Edit in management UI
  - Export complete manifest to JSON
  - Import/Load saved templates
  - Live preview and instant deployment

#### Management Interface
- Modern, responsive web dashboard
- Component Management:
  - Visual component creator/editor
  - Drag-and-drop parameter configuration
  - Live preview functionality
  - Component organization and categorization
- File Management:
  - Media library browser
  - File upload system
  - Directory structure management
  - File usage tracking
- Configuration System:
  - JSON-based configuration files
  - Hot-reloading of settings
  - Preset management
  - Backup/Restore functionality
- Testing Tools:
  - Component preview window
  - Trigger simulation
  - Performance monitoring

## Technical Requirements

### System Requirements
- Python 3.11+ (recommended for modern async features)
- Modern web browser support in OBS (Chromium-based)
- Local storage for media assets (SSD recommended)
- Network access for chat platform connections
- Optional: Docker for easy local deployment

### Dependencies
#### Backend
- FastAPI
- Uvicorn (ASGI server)
- python-socketio[async] (async WebSocket support)
- twitchio (async Twitch integration)
- Pillow (Python Imaging Library)
- aiosqlite or SQLModel (async SQLite access)
- aiofiles (async file operations)
- Pydantic (data validation)
- Optional: fastapi-admin (admin UI)

#### Frontend Management Interface
- Vue.js (management interface framework)
- Vuetify (UI component library)
- CodeMirror (parameter JSON editing)
- MediaElement.js (media preview)

#### Frontend Overlay System
- Vue 3 + Vite (single overlay application)
- GSAP or Anime.js for advanced animations
- socket.io-client for real-time updates
- Pinia for state management
- TypeScript for type safety

### Performance Considerations
- Efficient WebSocket message handling via socket.io
- Media optimization and preloading strategies
- Memory and resource management
- Browser and OBS optimization
- Vue Performance Strategy:
  1. Minimal initial bundle size (Vite build)
  2. Code splitting for large components
  3. Lazy loading of heavy dependencies
  4. Efficient reactivity with Vue 3 composition API
- Optimization Techniques:
  - Virtual DOM efficiency
  - Computed property caching
  - Event debouncing/throttling
  - Asset lazy loading
  - State batching with Pinia

## Security Considerations
- Secure storage of Twitch credentials
- Input sanitization for chat commands
- Rate limiting for API endpoints
- Access control for admin features

## Development Setup
(To be expanded with specific setup instructions)

## Deployment
(To be expanded with deployment procedures)

## Future Enhancements
- Multiple platform support (YouTube, Facebook)
- Advanced alert customization
- Interactive viewer games
- Stream statistics overlay
- Custom widget development API
