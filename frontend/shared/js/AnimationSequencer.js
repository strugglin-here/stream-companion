/**
 * AnimationSequencer - Step-Based Animation Framework for Stream Companion Overlay
 * 
 * Executes step-based animation sequences using GSAP timeline.
 * Each element behavior is an array of animation steps that execute sequentially.
 * 
 * Step Types:
 * - appear: Make element visible with entrance animation
 * - animate_property: Animate CSS properties with optional modulation
 * - animate: Execute predefined animation
 * - wait: Pause animation for duration
 * - set: Instantly set properties
 * - disappear: Exit animation and hide element
 */

class AnimationSequencer {
    constructor(domElement, behavior) {
        this.domElement = domElement;
        this.behavior = behavior || [];
        this.timeline = gsap.timeline({ paused: true });
        this.isPlaying = false;
        
        // Animation catalog for predefined animations
        this.animationCatalog = {
            'fade-in': { opacity: [0, 1] },
            'fade-out': { opacity: [1, 0] },
            'slide-in': { x: [-100, 0], opacity: [0, 1] },
            'slide-out': { x: [0, 100], opacity: [1, 0] },
            'scale-in': { scale: [0, 1], opacity: [0, 1] },
            'scale-out': { scale: [1, 0], opacity: [1, 0] },
            'explosion': { scale: [0, 1], opacity: [0, 1] },
            'pop': { scale: [0.5, 1.2, 1], opacity: [0, 1, 1] },
            'spin': { rotation: [0, 360] },
            'flip': { rotationY: [0, 360] },
            'zoom': { scale: [0.5, 1] },
            'fly': { x: [-200, 0], y: [-200, 0], opacity: [0, 1] },
            'swipe': { x: [window.innerWidth, 0], opacity: [0, 1] }
        };
        
        // Easing catalog
        this.easingCatalog = {
            'linear': 'none',
            'ease-in': 'power1.in',
            'ease-out': 'power1.out',
            'ease-in-out': 'power1.inOut',
            'cubic-bezier': 'power2.inOut'
        };
    }
    
    /**
     * Build the GSAP timeline from behavior array
     */
    build() {
        if (!Array.isArray(this.behavior)) {
            console.error('Behavior must be an array of animation steps');
            return this;
        }
        
        // Clear existing timeline
        this.timeline.clear();
        
        // Add each step to the timeline
        for (let i = 0; i < this.behavior.length; i++) {
            const step = this.behavior[i];
            
            try {
                this._addStep(step, i);
            } catch (err) {
                console.error(`Error processing step ${i}:`, err, step);
                // Continue to next step on error (graceful degradation)
            }
        }
        
        // Add completion handler
        this.timeline.eventCallback('onComplete', () => {
            this.isPlaying = false;
            console.log(`Animation complete for element: ${this.domElement.id}`);
        });
        
        return this;
    }
    
    /**
     * Add a single step to the timeline
     */
    _addStep(step, stepIndex) {
        if (!step || typeof step !== 'object') {
            console.warn(`Step ${stepIndex}: invalid step format`, step);
            return;
        }
        
        const stepType = step.type;
        
        switch (stepType) {
            case 'appear':
                this._addAppearStep(step, stepIndex);
                break;
                
            case 'animate_property':
                this._addAnimatePropertyStep(step, stepIndex);
                break;
                
            case 'animate':
                this._addAnimateStep(step, stepIndex);
                break;
                
            case 'wait':
                this._addWaitStep(step, stepIndex);
                break;
                
            case 'set':
                this._addSetStep(step, stepIndex);
                break;
                
            case 'disappear':
                this._addDisappearStep(step, stepIndex);
                break;
                
            default:
                console.warn(`Step ${stepIndex}: unknown step type '${stepType}'`);
        }
    }
    
    /**
     * Add 'appear' step: make element visible with entrance animation
     */
    _addAppearStep(step, stepIndex) {
        const duration = (step.duration || 500) / 1000; // Convert ms to seconds
        const animation = step.animation || 'fade-in';
        
        const { fromProps, toProps } = this._buildAnimationProps(animation);
        if (!fromProps) {
            console.warn(`Step ${stepIndex}: unknown animation '${animation}'`);
            return;
        }
        
        this.timeline.fromTo(
            this.domElement,
            fromProps,
            { ...toProps, duration, ease: 'power2.out' }
        );
        
        console.log(`Step ${stepIndex}: appear animation '${animation}' (${duration}s)`);
    }
    
    /**
     * Add 'animate_property' step: animate element properties with modulation
     * Properties can have independent durations and easing functions
     */
    _addAnimatePropertyStep(step, stepIndex) {
        const properties = step.properties || [];
        
        if (!Array.isArray(properties) || properties.length === 0) {
            console.warn(`Step ${stepIndex}: animate_property requires properties array`);
            return;
        }
        
        let maxDuration = 0;
        
        for (const propAnim of properties) {
            const propName = propAnim.property;
            const toValue = propAnim.to;
            const duration = (propAnim.duration || 1000) / 1000;
            const easing = this._resolveEasing(propAnim.modulation || 'linear');
            
            maxDuration = Math.max(maxDuration, duration);
            
            // Each property gets its own tween with independent duration/easing
            // Use '<' ONLY for the first property, others follow sequentially
            this.timeline.to(
                this.domElement,
                { [propName]: toValue, duration, ease: easing },
                properties.indexOf(propAnim) === 0 ? '<' : ''
            );
        }
        
        console.log(`Step ${stepIndex}: animate_property (${maxDuration}s)`);
    }
    
