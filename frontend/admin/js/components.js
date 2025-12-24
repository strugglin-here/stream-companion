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

// Confirmation Dialog Component
const ConfirmDialog = {
    name: 'ConfirmDialog',
    props: {
        title: {
            type: String,
            default: 'Confirm Action'
        },
        message: {
            type: String,
            required: true
        },
        confirmText: {
            type: String,
            default: 'Confirm'
        },
        cancelText: {
            type: String,
            default: 'Cancel'
        },
        confirmClass: {
            type: String,
            default: 'bg-red-600 hover:bg-red-700'
        }
    },
    template: `
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="$emit('cancel')">
            <div class="bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 border border-gray-700">
                <div class="p-6">
                    <h3 class="text-xl font-bold mb-4 text-white">{{ title }}</h3>
                    <p class="text-gray-300 mb-6">{{ message }}</p>
                    <div class="flex justify-end space-x-3">
                        <button
                            @click="$emit('cancel')"
                            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition text-white"
                        >
                            {{ cancelText }}
                        </button>
                        <button
                            @click="$emit('confirm')"
                            :class="['px-4 py-2 rounded transition text-white', confirmClass]"
                        >
                            {{ confirmText }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,
    emits: ['confirm', 'cancel']
};

// Widget Panel Component
const WidgetPanel = {
    name: 'WidgetPanel',
    props: {
        widget: {
            type: Object,
            required: true
        },
        widgetTypes: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            featureParams: {},
            executing: null,
            showElements: false,
            editingElement: null,
            elementForm: {},
            showAssetPicker: false,
            showAssetUploader: false,
            mediaFiles: [],
            mediaLibrary: null,
            mediaUploader: null,
            showEditWidget: false,
            widgetForm: {},
            currentAssetRole: 'primary', // Current role being edited in multi-asset UI
        };
    },
    computed: {
        filteredMediaFiles() {
            if (!this.editingElement) return this.mediaFiles;
            
            const elementType = this.editingElement.element_type;
            
            return this.mediaFiles.filter(file => {
                const mimeType = file.mime_type;
                
                switch (elementType) {
                    case 'image':
                        return mimeType.startsWith('image/');
                    case 'video':
                        return mimeType.startsWith('video/');
                    case 'audio':
                        return mimeType.startsWith('audio/');
                    case 'text':
                    case 'timer':
                    case 'counter':
                    case 'animation':
                    case 'canvas':
                        // These types may use images for backgrounds or icons
                        return mimeType.startsWith('image/');
                    default:
                        // Show all files for unknown types
                        return true;
                }
            });
        },
        // Get all roles defined in element's schema
        elementRoles() {
            if (!this.editingElement) return [];
            const properties = this.editingElement.properties || {};
            return properties.media_roles || [];
        },
        // Get all roles that have media assigned
        assignedRoles() {
            if (!this.elementForm.media_assets) return [];
            return this.elementForm.media_assets.map(a => a.role);
        },
        // Get media details for current role
        currentMediaDetails() {
            if (!this.elementForm.media_assets) return null;
            const asset = this.elementForm.media_assets.find(a => a.role === this.currentAssetRole);
            if (!asset) return null;
            
            // Find in media files list
            const media = this.mediaFiles.find(f => f.id === asset.media_id);
            return media || null;
        }
    },
    mounted() {
        // Load media files when component mounts
        this.loadMediaFiles();
    },
    methods: {
        async executeFeature(feature) {
            this.executing = feature.method_name;
            try {
                // Build params with defaults for any missing values
                const params = {};
                if (feature.parameters) {
                    feature.parameters.forEach(param => {
                        const value = this.getParamValue(feature.method_name, param.name);
                        params[param.name] = value !== undefined && value !== '' 
                            ? value 
                            : this.getParamDefault(param);
                    });
                }
                
                await this.$emit('execute', {
                    widgetId: this.widget.id,
                    featureName: feature.method_name,
                    params: params
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
        },
        isMediaSelected(mediaId) {
            // Check if media is selected for current role
            const asset = this.elementForm.media_assets?.find(a => a.role === this.currentAssetRole);
            return asset && asset.media_id === mediaId;
        },
        isRoleAssigned(role) {
            // Check if a role has media assigned
            return this.assignedRoles.includes(role);
        },
        removeAssetRole(role) {
            // Remove asset for specific role
            if (!this.elementForm.media_assets) return;
            this.elementForm.media_assets = this.elementForm.media_assets.filter(
                a => a.role !== role
            );
        },
        switchAssetRole(role) {
            // Switch to editing a different role
            this.currentAssetRole = role;
        },
        getAvailableRoles() {
            // Get role suggestions based on element type
            const type = this.editingElement?.element_type;
            if (type === 'card') {
                return ['front_background', 'front_content', 'back_background', 'back_content'];
            }
            return ['primary', 'background', 'overlay', 'icon'];
        },
        editElement(element) {
            this.editingElement = element;
            this.elementForm = {
                name: element.name,
                description: element.description || '',
                media_assets: element.media_assets ? [...element.media_assets] : [],
                playing: element.playing,
                properties: JSON.stringify(element.properties || {}, null, 2),
                behavior: JSON.stringify(element.behavior || [], null, 2)
            };
            // Set current role to first defined role in schema
            const roles = element.properties?.media_roles || [];
            this.currentAssetRole = roles.length > 0 ? roles[0] : 'default';
            this.showAssetPicker = false;
            this.showAssetUploader = false;
            
            // Reload media files when opening editor
            this.loadMediaFiles();
        },
        cancelEdit() {
            this.editingElement = null;
            this.elementForm = {};
            this.showAssetPicker = false;
            this.showAssetUploader = false;
        },
        async loadMediaFiles() {
            try {
                const response = await fetch('/api/media/');
                const data = await response.json();
                this.mediaFiles = data.files || [];
            } catch (error) {
                console.error('Error loading media files:', error);
                this.mediaFiles = [];
            }
        },
        selectAsset(mediaId) {
            // Add or update media asset for current role
            if (!this.elementForm.media_assets) {
                this.elementForm.media_assets = [];
            }
            
            // Remove existing asset with this role
            this.elementForm.media_assets = this.elementForm.media_assets.filter(
                a => a.role !== this.currentAssetRole
            );
            
            // Add new asset
            this.elementForm.media_assets.push({
                media_id: mediaId,
                role: this.currentAssetRole
            });
            
            this.showAssetPicker = false;
        },
        removeAssetRole(role) {
            // Remove asset for specific role
            if (!this.elementForm.media_assets) return;
            this.elementForm.media_assets = this.elementForm.media_assets.filter(
                a => a.role !== role
            );
        },
        switchAssetRole(role) {
            // Switch to editing a different role
            this.currentAssetRole = role;
        },
        toggleAssetPicker() {
            this.showAssetPicker = !this.showAssetPicker;
            this.showAssetUploader = false;
        },
        toggleAssetUploader() {
            this.showAssetUploader = !this.showAssetUploader;
            this.showAssetPicker = false;
        },
        openFileDialog(event) {
            // Find the file input element within the event target's parent
            const fileInput = event.currentTarget.parentElement.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.click();
            }
        },
        handleDragOver(event) {
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.classList.add('border-blue-500', 'bg-gray-700');
        },
        handleDragLeave(event) {
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.classList.remove('border-blue-500', 'bg-gray-700');
        },
        async handleDrop(event) {
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.classList.remove('border-blue-500', 'bg-gray-700');
            
            const files = event.dataTransfer.files;
            if (!files || !files.length) return;
            
            console.log('Files dropped:', files);
            await this.uploadFiles(files);
        },
        async uploadFiles(files) {
            console.log('Uploading files:', files);
            
            const formData = new FormData();
            for (const file of files) {
                formData.append('files', file);
                console.log('Adding file to upload:', file.name);
            }
            
            try {
                console.log('Uploading to /api/media/...');
                const response = await fetch('/api/media/', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Upload failed: ${errorText}`);
                }
                
                const result = await response.json();
                console.log('Upload result:', result);
                
                // Use the first uploaded file's ID
                if (result.uploaded && result.uploaded.length > 0) {
                    const mediaId = result.uploaded[0].id;
                    this.selectAsset(mediaId);
                    console.log('Added media_id', mediaId, 'to role', this.currentAssetRole);
                } else {
                    console.warn('No uploaded files in response:', result);
                }
                
                // Use the first uploaded file's ID
                if (result.uploaded && result.uploaded.length > 0) {
                    const mediaId = result.uploaded[0].id;
                    this.selectAsset(mediaId);
                    console.log('Added media_id', mediaId, 'to role', this.currentAssetRole);
                } else {
                    console.warn('No uploaded files in response:', result);
                }
                
                // Reload media list
                await this.loadMediaFiles();
                this.showAssetUploader = false;
            } catch (error) {
                console.error('Error uploading file:', error);
                alert('Failed to upload file: ' + error.message);
            }
        },
        async handleFileUpload(event) {
            const files = event.target.files;
            console.log('File upload triggered, files:', files);
            
            if (!files || !files.length) {
                console.log('No files selected');
                return;
            }
            
            await this.uploadFiles(files);
            
            // Clear the file input so the same file can be uploaded again
            event.target.value = '';
        },
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        },
        getDefaultParameters() {
            const widgetType = this.widgetTypes.find(wt => wt.widget_class === this.widget.widget_class);
            return widgetType ? widgetType.default_parameters : {};
        },
        openEditWidget() {
            this.widgetForm = {
                name: this.widget.name,
                widget_parameters: JSON.stringify(this.widget.widget_parameters || {}, null, 2)
            };
            this.showEditWidget = true;
        },
        cancelEditWidget() {
            this.showEditWidget = false;
            this.widgetForm = {};
        },
        async saveWidget() {
            try {
                // Parse JSON parameters
                const params = JSON.parse(this.widgetForm.widget_parameters);
                
                this.$emit('updateWidget', {
                    widgetId: this.widget.id,
                    data: {
                        name: this.widgetForm.name,
                        widget_parameters: params
                    }
                });
                
                this.cancelEditWidget();
            } catch (err) {
                alert('Error saving widget: ' + err.message);
            }
        },
        async saveElement() {
            try {
                // Parse and validate JSON fields with inline error display
                let properties, behavior;
                
                try {
                    properties = JSON.parse(this.elementForm.properties);
                } catch (err) {
                    this.elementForm.error = `Properties JSON error: ${err.message}`;
                    return;
                }
                
                try {
                    behavior = JSON.parse(this.elementForm.behavior);
                } catch (err) {
                    this.elementForm.error = `Behavior JSON error: ${err.message}`;
                    return;
                }
                
                // Validate behavior is an array
                if (!Array.isArray(behavior)) {
                    this.elementForm.error = 'Behavior must be a JSON array of animation steps';
                    return;
                }
                
                // Clear error if validation passed
                this.elementForm.error = null;
                
                await this.$emit('updateElement', {
                    widgetId: this.widget.id,
                    elementId: this.editingElement.id,
                    data: {
                        // name is immutable and not included in updates
                        description: this.elementForm.description || null,
                        media_assets: this.elementForm.media_assets || [],
                        playing: this.elementForm.playing,
                        properties,
                        behavior
                    }
                });
                
                this.cancelEdit();
            } catch (err) {
                alert('Error saving element: ' + err.message);
            }
        }
    },
    template: `
        <div class="bg-gray-800 rounded-lg border border-gray-700 p-6 shadow-lg">
            <!-- Widget Header -->
            <div class="flex items-start justify-between mb-4 pb-4 border-b border-gray-700">
                <div class="flex-1">
                    <h3 class="text-lg font-bold text-white">{{ widget.name }} <span class="text-sm text-gray-400 font-normal">({{ widget.widget_class }})</span></h3>
                </div>
                <div class="flex gap-2">
                    <button
                        @click="openEditWidget"
                        class="text-gray-400 hover:text-blue-400 transition"
                        title="Edit widget"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                    </button>
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
            </div>

            <!-- Features List -->
            <div class="space-y-3 mb-4">
                <div v-if="widget.features.length === 0" class="text-center py-4 text-gray-500 text-sm">
                    No features available
                </div>
                <div v-for="feature in widget.features" :key="feature.method_name">
                    <!-- Execute Button (now at top with feature name) -->
                    <button
                        @click="executeFeature(feature)"
                        :disabled="executing === feature.method_name"
                        class="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded text-sm font-medium transition mb-3"
                    >
                        <span v-if="executing === feature.method_name">⏳ {{ feature.display_name }}...</span>
                        <span v-else>▶ {{ feature.display_name }}</span>
                    </button>
                    
                    <!-- Feature Parameters (horizontal layout) -->
                    <div v-if="feature.parameters.length > 0" class="space-y-2">
                        <div v-for="param in feature.parameters" :key="param.name" class="flex items-center gap-2">
                            <label class="text-xs font-medium text-gray-300 whitespace-nowrap w-24 flex-shrink-0">
                                {{ param.label || param.name }}<span v-if="!param.optional" class="text-red-400">*</span>
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
                            
                            <!-- Slider (Range Input) -->
                            <div v-else-if="param.type === 'slider'" class="flex items-center gap-2 w-full">
                                <input
                                    type="range"
                                    :value="getParamValue(feature.method_name, param.name) || getParamDefault(param)"
                                    @input="setParamValue(feature.method_name, param.name, parseInt($event.target.value))"
                                    :min="param.min || 0"
                                    :max="param.max || 100"
                                    :step="param.step || 1"
                                    class="flex-1 h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                                >
                                <span class="text-sm font-mono text-blue-400 w-12 text-right">
                                    {{ getParamValue(feature.method_name, param.name) || getParamDefault(param) }}
                                </span>
                            </div>
                            
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
                </div>
            </div>

            <!-- Elements Toggle (moved to bottom) -->
            <div class="mt-4 pt-4 border-t border-gray-700">
                <button
                    @click="showElements = !showElements"
                    class="text-sm text-blue-400 hover:text-blue-300 transition"
                >
                    {{ showElements ? '▼ Hide Elements' : '▶ Show Elements' }} ({{ widget.elements.length }})
                </button>
            </div>

            <!-- Elements List (Collapsible) -->
            <div v-if="showElements" class="mt-4 pt-4 border-t border-gray-700 space-y-2">
                <div v-if="widget.elements.length === 0" class="text-center py-4 text-gray-500 text-sm">
                    No elements
                </div>
                <div v-for="element in widget.elements" :key="element.id" class="bg-gray-700 rounded p-3">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center space-x-2 mb-1">
                                <h5 class="font-medium text-white text-sm">{{ element.name }}</h5>
                                <span class="text-xs px-2 py-0.5 rounded bg-gray-600 text-gray-300">{{ element.element_type }}</span>
                            </div>
                            <p v-if="element.description" class="text-xs text-gray-400 mb-1">{{ element.description }}</p>
                            <div class="flex items-center space-x-3 text-xs text-gray-400">
                                <span :class="element.playing ? 'text-green-400' : 'text-gray-500'">
                                    {{ element.playing ? '▶ Playing' : '⏸ Stopped' }}
                                </span>
                                <span v-if="element.behavior && element.behavior.length > 0" class="text-yellow-400">
                                    ✨ {{ element.behavior.length }} steps
                                </span>
                                <span v-if="element.media_details && element.media_details.length > 0" class="text-purple-400">📎 {{ element.media_details.length }} Media</span>
                            </div>
                        </div>
                        <button
                            @click="editElement(element)"
                            class="ml-2 text-gray-400 hover:text-blue-400 transition"
                            title="Edit element"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Element Edit Modal -->
        <div v-if="editingElement" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="cancelEdit">
            <div class="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 border border-gray-700 max-h-[90vh] overflow-y-auto">
                <div class="p-6">
                    <h3 class="text-xl font-bold mb-4 text-white">Edit Element: {{ editingElement.name }}</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Description</label>
                            <input
                                v-model="elementForm.description"
                                type="text"
                                placeholder="Optional"
                                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:ring-2 focus:ring-blue-500"
                            >
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Media Assets</label>
                            
                            <!-- Current Assets List -->
                            <div v-if="elementForm.media_assets && elementForm.media_assets.length > 0" class="mb-3 space-y-2">
                                <div 
                                    v-for="asset in elementForm.media_assets" 
                                    :key="asset.role"
                                    :class="[
                                        'flex items-center justify-between p-2 rounded border text-sm',
                                        currentAssetRole === asset.role 
                                            ? 'bg-blue-900 border-blue-500' 
                                            : 'bg-gray-750 border-gray-600'
                                    ]"
                                >
                                    <div class="flex-1">
                                        <div class="font-medium">{{ asset.role }}</div>
                                        <div class="text-xs text-gray-400">Media ID: {{ asset.media_id }}</div>
                                    </div>
                                    <div class="flex gap-2">
                                        <button
                                            v-if="currentAssetRole !== asset.role"
                                            @click="switchAssetRole(asset.role)"
                                            type="button"
                                            class="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            @click="removeAssetRole(asset.role)"
                                            type="button"
                                            class="px-2 py-1 text-xs bg-red-600 hover:bg-red-700 rounded"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Role Selector - Shows element's defined media_roles schema -->
                            <div class="mb-3">
                                <label class="block text-xs font-medium text-gray-400 mb-1">
                                    Element Roles
                                    <span v-if="elementRoles.length === 0" class="text-yellow-400">(No media_roles defined in properties)</span>
                                </label>
                                <div class="flex gap-2 flex-wrap">
                                    <button
                                        v-for="role in elementRoles"
                                        :key="role"
                                        @click="switchAssetRole(role)"
                                        type="button"
                                        :class="[
                                            'px-3 py-1 text-xs rounded transition flex items-center gap-1',
                                            currentAssetRole === role
                                                ? 'bg-blue-600 text-white'
                                                : isRoleAssigned(role)
                                                    ? 'bg-green-700 text-white hover:bg-green-600'
                                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-650'
                                        ]"
                                    >
                                        <span v-if="isRoleAssigned(role)">✓</span>
                                        <span v-else>○</span>
                                        {{ role }}
                                    </button>
                                </div>
                                <div v-if="currentAssetRole" class="mt-2 text-xs text-gray-400">
                                    Currently editing: <span class="text-blue-400 font-medium">{{ currentAssetRole }}</span>
                                </div>
                            </div>
                            <div class="space-y-2">
                                
                                <!-- Asset selection buttons -->
                                <div class="flex gap-2">
                                    <button
                                        type="button"
                                        @click="toggleAssetPicker"
                                        class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition"
                                    >
                                        📁 {{ showAssetPicker ? 'Hide' : 'Choose Existing' }}
                                    </button>
                                    <button
                                        type="button"
                                        @click="toggleAssetUploader"
                                        class="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition"
                                    >
                                        ⬆️ {{ showAssetUploader ? 'Hide' : 'Upload New' }}
                                    </button>
                                </div>
                                
                                <!-- Asset Picker -->
                                <div v-if="showAssetPicker" class="border border-gray-600 rounded-lg p-4 bg-gray-750">
                                    <h4 class="text-sm font-medium text-gray-300 mb-3">Select Existing Asset</h4>
                                    <div v-if="filteredMediaFiles.length === 0 && mediaFiles.length === 0" class="text-center py-4 text-gray-400 text-sm">
                                        No media files uploaded yet
                                    </div>
                                    <div v-else-if="filteredMediaFiles.length === 0" class="text-center py-4 text-gray-400 text-sm">
                                        No compatible {{ editingElement.element_type }} files found.<br>
                                        <span class="text-xs">Upload a {{ editingElement.element_type }} file to use with this element.</span>
                                    </div>
                                    <div v-else class="max-h-64 overflow-y-auto space-y-2">
                                        <button
                                            v-for="file in filteredMediaFiles"
                                            :key="file.id"
                                            @click="selectAsset(file.id)"
                                            :class="[
                                                'w-full text-left px-3 py-2 rounded border transition',
                                                isMediaSelected(file.id)
                                                    ? 'bg-blue-600 border-blue-500 text-white'
                                                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-650'
                                            ]"
                                        >
                                            <div class="flex items-center justify-between">
                                                <div class="flex-1 min-w-0">
                                                    <div class="font-medium text-sm truncate">{{ file.original_filename || file.filename }}</div>
                                                    <div class="text-xs opacity-75">
                                                        {{ file.mime_type }} • {{ formatFileSize(file.size) }}
                                                    </div>
                                                </div>
                                                <div v-if="file.mime_type.startsWith('image/')" class="ml-3 flex-shrink-0">
                                                    <img 
                                                        :src="file.url" 
                                                        :alt="file.filename"
                                                        class="w-12 h-12 object-cover rounded border border-gray-600"
                                                    >
                                                </div>
                                            </div>
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- Asset Uploader -->
                                <div v-if="showAssetUploader" class="border border-gray-600 rounded-lg p-4 bg-gray-750">
                                    <h4 class="text-sm font-medium text-gray-300 mb-3">Upload New Asset</h4>
                                    <div class="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-blue-500 transition cursor-pointer"
                                         @click="openFileDialog"
                                         @dragover="handleDragOver"
                                         @dragleave="handleDragLeave"
                                         @drop="handleDrop">
                                        <div class="text-4xl mb-2">📁</div>
                                        <p class="text-sm text-gray-300 mb-1">Click to select files</p>
                                        <p class="text-xs text-gray-500">or drag and drop</p>
                                        <p class="text-xs text-gray-500 mt-2">Images, videos, and audio files accepted</p>
                                        <input
                                            type="file"
                                            @change="handleFileUpload"
                                            accept="image/*,video/*,audio/*"
                                            multiple
                                            class="hidden"
                                        >
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Asset Preview -->
                        <div v-if="currentMediaDetails">
                            <label class="block text-sm font-medium text-gray-300 mb-2">Preview ({{ currentAssetRole }})</label>
                            <div class="flex items-center justify-center bg-gray-900 rounded-lg p-4 min-h-[120px]">
                                <!-- Image Preview -->
                                <img 
                                    v-if="currentMediaDetails.mime_type && currentMediaDetails.mime_type.startsWith('image/')"
                                    :src="currentMediaDetails.url"
                                    :alt="currentMediaDetails.original_filename"
                                    class="max-w-full max-h-64 object-contain rounded"
                                    @error="$event.target.style.display='none'"
                                >
                                
                                <!-- Video Preview -->
                                <video
                                    v-else-if="currentMediaDetails.mime_type && currentMediaDetails.mime_type.startsWith('video/')"
                                    :src="currentMediaDetails.url"
                                    controls
                                    class="max-w-full max-h-64 rounded"
                                    @error="$event.target.style.display='none'"
                                >
                                    Your browser does not support video playback.
                                </video>
                                
                                <!-- Audio Preview -->
                                <div v-else-if="currentMediaDetails.mime_type && currentMediaDetails.mime_type.startsWith('audio/')" class="w-full">
                                    <div class="text-center mb-3">
                                        <div class="text-4xl mb-2">🔊</div>
                                        <div class="text-xs text-gray-400">{{ currentMediaDetails.original_filename }}</div>
                                    </div>
                                    <audio
                                        :src="currentMediaDetails.url"
                                        controls
                                        class="w-full"
                                        @error="$event.target.style.display='none'"
                                    >
                                        Your browser does not support audio playback.
                                    </audio>
                                </div>
                                
                                <!-- Fallback for unknown types -->
                                <div v-else class="text-center text-gray-400 text-sm">
                                    <div class="text-4xl mb-2">📄</div>
                                    <div>{{ currentMediaDetails.original_filename }}</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <label class="flex items-center space-x-2">
                                <input
                                    v-model="elementForm.playing"
                                    type="checkbox"
                                    class="form-checkbox"
                                >
                                <span class="text-sm text-gray-300">Playing (executes animation behavior)</span>
                            </label>
                        </div>
                        
                        <!-- Error Message Display -->
                        <div v-if="elementForm.error" class="p-3 bg-red-900 border border-red-700 rounded text-red-100 text-sm">
                            <strong>Error:</strong> {{ elementForm.error }}
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Properties (JSON)</label>
                            <textarea
                                v-model="elementForm.properties"
                                rows="6"
                                placeholder="{}"
                                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded font-mono text-sm focus:ring-2 focus:ring-blue-500"
                            ></textarea>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Behavior (JSON Array of Animation Steps)</label>
                            <div class="mb-2 p-2 bg-blue-900 border border-blue-700 rounded text-xs text-blue-100">
                                <strong>Step types:</strong> appear, animate_property, animate, wait, set, disappear
                            </div>
                            <textarea
                                v-model="elementForm.behavior"
                                rows="8"
                                placeholder="[]"
                                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded font-mono text-sm focus:ring-2 focus:ring-blue-500"
                            ></textarea>
                        </div>
                        <div class="flex justify-end space-x-3 pt-4 border-t border-gray-700">
                            <button
                                @click="cancelEdit"
                                class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition"
                            >
                                Cancel
                            </button>
                            <button
                                @click="saveElement"
                                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
                            >
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Widget Edit Modal -->
        <div v-if="showEditWidget" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="cancelEditWidget">
            <div class="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 border border-gray-700 max-h-[90vh] overflow-y-auto">
                <div class="p-6">
                    <h3 class="text-xl font-bold mb-4 text-white">Edit Widget Configuration</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Widget Name</label>
                            <input
                                v-model="widgetForm.name"
                                type="text"
                                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:ring-2 focus:ring-blue-500 text-white"
                            >
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Widget Parameters (JSON)</label>
                            <textarea
                                v-model="widgetForm.widget_parameters"
                                rows="12"
                                placeholder="{}"
                                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded font-mono text-sm focus:ring-2 focus:ring-blue-500 text-white"
                            ></textarea>
                            <div class="mt-2 p-3 bg-gray-750 rounded border border-gray-600">
                                <p class="text-xs font-medium text-gray-400 mb-2">Default Parameters:</p>
                                <pre class="text-xs text-gray-300 font-mono overflow-x-auto">{{ JSON.stringify(getDefaultParameters(), null, 2) }}</pre>
                            </div>
                        </div>
                        <div class="flex justify-end space-x-3 pt-4 border-t border-gray-700">
                            <button
                                @click="cancelEditWidget"
                                class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition text-white"
                            >
                                Cancel
                            </button>
                            <button
                                @click="saveWidget"
                                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition text-white"
                            >
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    emits: ['remove', 'execute', 'updateElement', 'updateWidget']
};

// Export components
window.VueComponents = {
    Modal,
    ConfirmDialog,
    WidgetPanel
};
})();
