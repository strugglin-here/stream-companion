// Vue 3 Components for Stream Companion Admin

(function() {
    // Modal Component
    const Modal = {
    name: 'Modal',
    template: `
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('close')">
            <div class="bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 border border-gray-700">
                <div class="p-6">
                    <slot></slot>
                </div>
            </div>
        </div>
    `,
    emits: ['close']
};

// Widget Panel Component
const WidgetPanel = {
    name: 'WidgetPanel',
    props: {
        widget: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            featureParams: {},
            executing: null
        };
    },
    methods: {
        async executeFeature(feature) {
            this.executing = feature.method_name;
            try {
                await this.$emit('execute', {
                    widgetId: this.widget.id,
                    featureName: feature.method_name,
                    params: this.featureParams[feature.method_name] || {}
                });
            } finally {
                this.executing = null;
            }
        },
        getParamValue(featureName, paramName) {
            if (!this.featureParams[featureName]) {
                this.featureParams[featureName] = {};
            }
            return this.featureParams[featureName][paramName];
        },
        setParamValue(featureName, paramName, value) {
            if (!this.featureParams[featureName]) {
                this.featureParams[featureName] = {};
            }
            this.featureParams[featureName][paramName] = value;
        },
        getParamDefault(param) {
            return param.default || '';
        }
    },
    template: `
        <div class="bg-gray-800 rounded-lg border border-gray-700 p-6 shadow-lg">
            <!-- Widget Header -->
            <div class="flex items-start justify-between mb-4">
                <div>
                    <h3 class="text-lg font-bold text-white">{{ widget.name }}</h3>
                    <p class="text-sm text-gray-400">{{ widget.widget_class }}</p>
                </div>
                <button
                    @click="$emit('remove', widget.id)"
                    class="text-gray-400 hover:text-red-500 transition"
                    title="Remove from dashboard"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>

            <!-- Widget Info -->
            <div class="mb-4 pb-4 border-b border-gray-700">
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-400">Elements: {{ widget.elements.length }}</span>
                    <span class="text-gray-400">Features: {{ widget.features.length }}</span>
                </div>
            </div>

            <!-- Features List -->
            <div class="space-y-4">
                <div v-if="widget.features.length === 0" class="text-center py-4 text-gray-500 text-sm">
                    No features available
                </div>
                <div v-for="feature in widget.features" :key="feature.method_name" class="bg-gray-700 rounded-lg p-4">
                    <h4 class="font-medium text-white mb-2">{{ feature.display_name }}</h4>
                    <p v-if="feature.description" class="text-sm text-gray-400 mb-3">{{ feature.description }}</p>
                    
                    <!-- Feature Parameters -->
                    <div v-if="feature.parameters.length > 0" class="space-y-3 mb-3">
                        <div v-for="param in feature.parameters" :key="param.name">
                            <label class="block text-xs font-medium text-gray-300 mb-1">
                                {{ param.label || param.name }}
                                <span v-if="!param.optional" class="text-red-400">*</span>
                            </label>
                            
                            <!-- Dropdown -->
                            <select
                                v-if="param.type === 'dropdown'"
                                :value="getParamValue(feature.method_name, param.name) || getParamDefault(param)"
                                @input="setParamValue(feature.method_name, param.name, $event.target.value)"
                                class="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-sm focus:ring-2 focus:ring-blue-500"
                            >
                                <option v-if="param.optional" value="">-- Optional --</option>
                                <option v-for="opt in param.options" :key="opt" :value="opt">{{ opt }}</option>
                            </select>
                            
                            <!-- Color Picker -->
                            <input
                                v-else-if="param.type === 'color-picker'"
                                type="color"
                                :value="getParamValue(feature.method_name, param.name) || getParamDefault(param)"
                                @input="setParamValue(feature.method_name, param.name, $event.target.value)"
                                class="w-full h-10 bg-gray-600 border border-gray-500 rounded cursor-pointer"
                            >
                            
                            <!-- Number -->
                            <input
                                v-else-if="param.type === 'number'"
                                type="number"
                                :value="getParamValue(feature.method_name, param.name) || getParamDefault(param)"
                                @input="setParamValue(feature.method_name, param.name, parseFloat($event.target.value))"
                                :min="param.min"
                                :max="param.max"
                                :placeholder="param.placeholder"
                                class="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-sm focus:ring-2 focus:ring-blue-500"
                            >
                            
                            <!-- Text -->
                            <input
                                v-else-if="param.type === 'text'"
                                type="text"
                                :value="getParamValue(feature.method_name, param.name) || getParamDefault(param)"
                                @input="setParamValue(feature.method_name, param.name, $event.target.value)"
                                :placeholder="param.placeholder"
                                class="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-sm focus:ring-2 focus:ring-blue-500"
                            >
                            
                            <!-- Checkbox -->
                            <label v-else-if="param.type === 'checkbox'" class="flex items-center">
                                <input
                                    type="checkbox"
                                    :checked="getParamValue(feature.method_name, param.name) || getParamDefault(param)"
                                    @change="setParamValue(feature.method_name, param.name, $event.target.checked)"
                                    class="mr-2"
                                >
                                <span class="text-sm">{{ param.label || param.name }}</span>
                            </label>
                        </div>
                    </div>
                    
                    <!-- Execute Button -->
                    <button
                        @click="executeFeature(feature)"
                        :disabled="executing === feature.method_name"
                        class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded text-sm font-medium transition"
                    >
                        <span v-if="executing === feature.method_name">Executing...</span>
                        <span v-else>▶ Execute</span>
                    </button>
                </div>
            </div>
        </div>
    `,
    emits: ['remove', 'execute']
};

// Export components
window.VueComponents = {
    Modal,
    WidgetPanel
};
})();
