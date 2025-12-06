// Stream Companion Admin - Main Vue App

// Check if Vue is loaded
if (typeof Vue === 'undefined') {
    console.error('Vue is not loaded! Check if the CDN is accessible.');
    document.body.innerHTML = '<div style="padding: 2rem; color: red; font-family: sans-serif;"><h1>Error: Vue.js not loaded</h1><p>The Vue.js library failed to load from the CDN. Please check your internet connection or try refreshing the page.</p></div>';
    throw new Error('Vue is not loaded');
}

const { createApp } = Vue;

// Wait for components to be available
if (!window.VueComponents) {
    console.error('VueComponents not loaded!');
}

const { Modal, WidgetPanel } = window.VueComponents || {};

const API_BASE = window.location.origin;

// API Service
class API {
    static async request(method, path, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE}${path}`, options);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        if (response.status === 204) {
            return null;
        }

        return await response.json();
    }

    // Dashboard endpoints
    static getDashboards() {
        return this.request('GET', '/api/dashboards/');
    }

    static createDashboard(data) {
        return this.request('POST', '/api/dashboards/', data);
    }

    static activateDashboard(id) {
        return this.request('POST', `/api/dashboards/${id}/activate`);
    }

    static deleteDashboard(id) {
        return this.request('DELETE', `/api/dashboards/${id}`);
    }

    static addWidgetToDashboard(dashboardId, widgetId) {
        return this.request('POST', `/api/dashboards/${dashboardId}/widgets/${widgetId}`);
    }

    static removeWidgetFromDashboard(dashboardId, widgetId) {
        return this.request('DELETE', `/api/dashboards/${dashboardId}/widgets/${widgetId}`);
    }

    // Widget endpoints
    static getWidgetTypes() {
        return this.request('GET', '/api/widgets/types');
    }

    static getAllWidgets(excludeDashboardId = null) {
        const params = excludeDashboardId ? `?exclude_dashboard_id=${excludeDashboardId}` : '';
        return this.request('GET', `/api/widgets/${params}`);
    }

    static getWidget(id) {
        return this.request('GET', `/api/widgets/${id}`);
    }

    static createWidget(data) {
        return this.request('POST', '/api/widgets/', data);
    }

    static deleteWidget(id) {
        return this.request('DELETE', `/api/widgets/${id}`);
    }

    static executeFeature(widgetId, featureName, params) {
        return this.request('POST', `/api/widgets/${widgetId}/execute`, {
            feature_name: featureName,
            feature_params: params
        });
    }
}

// Vue App
const app = createApp({
    components: {
        Modal,
        WidgetPanel
    },
    data() {
        return {
            loading: true,
            dashboards: [],
            selectedDashboard: null,
            dashboardWidgets: [],
            widgetTypes: [],
            availableWidgets: [], // Widgets not on current dashboard
            wsConnected: false,
            ws: null,
            
            // Modals
            showCreateDashboard: false,
            showAddWidget: false,
            addWidgetMode: 'existing', // 'existing' or 'new'
            
            // Forms
            newDashboard: {
                name: '',
                description: ''
            },
            newWidget: {
                widget_class: '',
                name: ''
            },
            selectedExistingWidget: null
        };
    },
    async mounted() {
        await this.loadDashboards();
        await this.loadWidgetTypes();
        this.connectWebSocket();
    },
    methods: {
        async loadDashboards() {
            this.loading = true;
            try {
                const response = await API.getDashboards();
                this.dashboards = response.dashboards;
                
                // Select first dashboard or active dashboard
                if (this.dashboards.length > 0) {
                    const active = this.dashboards.find(d => d.is_active);
                    this.selectedDashboard = active || this.dashboards[0];
                    await this.loadDashboardWidgets();
                    await this.loadAvailableWidgets();
                }
            } catch (error) {
                console.error('Error loading dashboards:', error);
                alert('Failed to load dashboards: ' + error.message);
            } finally {
                this.loading = false;
            }
        },

        async loadWidgetTypes() {
            try {
                const response = await API.getWidgetTypes();
                this.widgetTypes = response.widget_types;
            } catch (error) {
                console.error('Error loading widget types:', error);
            }
        },

        async selectDashboard(dashboard) {
            this.selectedDashboard = dashboard;
            await this.loadDashboardWidgets();
            await this.loadAvailableWidgets();
        },

        async loadDashboardWidgets() {
            if (!this.selectedDashboard) return;
            
            this.dashboardWidgets = [];
            
            try {
                // Load full widget details for each widget on dashboard
                const widgetPromises = this.selectedDashboard.widgets.map(w => 
                    API.getWidget(w.id)
                );
                this.dashboardWidgets = await Promise.all(widgetPromises);
            } catch (error) {
                console.error('Error loading dashboard widgets:', error);
            }
        },

        async loadAvailableWidgets() {
            if (!this.selectedDashboard) return;
            
            try {
                this.availableWidgets = await API.getAllWidgets(this.selectedDashboard.id);
            } catch (error) {
                console.error('Error loading available widgets:', error);
                this.availableWidgets = [];
            }
        },

        async createDashboard() {
            if (!this.newDashboard.name) return;
            
            try {
                await API.createDashboard(this.newDashboard);
                this.showCreateDashboard = false;
                this.newDashboard = { name: '', description: '' };
                await this.loadDashboards();
            } catch (error) {
                console.error('Error creating dashboard:', error);
                alert('Failed to create dashboard: ' + error.message);
            }
        },

        async activateDashboard(id) {
            try {
                await API.activateDashboard(id);
                await this.loadDashboards();
            } catch (error) {
                console.error('Error activating dashboard:', error);
                alert('Failed to activate dashboard: ' + error.message);
            }
        },

        async deleteDashboard(id) {
            if (!confirm('Are you sure you want to delete this dashboard?')) return;
            
            try {
                await API.deleteDashboard(id);
                this.selectedDashboard = null;
                await this.loadDashboards();
            } catch (error) {
                console.error('Error deleting dashboard:', error);
                alert('Failed to delete dashboard: ' + error.message);
            }
        },

        async createWidget() {
            if (!this.newWidget.widget_class || !this.newWidget.name) return;
            if (!this.selectedDashboard) return;
            
            try {
                const widgetData = {
                    widget_class: this.newWidget.widget_class,
                    name: this.newWidget.name,
                    dashboard_ids: [this.selectedDashboard.id]
                };
                
                await API.createWidget(widgetData);
                this.showAddWidget = false;
                this.newWidget = { widget_class: '', name: '' };
                await this.loadDashboards();
                await this.loadDashboardWidgets();
                await this.loadAvailableWidgets();
            } catch (error) {
                console.error('Error creating widget:', error);
                alert('Failed to create widget: ' + error.message);
            }
        },

        async addExistingWidget() {
            if (!this.selectedExistingWidget) return;
            if (!this.selectedDashboard) return;
            
            try {
                await API.addWidgetToDashboard(this.selectedDashboard.id, this.selectedExistingWidget);
                this.showAddWidget = false;
                this.selectedExistingWidget = null;
                await this.loadDashboards();
                await this.loadDashboardWidgets();
                await this.loadAvailableWidgets();
            } catch (error) {
                console.error('Error adding widget:', error);
                alert('Failed to add widget: ' + error.message);
            }
        },

        openAddWidgetModal() {
            // Default to existing if there are available widgets, otherwise new
            this.addWidgetMode = this.availableWidgets.length > 0 ? 'existing' : 'new';
            this.showAddWidget = true;
        },

        async removeWidgetFromDashboard(widgetId) {
            if (!this.selectedDashboard) return;
            if (!confirm('Remove this widget from the dashboard?')) return;
            
            try {
                await API.removeWidgetFromDashboard(this.selectedDashboard.id, widgetId);
                await this.loadDashboards();
                await this.loadDashboardWidgets();
                await this.loadAvailableWidgets();
            } catch (error) {
                console.error('Error removing widget:', error);
                alert('Failed to remove widget: ' + error.message);
            }
        },

        async executeFeature({ widgetId, featureName, params }) {
            try {
                const result = await API.executeFeature(widgetId, featureName, params);
                console.log('Feature executed:', result);
                
                // Show success notification
                this.showNotification('Feature executed successfully', 'success');
            } catch (error) {
                console.error('Error executing feature:', error);
                alert('Failed to execute feature: ' + error.message);
            }
        },

        connectWebSocket() {
            const wsUrl = `ws://${window.location.host}/ws?client_type=control`;
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.wsConnected = true;
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.wsConnected = false;
                
                // Reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WebSocket message:', data);
                
                if (data.type === 'dashboard_activated') {
                    this.loadDashboards();
                }
            };
        },

        showNotification(message, type = 'info') {
            // Simple notification - could be enhanced with a toast library
            console.log(`[${type}] ${message}`);
        }
    }
});

// Register components
if (Modal) {
    app.component('Modal', Modal);
}
if (WidgetPanel) {
    app.component('WidgetPanel', WidgetPanel);
}

// Mount the app
try {
    app.mount('#app');
    console.log('Vue app mounted successfully');
} catch (error) {
    console.error('Failed to mount Vue app:', error);
}
