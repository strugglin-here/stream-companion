# Stream Companion - OBS Web Overlay System

## Project Overview
A Python-based web application that provides dynamic stream overlays for OBS (Open Broadcaster Software). This system generates web-based overlays on a local port that can be integrated into OBS scenes through browser sources. Real-time interactivity, pre-defined animation sequences, and unique customizations for streamers.

## Technical Architecture

### Core Technologies
- **Backend**: FastAPI ASGI web server
- **Frontend**: Vue 3 Single-App Architecture
  - Base Layer: Vue 3 + Vite + TypeScript
  - State Management: Pinia for reactive state
  - Real-time Updates: socket.io-client
  - Advanced Animations: GSAP/Anime.js
- **WebSocket**: For real-time communication via socket.io
- **Database**: SQLite for persistent storage
- **OBS Integration**: Leverage the included 'browser source' in OBS to open the server's overlay endpoint

### Key Components

#### 1. Web Server (FastAPI Application)
- Serves dynamic web content for OBS browser sources via ASGI
- Serves management interface for component configuration and live operation
- Native WebSocket support for real-time updates
- Async asset serving (images, videos, sounds)
- OpenAPI-documented REST endpoints with Pydantic validation
- Multi-route system:
  - `/overlay/*` - OBS-facing overlay endpoints
  - `/manage/*` - Component management interface
  - `/api/*` - REST API endpoints for external control

#### 2. Twitch Integration
- Real-time chat monitoring and parsing
- Chat command handling system
- Event subscription system (follows, subscriptions, bits)
- Authentication and API token management

#### 3. Media Management
- Local asset management system
  - Image storage and serving
  - Video file handling
  - Sound effect library
- Media queue system
- Format validation and optimization

#### 4. Animation System
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
- Real-time chat display with customizable styling
- Chat command system for triggering overlay actions
- User badge and emote rendering
- Message filtering and moderation capabilities

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
- Python 3.8+
- Modern web browser support in OBS
- Local storage for media assets
- Network access for Twitch integration

### Dependencies
#### Backend
- FastAPI
- Uvicorn (ASGI server)
- python-socketio[async] (async WebSocket support)
- twitchio
- aiofiles (async file operations)
- Pillow (Python Imaging Library)
- SQLAlchemy (async with SQLite)
- Pydantic (data validation)
- FastAPI Admin (admin interface)

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
- Async WebSocket handling with native ASGI support
- Async file operations and media serving
- Concurrent request handling via ASGI event loop
- Memory and resource management with background tasks
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
