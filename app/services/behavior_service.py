"""Behavior validation service for step-based animation framework.

Validates animation step syntax and provides validation utilities for
element behavior arrays. Used by API endpoints and widgets to ensure
behavior is well-formed before storing in database.
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Valid animation step types
VALID_STEP_TYPES = {"appear", "animate_property", "animate", "wait", "set", "disappear"}

# Valid animations (predefined animation names)
VALID_ANIMATIONS = {
    "fade-in", "fade-out",
    "slide-in", "slide-out",
    "scale-in", "scale-out",
    "explosion", "pop",
    "spin", "flip", "zoom", "fly", "swipe",
}

# Valid modulation functions (for animate_property)
VALID_MODULATIONS = {
    "linear",
    "ease-in", "ease-out", "ease-in-out",
    "cubic-bezier",
    "steps",
}


def validate_behavior_array(behavior: Any) -> Tuple[bool, List[str]]:
    """Validate a behavior array for correct step syntax.
    
    Args:
        behavior: Behavior value (should be list of step dicts)
    
    Returns:
        Tuple of (is_valid, errors_list)
        - is_valid: True if behavior is valid, False otherwise
        - errors_list: List of error messages (empty if valid)
    """
    errors = []
    
    # Check if behavior is a list
    if not isinstance(behavior, list):
        errors.append(f"behavior must be a list, got {type(behavior).__name__}")
        return False, errors
    
    # Empty behavior array is valid (no animation)
    if len(behavior) == 0:
        return True, []
    
    # Validate each step
    for idx, step in enumerate(behavior):
        step_errors = _validate_step(step, idx)
        errors.extend(step_errors)
    
    is_valid = len(errors) == 0
    return is_valid, errors


def _validate_step(step: Any, step_idx: int) -> List[str]:
    """Validate a single animation step.
    
    Args:
        step: Step dict to validate
        step_idx: Index of step in behavior array (for error messages)
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if not isinstance(step, dict):
        errors.append(f"Step {step_idx}: step must be a dict, got {type(step).__name__}")
        return errors
    
    # Check required 'type' field
    if "type" not in step:
        errors.append(f"Step {step_idx}: missing required field 'type'")
        return errors
    
    step_type = step.get("type")
    if step_type not in VALID_STEP_TYPES:
        errors.append(f"Step {step_idx}: invalid step type '{step_type}'. Must be one of: {', '.join(VALID_STEP_TYPES)}")
        return errors
    
    # Validate step-specific fields
    if step_type == "appear":
        errors.extend(_validate_appear_step(step, step_idx))
    elif step_type == "animate_property":
        errors.extend(_validate_animate_property_step(step, step_idx))
    elif step_type == "animate":
        errors.extend(_validate_animate_step(step, step_idx))
    elif step_type == "wait":
        errors.extend(_validate_wait_step(step, step_idx))
    elif step_type == "set":
        errors.extend(_validate_set_step(step, step_idx))
    elif step_type == "disappear":
        errors.extend(_validate_disappear_step(step, step_idx))
    
    return errors


def _validate_appear_step(step: Dict[str, Any], step_idx: int) -> List[str]:
    """Validate 'appear' step: make element visible with entrance animation."""
    errors = []
    
    # Optional: animation name
    if "animation" in step:
        animation = step["animation"]
        if not isinstance(animation, str):
            errors.append(f"Step {step_idx}: 'animation' must be string, got {type(animation).__name__}")
        elif animation not in VALID_ANIMATIONS:
            errors.append(f"Step {step_idx}: invalid animation '{animation}'. Known animations: {', '.join(VALID_ANIMATIONS)}")
    
    # Optional: duration (milliseconds)
    if "duration" in step:
        duration = step["duration"]
        if not isinstance(duration, (int, float)):
            errors.append(f"Step {step_idx}: 'duration' must be number, got {type(duration).__name__}")
        elif duration < 0:
            errors.append(f"Step {step_idx}: 'duration' must be non-negative, got {duration}")
    
    return errors


def _validate_animate_property_step(step: Dict[str, Any], step_idx: int) -> List[str]:
    """Validate 'animate_property' step: animate element properties over time."""
    errors = []
    
    # Required: properties array
    if "properties" not in step:
        errors.append(f"Step {step_idx}: 'animate_property' requires 'properties' field")
        return errors
    
    properties = step.get("properties")
    if not isinstance(properties, list):
        errors.append(f"Step {step_idx}: 'properties' must be array, got {type(properties).__name__}")
        return errors
    
    if len(properties) == 0:
        errors.append(f"Step {step_idx}: 'properties' array must not be empty")
        return errors
    
    # Validate each property animation
    for prop_idx, prop_anim in enumerate(properties):
        if not isinstance(prop_anim, dict):
            errors.append(f"Step {step_idx}: property[{prop_idx}] must be dict, got {type(prop_anim).__name__}")
            continue
        
        if "property" not in prop_anim:
            errors.append(f"Step {step_idx}: property[{prop_idx}] missing 'property' name")
        
        if "from" not in prop_anim or "to" not in prop_anim:
            errors.append(f"Step {step_idx}: property[{prop_idx}] must have 'from' and 'to' values")
        
        if "duration" not in prop_anim:
            errors.append(f"Step {step_idx}: property[{prop_idx}] missing 'duration'")
        elif not isinstance(prop_anim["duration"], (int, float)):
            errors.append(f"Step {step_idx}: property[{prop_idx}] 'duration' must be number")
        
        # Optional: modulation function
        if "modulation" in prop_anim:
            modulation = prop_anim["modulation"]
            if isinstance(modulation, str):
                if modulation not in VALID_MODULATIONS:
                    errors.append(f"Step {step_idx}: property[{prop_idx}] unknown modulation '{modulation}'. Valid: {', '.join(VALID_MODULATIONS)}")
            elif isinstance(modulation, dict):
                # Modulation function with parameters (e.g., cubic-bezier with control points)
                if "type" not in modulation:
                    errors.append(f"Step {step_idx}: property[{prop_idx}] modulation object missing 'type'")
    
    return errors