    /**
     * Add 'animate' step: execute predefined animation
     */
    _addAnimateStep(step, stepIndex) {
        const animation = step.animation;
        const duration = (step.duration || 1000) / 1000;
        
        if (!animation) {
            console.warn(`Step ${stepIndex}: animate requires animation name`);
            return;
        }
        
        const { toProps } = this._buildAnimationProps(animation);
        if (!toProps) {
            console.warn(`Step ${stepIndex}: unknown animation '${animation}'`);
            return;
        }
        
        this.timeline.to(
            this.domElement,
            { ...toProps, duration, ease: 'power2.out' }
        );
        
        console.log(`Step ${stepIndex}: animate '${animation}' (${duration}s)`);
    }
    
    /**
     * Add 'wait' step: pause animation
     */
    _addWaitStep(step, stepIndex) {
        const duration = (step.duration || 1000) / 1000;
        
        // Add empty tween as pause
        this.timeline.to({}, { duration });
        
        console.log(`Step ${stepIndex}: wait (${duration}s)`);
    }
    
    /**
     * Add 'set' step: instantly set properties
     */
    _addSetStep(step, stepIndex) {
        const properties = step.properties || {};
        
        this.timeline.set(this.domElement, properties);
        
        console.log(`Step ${stepIndex}: set properties`, properties);
    }
    
    /**
     * Add 'disappear' step: exit animation and hide
     */
    _addDisappearStep(step, stepIndex) {
        console.log(`_addDisappearStep called for step ${stepIndex}:`, step);
        
        const duration = (step.duration || 500) / 1000;
        const animation = step.animation || 'fade-out';
        
        console.log(`_addDisappearStep: duration=${step.duration}ms → ${duration}s, animation=${animation}`);
        
        const { toProps } = this._buildAnimationProps(animation);
        console.log(`_addDisappearStep: toProps=`, toProps);
        
        if (!toProps) {
            console.warn(`Step ${stepIndex}: unknown animation '${animation}'`);
            return;
        }
        
        // Animate the disappear effect, then hide the element
        this.timeline.to(
            this.domElement,
            { ...toProps, duration, ease: 'power2.in' }
        );
        
        // After disappear animation completes, hide the element
        this.timeline.set(this.domElement, { visibility: 'hidden' });
        
        console.log(`Step ${stepIndex}: disappear animation '${animation}' (${duration}s)`);
    }
    
    /**
     * Resolve easing function name to GSAP easing
     */
    _resolveEasing(modulation) {
        if (!modulation) return 'power1.inOut';
        
        if (typeof modulation === 'string') {
            return this.easingCatalog[modulation] || 'power1.inOut';
        }
        
        if (typeof modulation === 'object' && modulation.type) {
            return this.easingCatalog[modulation.type] || 'power1.inOut';
        }
        
        return 'power1.inOut';
    }
    
    /**
     * Build animation properties from catalog
     * Returns { fromProps, toProps } for use with fromTo() or just { toProps } for to()
     */
    _buildAnimationProps(animationName) {
        const animProps = this.animationCatalog[animationName];
        if (!animProps) {
            return { fromProps: null, toProps: null };
        }
        
        const toProps = {};
        const fromProps = {};
        
        for (const [prop, values] of Object.entries(animProps)) {
            if (Array.isArray(values)) {
                fromProps[prop] = values[0]; // Initial value
                toProps[prop] = values[values.length - 1]; // Final value
            } else {
                toProps[prop] = values;
            }
        }
        
        return { fromProps, toProps };
    }
    
    /**
     * Play the animation sequence (restarts from beginning)
     */
    play() {
        if (this.timeline.duration() === 0) {
            console.log(`No animation steps for element: ${this.domElement.id}`);
            return this;
        }
        
        this.isPlaying = true;
        this.timeline.restart();
        console.log(`Playing animation for element: ${this.domElement.id}`);
        return this;
    }
    
    /**
     * Pause the animation
     */
    pause() {
        this.isPlaying = false;
        this.timeline.pause();
        console.log(`Paused animation for element: ${this.domElement.id}`);
        return this;
    }
    
    /**
     * Stop the animation and reset
     */
    stop() {
        this.isPlaying = false;
        this.timeline.pause();
        this.timeline.progress(0);
        
        // Reset element to initial state
        gsap.set(this.domElement, { opacity: 0, transform: 'none' });
        
        console.log(`Stopped animation for element: ${this.domElement.id}`);
        return this;
    }
    
    /**
     * Restart the animation from beginning
     */
    restart() {
        this.isPlaying = true;
        this.timeline.restart();
        console.log(`Restarted animation for element: ${this.domElement.id}`);
        return this;
    }
    
    /**
     * Get total animation duration in seconds
     */
    getDuration() {
        return this.timeline.duration();
    }
    
    /**
     * Get animation progress (0-1)
     */
    getProgress() {
        return this.timeline.progress();
    }
    
    /**
     * Set animation progress (0-1)
     */
    setProgress(value) {
        this.timeline.progress(Math.max(0, Math.min(1, value)));
        return this;
    }
    
    /**
     * Get animation status
     */
    getStatus() {
        return {
            isPlaying: this.isPlaying,
            duration: this.getDuration(),
            progress: this.getProgress(),
            elementId: this.domElement.id,
            stepCount: this.behavior.length
        };
    }
    
    /**
     * Apply property updates without restarting animation
     * Used when element.properties changes while animation is playing
     * All properties are allowed (element type defines valid properties)
     */
    updateProperties(properties) {
        if (!this.isPlaying || !properties || typeof properties !== 'object') {
            return;
        }
        
        // Apply all properties (element type validation happens server-side)
        gsap.set(this.domElement, properties);
        console.log(`Updated properties on element ${this.domElement.id} during animation:`, properties);
    }
}

// Export for use in HTML
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationSequencer;
}
