# Frontend Documentation

## Table of Contents
- [Overview](#overview)
- [HTML Template Structure](#html-template-structure)
- [JavaScript Functions](#javascript-functions)
- [CSS Styling](#css-styling)
- [Data Visualization](#data-visualization)
- [Error Handling](#error-handling)
- [Customization Guide](#customization-guide)
- [Performance Optimization](#performance-optimization)

## Overview

The frontend of the AWS Cost Optimization Dashboard is built with vanilla HTML, CSS, and JavaScript, featuring:

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Interactive Charts**: Plotly.js for cost visualization
- **Real-time Data**: AJAX calls to backend APIs
- **User-friendly Tables**: Sortable and filterable data tables
- **Error Handling**: Graceful degradation when APIs fail

### Technology Stack
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with Flexbox and Grid
- **JavaScript (ES6+)**: Asynchronous data fetching and DOM manipulation
- **Plotly.js**: Interactive charts and graphs
- **Font Awesome** (optional): Icons for enhanced UX

## HTML Template Structure

### Main Template: `templates/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <!-- External Dependencies -->
    <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
    <!-- Internal Styles -->
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <!-- Dashboard Layout -->
    <h1>AWS Cost Optimization Dashboard</h1>
    
    <div class="container">
        <!-- Cost Chart Widget -->
        <div class="card chart-container">
            <h2>Cost Breakdown by Service</h2>
            <div id="costChart"></div>
        </div>
        
        <!-- Data Tables -->
        <div class="card table-container">
            <h2>Potentially Idle EC2 Instances</h2>
            <table id="idleInstancesTable">
                <thead>
                    <tr>
                        <th>Instance ID</th>
                        <th>Region</th>
                        <th>Avg CPU (%)</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Populated by JavaScript -->
                </tbody>
            </table>
        </div>
        
        <!-- Additional widgets... -->
    </div>
    
    <!-- Scripts -->
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
```

### Template Customization

#### Adding New Widgets

```html
<!-- Custom Widget Template -->
<div class="card widget-container">
    <div class="widget-header">
        <h2>Widget Title</h2>
        <div class="widget-controls">
            <button class="refresh-btn" onclick="refreshWidget()">
                🔄 Refresh
            </button>
            <select class="region-selector" onchange="changeRegion(this.value)">
                <option value="us-east-1">US East 1</option>
                <option value="us-west-2">US West 2</option>
            </select>
        </div>
    </div>
    <div class="widget-content">
        <div id="customWidget" class="loading">
            <div class="spinner"></div>
            <p>Loading data...</p>
        </div>
    </div>
</div>
```

#### Responsive Breakpoints

```html
<!-- Mobile-first responsive design -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<!-- Additional responsive features -->
<div class="container">
    <div class="grid-layout">
        <!-- Widgets automatically stack on mobile -->
        <div class="grid-item chart-widget">
            <!-- Chart content -->
        </div>
        <div class="grid-item table-widget">
            <!-- Table content -->
        </div>
    </div>
</div>
```

## JavaScript Functions

### Core Application: `static/script.js`

#### Application Initialization

```javascript
// Application state management
const AppState = {
    currentRegion: 'us-east-1',
    refreshInterval: 300000, // 5 minutes
    lastRefresh: null,
    activeWidgets: new Set(),
    errorCount: 0
};

// Initialize application on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('AWS Cost Dashboard initializing...');
    
    // Initialize all widgets
    initializeWidgets();
    
    // Set up periodic refresh
    setupAutoRefresh();
    
    // Set up error handling
    setupGlobalErrorHandling();
    
    console.log('Dashboard initialized successfully');
});

function initializeWidgets() {
    const widgets = [
        { name: 'costChart', initFunc: fetchCostData },
        { name: 'idleInstances', initFunc: fetchIdleInstances },
        { name: 'untaggedResources', initFunc: fetchUntaggedResources },
        { name: 'ebsOptimization', initFunc: fetchEbsOptimizationData },
        { name: 'costAnomalies', initFunc: fetchCostAnomalyData }
    ];
    
    widgets.forEach(widget => {
        try {
            AppState.activeWidgets.add(widget.name);
            widget.initFunc();
        } catch (error) {
            console.error(`Failed to initialize ${widget.name}:`, error);
            showWidgetError(widget.name, error.message);
        }
    });
}
```

#### Data Fetching with Error Handling

```javascript
// Enhanced fetch function with retry logic
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.warn(`Fetch attempt ${attempt} failed:`, error.message);
            
            if (attempt === maxRetries) {
                throw error;
            }
            
            // Exponential backoff
            await new Promise(resolve => 
                setTimeout(resolve, Math.pow(2, attempt) * 1000)
            );
        }
    }
}

// Cost data fetching with caching
let costDataCache = {
    data: null,
    timestamp: null,
    ttl: 60000 // 1 minute TTL
};

async function fetchCostData(forceRefresh = false) {
    const widgetId = 'costChart';
    
    try {
        // Check cache first
        if (!forceRefresh && costDataCache.data && 
            Date.now() - costDataCache.timestamp < costDataCache.ttl) {
            renderCostChart(costDataCache.data);
            return;
        }
        
        showLoadingState(widgetId);
        
        const data = await fetchWithRetry('/api/cost-by-service');
        
        // Update cache
        costDataCache = {
            data: data,
            timestamp: Date.now(),
            ttl: 60000
        };
        
        renderCostChart(data);
        updateWidgetTimestamp(widgetId);
        
    } catch (error) {
        console.error('Error fetching cost data:', error);
        showWidgetError(widgetId, 'Failed to load cost data');
        AppState.errorCount++;
    }
}

// Idle instances with advanced filtering
async function fetchIdleInstances(region = AppState.currentRegion) {
    const widgetId = 'idleInstances';
    
    try {
        showLoadingState(widgetId);
        
        const data = await fetchWithRetry('/api/idle-instances');
        
        // Filter by region if specified
        const filteredData = region === 'all' ? data : 
            data.filter(instance => instance.Region === region);
        
        renderIdleInstancesTable(filteredData);
        updateWidgetTimestamp(widgetId);
        
        // Update summary stats
        updateIdleInstancesSummary(filteredData);
        
    } catch (error) {
        console.error('Error fetching idle instances:', error);
        showWidgetError(widgetId, 'Failed to load idle instances');
    }
}
```

#### Advanced Table Rendering

```javascript
// Enhanced table rendering with sorting and filtering
function renderIdleInstancesTable(instances) {
    const tableBody = document.querySelector('#idleInstancesTable tbody');
    
    if (!instances || instances.length === 0) {
        tableBody.innerHTML = `
            <tr class="no-data-row">
                <td colspan="4">
                    <div class="no-data-message">
                        <span class="icon">✓</span>
                        <span>No idle instances found</span>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort instances by average CPU (lowest first)
    const sortedInstances = instances.sort((a, b) => a.AvgCPU - b.AvgCPU);
    
    tableBody.innerHTML = sortedInstances.map(instance => `
        <tr class="data-row" data-instance-id="${instance.InstanceId}">
            <td>
                <span class="instance-id">${instance.InstanceId}</span>
                <button class="copy-btn" onclick="copyToClipboard('${instance.InstanceId}')" 
                        title="Copy Instance ID">📋</button>
            </td>
            <td>
                <span class="region-badge">${instance.Region}</span>
            </td>
            <td>
                <span class="cpu-percentage ${getCpuSeverityClass(instance.AvgCPU)}">
                    ${instance.AvgCPU.toFixed(1)}%
                </span>
            </td>
            <td>
                <span class="reason-text">${instance.Reason}</span>
            </td>
        </tr>
    `).join('');
    
    // Add click handlers for row details
    addTableRowHandlers('idleInstancesTable');
}

function getCpuSeverityClass(cpuPercent) {
    if (cpuPercent < 1) return 'cpu-very-low';
    if (cpuPercent < 3) return 'cpu-low';
    if (cpuPercent < 5) return 'cpu-medium';
    return 'cpu-normal';
}

// Interactive table features
function addTableRowHandlers(tableId) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr.data-row');
    
    rows.forEach(row => {
        row.addEventListener('click', function() {
            const instanceId = this.dataset.instanceId;
            if (instanceId) {
                showInstanceDetails(instanceId);
            }
        });
        
        // Hover effects
        row.addEventListener('mouseenter', function() {
            this.classList.add('row-hover');
        });
        
        row.addEventListener('mouseleave', function() {
            this.classList.remove('row-hover');
        });
    });
}

// Instance details modal
function showInstanceDetails(instanceId) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Instance Details: ${instanceId}</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="loading-spinner">Loading instance details...</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Fetch detailed instance information
    fetchInstanceDetails(instanceId)
        .then(details => {
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = renderInstanceDetails(details);
        })
        .catch(error => {
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = `<p class="error">Failed to load details: ${error.message}</p>`;
        });
}
```

#### Chart Visualization

```javascript
// Advanced chart rendering with Plotly.js
function renderCostChart(data) {
    const chartDiv = document.getElementById('costChart');
    
    if (!data || Object.keys(data).length === 0) {
        chartDiv.innerHTML = `
            <div class="no-data-chart">
                <span class="icon">📊</span>
                <p>No cost data available</p>
            </div>
        `;
        return;
    }
    
    // Prepare data for visualization
    const services = Object.keys(data);
    const costs = Object.values(data);
    const totalCost = costs.reduce((sum, cost) => sum + cost, 0);
    
    // Create color scheme based on cost magnitude
    const colors = generateColorScheme(costs.length);
    
    const plotData = [{
        values: costs,
        labels: services,
        type: 'pie',
        hole: 0.4,
        textinfo: 'label+percent+value',
        texttemplate: '%{label}<br>%{percent}<br>$%{value:.2f}',
        hovertemplate: '<b>%{label}</b><br>Cost: $%{value:.2f}<br>Percentage: %{percent}<extra></extra>',
        marker: {
            colors: colors,
            line: {
                color: '#FFFFFF',
                width: 2
            }
        },
        pull: costs.map(cost => cost === Math.max(...costs) ? 0.1 : 0) // Highlight largest segment
    }];
    
    const layout = {
        title: {
            text: `Total Cost: $${totalCost.toFixed(2)}`,
            font: { size: 18, family: 'Arial, sans-serif' }
        },
        height: 400,
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1,
            y: 0.5
        },
        margin: { t: 60, b: 40, l: 40, r: 120 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(chartDiv, plotData, layout, config);
    
    // Add click event for drill-down
    chartDiv.on('plotly_click', function(data) {
        const clickedService = data.points[0].label;
        showServiceDetails(clickedService, data.points[0].value);
    });
}

function generateColorScheme(count) {
    // Generate a harmonious color scheme
    const baseColors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
        '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'
    ];
    
    if (count <= baseColors.length) {
        return baseColors.slice(0, count);
    }
    
    // Generate additional colors if needed
    const colors = [...baseColors];
    for (let i = baseColors.length; i < count; i++) {
        colors.push(`hsl(${(i * 137.508) % 360}, 70%, 60%)`);
    }
    
    return colors;
}
```

#### Real-time Updates

```javascript
// Auto-refresh functionality
function setupAutoRefresh() {
    const refreshInterval = AppState.refreshInterval;
    
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            refreshAllWidgets();
        }
    }, refreshInterval);
    
    // Refresh when page becomes visible
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && 
            Date.now() - AppState.lastRefresh > 60000) {
            refreshAllWidgets();
        }
    });
}

function refreshAllWidgets() {
    console.log('Refreshing all widgets...');
    AppState.lastRefresh = Date.now();
    
    // Show refresh indicator
    showRefreshIndicator();
    
    const refreshPromises = [
        fetchCostData(true),
        fetchIdleInstances(),
        fetchUntaggedResources(),
        fetchEbsOptimizationData(),
        fetchCostAnomalyData()
    ];
    
    Promise.allSettled(refreshPromises)
        .then(results => {
            const failures = results.filter(r => r.status === 'rejected');
            if (failures.length > 0) {
                console.warn(`${failures.length} widgets failed to refresh`);
            }
        })
        .finally(() => {
            hideRefreshIndicator();
        });
}

// Manual refresh button
function addRefreshControls() {
    const header = document.querySelector('h1');
    const refreshButton = document.createElement('button');
    refreshButton.className = 'refresh-button';
    refreshButton.innerHTML = '🔄 Refresh All';
    refreshButton.onclick = refreshAllWidgets;
    
    const lastUpdate = document.createElement('span');
    lastUpdate.className = 'last-update';
    lastUpdate.id = 'lastUpdateTime';
    
    const controls = document.createElement('div');
    controls.className = 'dashboard-controls';
    controls.appendChild(refreshButton);
    controls.appendChild(lastUpdate);
    
    header.after(controls);
    
    updateLastRefreshTime();
}
```

## CSS Styling

### Main Stylesheet: `static/style.css`

#### Responsive Grid Layout

```css
/* CSS Variables for theming */
:root {
    --primary-color: #2C3E50;
    --secondary-color: #3498DB;
    --success-color: #27AE60;
    --warning-color: #F39C12;
    --danger-color: #E74C3C;
    --background-color: #F8F9FA;
    --card-background: #FFFFFF;
    --text-color: #2C3E50;
    --border-color: #E9ECEF;
    --border-radius: 8px;
    --box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    --transition: all 0.3s ease;
}

/* Dark theme support */
@media (prefers-color-scheme: dark) {
    :root {
        --background-color: #1A1A1A;
        --card-background: #2D2D2D;
        --text-color: #E0E0E0;
        --border-color: #404040;
        --box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
}

/* Base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    line-height: 1.6;
}

/* Container and layout */
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
}

@media (max-width: 768px) {
    .container {
        grid-template-columns: 1fr;
        padding: 10px;
        gap: 15px;
    }
}

/* Card styling */
.card {
    background: var(--card-background);
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 20px;
    transition: var(--transition);
    border: 1px solid var(--border-color);
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.card h2 {
    margin-bottom: 15px;
    color: var(--primary-color);
    font-size: 1.4rem;
    border-bottom: 2px solid var(--secondary-color);
    padding-bottom: 8px;
}
```

#### Widget-specific Styling

```css
/* Chart container */
.chart-container {
    min-height: 450px;
    grid-column: span 2;
}

@media (max-width: 1024px) {
    .chart-container {
        grid-column: span 1;
    }
}

.chart-container #costChart {
    width: 100%;
    height: 400px;
}

/* Table styling */
.table-container {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
}

thead {
    background-color: var(--secondary-color);
    color: white;
}

th, td {
    padding: 12px 8px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
}

tbody tr:hover {
    background-color: rgba(52, 152, 219, 0.1);
    cursor: pointer;
}

/* Status badges */
.cpu-very-low { color: var(--success-color); font-weight: bold; }
.cpu-low { color: var(--warning-color); font-weight: bold; }
.cpu-medium { color: var(--danger-color); }

.region-badge {
    background-color: var(--secondary-color);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
}

/* Loading states */
.loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    color: var(--text-color);
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color);
    border-top: 4px solid var(--secondary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Error states */
.error-state {
    background-color: rgba(231, 76, 60, 0.1);
    border: 1px solid var(--danger-color);
    color: var(--danger-color);
    padding: 20px;
    border-radius: var(--border-radius);
    text-align: center;
}

.error-state .icon {
    font-size: 2rem;
    margin-bottom: 10px;
    display: block;
}

/* Modal styling */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: var(--card-background);
    border-radius: var(--border-radius);
    max-width: 90%;
    max-height: 90%;
    overflow-y: auto;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-color);
}

.modal-body {
    padding: 20px;
}
```

#### Interactive Elements

```css
/* Buttons */
.btn {
    background-color: var(--secondary-color);
    color: white;
    border: none;
    padding: 10px 16px;
    border-radius: var(--border-radius);
    cursor: pointer;
    font-size: 0.9rem;
    transition: var(--transition);
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.btn:hover {
    background-color: #2980B9;
    transform: translateY(-1px);
}

.btn:active {
    transform: translateY(0);
}

.btn-small {
    padding: 6px 10px;
    font-size: 0.8rem;
}

.copy-btn {
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0.6;
    margin-left: 8px;
    transition: var(--transition);
}

.copy-btn:hover {
    opacity: 1;
    transform: scale(1.1);
}

/* Dashboard controls */
.dashboard-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 20px auto;
    max-width: 1400px;
    padding: 0 20px;
}

.refresh-button {
    background-color: var(--success-color);
}

.last-update {
    color: var(--text-color);
    font-size: 0.9rem;
    opacity: 0.8;
}

/* Responsive utilities */
@media (max-width: 480px) {
    .card {
        padding: 15px;
    }
    
    .card h2 {
        font-size: 1.2rem;
    }
    
    th, td {
        padding: 8px 4px;
        font-size: 0.9rem;
    }
    
    .dashboard-controls {
        flex-direction: column;
        gap: 10px;
    }
}

/* Print styles */
@media print {
    .dashboard-controls,
    .copy-btn,
    .btn {
        display: none !important;
    }
    
    .card {
        break-inside: avoid;
        box-shadow: none;
        border: 1px solid #000;
    }
    
    body {
        background: white;
        color: black;
    }
}
```

## Data Visualization

### Advanced Chart Configurations

```javascript
// Cost trend analysis chart
function renderCostTrendChart(dailyCostData) {
    const dates = Object.keys(dailyCostData);
    const costs = Object.values(dailyCostData);
    
    const trace = {
        x: dates,
        y: costs,
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#3498DB',
            width: 3
        },
        marker: {
            size: 6,
            color: '#2980B9'
        },
        hovertemplate: '<b>%{x}</b><br>Cost: $%{y:.2f}<extra></extra>'
    };
    
    const layout = {
        title: 'Daily Cost Trend',
        xaxis: {
            title: 'Date',
            type: 'date'
        },
        yaxis: {
            title: 'Cost ($)',
            tickformat: '$,.0f'
        },
        hovermode: 'closest'
    };
    
    Plotly.newPlot('costTrendChart', [trace], layout);
}

// Multi-region comparison chart
function renderRegionComparisonChart(regionData) {
    const regions = Object.keys(regionData);
    const idleCounts = regions.map(region => regionData[region].idleInstances);
    const untaggedCounts = regions.map(region => regionData[region].untaggedResources);
    
    const data = [
        {
            x: regions,
            y: idleCounts,
            name: 'Idle Instances',
            type: 'bar',
            marker: { color: '#E74C3C' }
        },
        {
            x: regions,
            y: untaggedCounts,
            name: 'Untagged Resources',
            type: 'bar',
            marker: { color: '#F39C12' }
        }
    ];
    
    const layout = {
        title: 'Optimization Opportunities by Region',
        barmode: 'group',
        xaxis: { title: 'AWS Region' },
        yaxis: { title: 'Count' }
    };
    
    Plotly.newPlot('regionComparisonChart', data, layout);
}
```

## Error Handling

### Comprehensive Error Management

```javascript
// Global error handling setup
function setupGlobalErrorHandling() {
    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showGlobalError('An unexpected error occurred. Please refresh the page.');
        event.preventDefault();
    });
    
    // Catch JavaScript errors
    window.addEventListener('error', function(event) {
        console.error('JavaScript error:', event.error);
        showGlobalError('A script error occurred. Some features may not work properly.');
    });
}

// Widget-specific error handling
function showWidgetError(widgetId, message) {
    const widget = document.getElementById(widgetId);
    if (!widget) return;
    
    widget.innerHTML = `
        <div class="error-state">
            <span class="icon">⚠️</span>
            <h3>Error Loading Data</h3>
            <p>${message}</p>
            <button class="btn btn-small" onclick="retryWidget('${widgetId}')">
                🔄 Retry
            </button>
        </div>
    `;
}

// Retry mechanism
function retryWidget(widgetId) {
    const retryFunctions = {
        'costChart': () => fetchCostData(true),
        'idleInstances': fetchIdleInstances,
        'untaggedResources': fetchUntaggedResources,
        'ebsOptimization': fetchEbsOptimizationData,
        'costAnomalies': fetchCostAnomalyData
    };
    
    const retryFunction = retryFunctions[widgetId];
    if (retryFunction) {
        retryFunction();
    }
}

// Network connectivity check
function checkConnectivity() {
    return fetch('/api/health-check', { 
        method: 'HEAD',
        cache: 'no-cache'
    })
    .then(response => response.ok)
    .catch(() => false);
}

// Offline handling
window.addEventListener('online', function() {
    console.log('Connection restored');
    refreshAllWidgets();
    hideOfflineIndicator();
});

window.addEventListener('offline', function() {
    console.log('Connection lost');
    showOfflineIndicator();
});
```

## Customization Guide

### Theme Customization

```css
/* Custom theme example */
.theme-dark {
    --primary-color: #BB86FC;
    --secondary-color: #03DAC6;
    --background-color: #121212;
    --card-background: #1E1E1E;
    --text-color: #FFFFFF;
    --border-color: #333333;
}

.theme-corporate {
    --primary-color: #1F4E79;
    --secondary-color: #2E86AB;
    --success-color: #A23B72;
    --warning-color: #F18F01;
    --danger-color: #C73E1D;
}
```

### Widget Customization

```javascript
// Custom widget template
class CustomWidget {
    constructor(containerId, apiEndpoint) {
        this.container = document.getElementById(containerId);
        this.apiEndpoint = apiEndpoint;
        this.data = null;
        this.isLoading = false;
    }
    
    async render() {
        this.showLoading();
        
        try {
            this.data = await fetchWithRetry(this.apiEndpoint);
            this.renderContent();
        } catch (error) {
            this.showError(error.message);
        }
    }
    
    showLoading() {
        this.container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        `;
    }
    
    renderContent() {
        // Override in subclass
        this.container.innerHTML = '<p>No content renderer defined</p>';
    }
    
    showError(message) {
        this.container.innerHTML = `
            <div class="error-state">
                <span class="icon">⚠️</span>
                <p>${message}</p>
                <button onclick="this.render()">Retry</button>
            </div>
        `;
    }
}

// Usage example
class CostSummaryWidget extends CustomWidget {
    renderContent() {
        const totalCost = Object.values(this.data).reduce((sum, cost) => sum + cost, 0);
        const serviceCount = Object.keys(this.data).length;
        
        this.container.innerHTML = `
            <div class="summary-widget">
                <div class="summary-item">
                    <h3>$${totalCost.toFixed(2)}</h3>
                    <p>Total Monthly Cost</p>
                </div>
                <div class="summary-item">
                    <h3>${serviceCount}</h3>
                    <p>Active Services</p>
                </div>
            </div>
        `;
    }
}
```

## Performance Optimization

### Lazy Loading and Code Splitting

```javascript
// Lazy load heavy components
const LazyLoader = {
    async loadPlotly() {
        if (window.Plotly) return window.Plotly;
        
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.plot.ly/plotly-latest.min.js';
            script.onload = () => resolve(window.Plotly);
            script.onerror = reject;
            document.head.appendChild(script);
        });
    },
    
    async loadWidget(widgetName) {
        const widgetModules = {
            'advanced-charts': () => import('./widgets/advanced-charts.js'),
            'data-export': () => import('./widgets/data-export.js'),
            'custom-filters': () => import('./widgets/custom-filters.js')
        };
        
        const moduleLoader = widgetModules[widgetName];
        if (moduleLoader) {
            return await moduleLoader();
        }
        throw new Error(`Widget ${widgetName} not found`);
    }
};

// Intersection Observer for lazy loading
const observeWidgets = () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const widgetId = entry.target.id;
                initializeWidget(widgetId);
                observer.unobserve(entry.target);
            }
        });
    });
    
    document.querySelectorAll('.lazy-widget').forEach(widget => {
        observer.observe(widget);
    });
};