def _validate_animate_step(step: Dict[str, Any], step_idx: int) -> List[str]:
    """Validate 'animate' step: execute predefined animation."""
    errors = []
    
    # Required: animation name
    if "animation" not in step:
        errors.append(f"Step {step_idx}: 'animate' requires 'animation' field")
        return errors
    
    animation = step.get("animation")
    if not isinstance(animation, str):
        errors.append(f"Step {step_idx}: 'animation' must be string, got {type(animation).__name__}")
    elif animation not in VALID_ANIMATIONS:
        errors.append(f"Step {step_idx}: invalid animation '{animation}'. Valid: {', '.join(VALID_ANIMATIONS)}")
    
    # Optional: duration (may override default animation duration)
    if "duration" in step:
        duration = step["duration"]
        if not isinstance(duration, (int, float)):
            errors.append(f"Step {step_idx}: 'duration' must be number, got {type(duration).__name__}")
        elif duration < 0:
            errors.append(f"Step {step_idx}: 'duration' must be non-negative, got {duration}")
    
    return errors


def _validate_wait_step(step: Dict[str, Any], step_idx: int) -> List[str]:
    """Validate 'wait' step: pause animation for duration."""
    errors = []
    
    # Required: duration (milliseconds)
    if "duration" not in step:
        errors.append(f"Step {step_idx}: 'wait' requires 'duration' field")
        return errors
    
    duration = step.get("duration")
    if not isinstance(duration, (int, float)):
        errors.append(f"Step {step_idx}: 'duration' must be number, got {type(duration).__name__}")
    elif duration < 0:
        errors.append(f"Step {step_idx}: 'duration' must be non-negative, got {duration}")
    
    return errors


def _validate_set_step(step: Dict[str, Any], step_idx: int) -> List[str]:
    """Validate 'set' step: instantly set properties without animation."""
    errors = []
    
    # Required: properties object
    if "properties" not in step:
        errors.append(f"Step {step_idx}: 'set' requires 'properties' field")
        return errors
    
    properties = step.get("properties")
    if not isinstance(properties, dict):
        errors.append(f"Step {step_idx}: 'properties' must be object, got {type(properties).__name__}")
    
    return errors


def _validate_disappear_step(step: Dict[str, Any], step_idx: int) -> List[str]:
    """Validate 'disappear' step: exit animation and hide element."""
    errors = []
    
    # Optional: animation name
    if "animation" in step:
        animation = step["animation"]
        if not isinstance(animation, str):
            errors.append(f"Step {step_idx}: 'animation' must be string, got {type(animation).__name__}")
        elif animation not in VALID_ANIMATIONS:
            errors.append(f"Step {step_idx}: invalid animation '{animation}'. Valid: {', '.join(VALID_ANIMATIONS)}")
    
    # Optional: duration (milliseconds)
    if "duration" in step:
        duration = step["duration"]
        if not isinstance(duration, (int, float)):
            errors.append(f"Step {step_idx}: 'duration' must be number, got {type(duration).__name__}")
        elif duration < 0:
            errors.append(f"Step {step_idx}: 'duration' must be non-negative, got {duration}")
    
    return errors


def validate_and_log_behavior(behavior: Any, context: str = "element") -> bool:
    """Validate behavior and log any errors.
    
    Args:
        behavior: Behavior array to validate
        context: Context string for logging (e.g., "alert_widget_image")
    
    Returns:
        True if valid, False if invalid. Invalid steps are logged as warnings
        but do not raise exceptions (graceful degradation).
    """
    is_valid, errors = validate_behavior_array(behavior)
    
    if not is_valid:
        for error in errors:
            logger.warning(f"Invalid behavior in {context}: {error}")
    
    return is_valid


def get_step_duration(step: Dict[str, Any]) -> float:
    """Get total duration of a step in milliseconds.
    
    Args:
        step: Animation step dict
    
    Returns:
        Duration in milliseconds (0 if step has no duration)
    
    Note:
        - 'wait' and 'disappear' return their duration field
        - 'appear', 'animate', 'animate_property' return duration field if present
        - 'set' returns 0 (instant)
    """
    step_type = step.get("type")
    
    if step_type in ("wait", "disappear", "appear", "animate"):
        return step.get("duration", 0)
    elif step_type == "animate_property":
        # Return max duration of all property animations
        properties = step.get("properties", [])
        if not properties:
            return 0
        return max(prop.get("duration", 0) for prop in properties)
    elif step_type == "set":
        return 0
    
    return 0


def get_total_animation_duration(behavior: List[Dict[str, Any]]) -> float:
    """Calculate total duration of entire behavior sequence.
    
    Args:
        behavior: Behavior array
    
    Returns:
        Total duration in milliseconds
    """
    return sum(get_step_duration(step) for step in behavior)