// Virtual scrolling for large tables
class VirtualTable {
    constructor(containerId, data, rowHeight = 40) {
        this.container = document.getElementById(containerId);
        this.data = data;
        this.rowHeight = rowHeight;
        this.visibleRows = Math.ceil(this.container.clientHeight / rowHeight) + 2;
        this.scrollTop = 0;
        
        this.init();
    }
    
    init() {
        this.container.innerHTML = `
            <div class="virtual-table-wrapper" style="height: ${this.data.length * this.rowHeight}px;">
                <div class="virtual-table-content"></div>
            </div>
        `;
        
        this.wrapper = this.container.querySelector('.virtual-table-wrapper');
        this.content = this.container.querySelector('.virtual-table-content');
        
        this.container.addEventListener('scroll', () => this.handleScroll());
        this.render();
    }
    
    handleScroll() {
        this.scrollTop = this.container.scrollTop;
        this.render();
    }
    
    render() {
        const startIndex = Math.floor(this.scrollTop / this.rowHeight);
        const endIndex = Math.min(startIndex + this.visibleRows, this.data.length);
        
        this.content.style.transform = `translateY(${startIndex * this.rowHeight}px)`;
        this.content.innerHTML = this.data
            .slice(startIndex, endIndex)
            .map(item => this.renderRow(item))
            .join('');
    }
    
    renderRow(item) {
        return `<div class="virtual-row" style="height: ${this.rowHeight}px;">${item.content}</div>`;
    }
}
```

This comprehensive frontend documentation provides detailed guidance for understanding, customizing, and extending the dashboard's user interface. It includes responsive design patterns, interactive features, error handling strategies, and performance optimization techniques.