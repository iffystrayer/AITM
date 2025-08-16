<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { writable } from 'svelte/stores';
	
	// Types
	interface QualityMetrics {
		id: string;
		project_id: string;
		timestamp: string;
		code_coverage?: number;
		cyclomatic_complexity?: number;
		maintainability_index?: number;
		technical_debt_ratio?: number;
		test_quality_score?: number;
		security_score?: number;
	}
	
	interface QualityAlert {
		id: string;
		project_id: string;
		alert_type: string;
		severity: 'critical' | 'warning' | 'info';
		metric_name: string;
		current_value?: number;
		threshold_value?: number;
		message: string;
		created_at: string;
		resolved: boolean;
	}
	
	interface MonitoringStatus {
		active: boolean;
		connected_clients: number;
		update_interval_seconds: number;
		websocket_port: number;
		last_update?: string;
	}
	
	// Props
	export let projectId: string = '';
	
	// Stores
	const metrics = writable<Record<string, QualityMetrics>>({});
	const alerts = writable<QualityAlert[]>([]);
	const monitoringStatus = writable<MonitoringStatus>({
		active: false,
		connected_clients: 0,
		update_interval_seconds: 30,
		websocket_port: 8765
	});
	const connectionStatus = writable<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
	
	// WebSocket connection
	let websocket: WebSocket | null = null;
	let reconnectAttempts = 0;
	const maxReconnectAttempts = 5;
	let reconnectTimeout: NodeJS.Timeout | null = null;
	
	// Component state
	let selectedProject = projectId;
	let showResolvedAlerts = false;
	let alertFilter = 'all'; // all, critical, warning, info
	
	onMount(async () => {
		await loadMonitoringStatus();
		await loadAlerts();
		connectWebSocket();
	});
	
	onDestroy(() => {
		disconnectWebSocket();
		if (reconnectTimeout) {
			clearTimeout(reconnectTimeout);
		}
	});
	
	async function loadMonitoringStatus() {
		try {
			const response = await fetch('/api/v1/quality-monitoring/status');
			if (response.ok) {
				const status = await response.json();
				monitoringStatus.set(status);
			}
		} catch (error) {
			console.error('Failed to load monitoring status:', error);
		}
	}
	
	async function loadAlerts() {
		try {
			const params = new URLSearchParams();
			if (selectedProject) {
				params.append('project_id', selectedProject);
			}
			params.append('hours', '24');
			params.append('page_size', '100');
			
			const response = await fetch(`/api/v1/quality-monitoring/alerts?${params}`);
			if (response.ok) {
				const data = await response.json();
				alerts.set(data.alerts);
			}
		} catch (error) {
			console.error('Failed to load alerts:', error);
		}
	}
	
	function connectWebSocket() {
		if (websocket?.readyState === WebSocket.OPEN) {
			return;
		}
		
		connectionStatus.set('connecting');
		
		try {
			const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
			const wsUrl = `${protocol}//${window.location.host}/api/v1/quality-monitoring/ws`;
			
			websocket = new WebSocket(wsUrl);
			
			websocket.onopen = () => {
				console.log('WebSocket connected');
				connectionStatus.set('connected');
				reconnectAttempts = 0;
				
				// Subscribe to updates
				if (selectedProject) {
					websocket?.send(JSON.stringify({
						type: 'subscribe',
						project_ids: [selectedProject]
					}));
				}
			};
			
			websocket.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					handleWebSocketMessage(data);
				} catch (error) {
					console.error('Failed to parse WebSocket message:', error);
				}
			};
			
			websocket.onclose = () => {
				console.log('WebSocket disconnected');
				connectionStatus.set('disconnected');
				websocket = null;
				
				// Attempt to reconnect
				if (reconnectAttempts < maxReconnectAttempts) {
					reconnectAttempts++;
					const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
					
					reconnectTimeout = setTimeout(() => {
						console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})`);
						connectWebSocket();
					}, delay);
				}
			};
			
			websocket.onerror = (error) => {
				console.error('WebSocket error:', error);
				connectionStatus.set('error');
			};
			
		} catch (error) {
			console.error('Failed to connect WebSocket:', error);
			connectionStatus.set('error');
		}
	}
	
	function disconnectWebSocket() {
		if (websocket) {
			websocket.close();
			websocket = null;
		}
		connectionStatus.set('disconnected');
	}
	
	function handleWebSocketMessage(data: any) {
		switch (data.type) {
			case 'welcome':
				if (data.current_metrics) {
					metrics.set(data.current_metrics);
				}
				if (data.recent_alerts) {
					alerts.set(data.recent_alerts);
				}
				break;
				
			case 'quality_update':
				if (data.metrics) {
					metrics.update(current => ({ ...current, ...data.metrics }));
				}
				if (data.alerts && data.alerts.length > 0) {
					alerts.update(current => [...data.alerts, ...current]);
				}
				break;
				
			case 'pong':
				// Handle ping/pong for connection keepalive
				break;
				
			default:
				console.log('Unknown WebSocket message type:', data.type);
		}
	}
	
	async function startMonitoring() {
		try {
			const response = await fetch('/api/v1/quality-monitoring/start', {
				method: 'POST'
			});
			if (response.ok) {
				await loadMonitoringStatus();
				connectWebSocket();
			}
		} catch (error) {
			console.error('Failed to start monitoring:', error);
		}
	}
	
	async function stopMonitoring() {
		try {
			const response = await fetch('/api/v1/quality-monitoring/stop', {
				method: 'POST'
			});
			if (response.ok) {
				await loadMonitoringStatus();
				disconnectWebSocket();
			}
		} catch (error) {
			console.error('Failed to stop monitoring:', error);
		}
	}
	
	async function resolveAlert(alertId: string) {
		try {
			const response = await fetch(`/api/v1/quality-monitoring/alerts/${alertId}/resolve`, {
				method: 'POST'
			});
			if (response.ok) {
				alerts.update(current => 
					current.map(alert => 
						alert.id === alertId 
							? { ...alert, resolved: true }
							: alert
					)
				);
			}
		} catch (error) {
			console.error('Failed to resolve alert:', error);
		}
	}
	
	function getSeverityColor(severity: string): string {
		switch (severity) {
			case 'critical': return 'text-red-600 bg-red-50 border-red-200';
			case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
			case 'info': return 'text-blue-600 bg-blue-50 border-blue-200';
			default: return 'text-gray-600 bg-gray-50 border-gray-200';
		}
	}
	
	function getConnectionStatusColor(status: string): string {
		switch (status) {
			case 'connected': return 'text-green-600';
			case 'connecting': return 'text-yellow-600';
			case 'disconnected': return 'text-gray-600';
			case 'error': return 'text-red-600';
			default: return 'text-gray-600';
		}
	}
	
	function formatTimestamp(timestamp: string): string {
		return new Date(timestamp).toLocaleString();
	}
	
	function formatMetricValue(value: number | undefined): string {
		if (value === undefined) return 'N/A';
		return value.toFixed(2);
	}
	
	// Reactive statements
	$: filteredAlerts = $alerts.filter(alert => {
		if (!showResolvedAlerts && alert.resolved) return false;
		if (alertFilter !== 'all' && alert.severity !== alertFilter) return false;
		if (selectedProject && alert.project_id !== selectedProject) return false;
		return true;
	});
	
	$: projectMetrics = selectedProject ? $metrics[selectedProject] : null;
</script>

<div class="quality-monitoring-dashboard p-6 space-y-6">
	<!-- Header -->
	<div class="flex justify-between items-center">
		<h2 class="text-2xl font-bold text-gray-900">Quality Monitoring Dashboard</h2>
		
		<div class="flex items-center space-x-4">
			<!-- Connection Status -->
			<div class="flex items-center space-x-2">
				<div class="w-3 h-3 rounded-full {$connectionStatus === 'connected' ? 'bg-green-500' : $connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'}"></div>
				<span class="text-sm {getConnectionStatusColor($connectionStatus)}">
					{$connectionStatus.charAt(0).toUpperCase() + $connectionStatus.slice(1)}
				</span>
			</div>
			
			<!-- Monitoring Controls -->
			{#if $monitoringStatus.active}
				<button 
					on:click={stopMonitoring}
					class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
				>
					Stop Monitoring
				</button>
			{:else}
				<button 
					on:click={startMonitoring}
					class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
				>
					Start Monitoring
				</button>
			{/if}
		</div>
	</div>
	
	<!-- Monitoring Status -->
	<div class="bg-white rounded-lg shadow p-6">
		<h3 class="text-lg font-semibold mb-4">Monitoring Status</h3>
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<div class="text-center">
				<div class="text-2xl font-bold {$monitoringStatus.active ? 'text-green-600' : 'text-red-600'}">
					{$monitoringStatus.active ? 'Active' : 'Inactive'}
				</div>
				<div class="text-sm text-gray-500">Status</div>
			</div>
			<div class="text-center">
				<div class="text-2xl font-bold text-blue-600">{$monitoringStatus.connected_clients}</div>
				<div class="text-sm text-gray-500">Connected Clients</div>
			</div>
			<div class="text-center">
				<div class="text-2xl font-bold text-purple-600">{$monitoringStatus.update_interval_seconds}s</div>
				<div class="text-sm text-gray-500">Update Interval</div>
			</div>
			<div class="text-center">
				<div class="text-2xl font-bold text-indigo-600">{$monitoringStatus.websocket_port}</div>
				<div class="text-sm text-gray-500">WebSocket Port</div>
			</div>
		</div>
	</div>
	
	<!-- Project Selection -->
	<div class="bg-white rounded-lg shadow p-6">
		<h3 class="text-lg font-semibold mb-4">Project Selection</h3>
		<select 
			bind:value={selectedProject}
			on:change={loadAlerts}
			class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
		>
			<option value="">All Projects</option>
			{#each Object.keys($metrics) as projectId}
				<option value={projectId}>{projectId}</option>
			{/each}
		</select>
	</div>
	
	<!-- Current Metrics -->
	{#if projectMetrics}
		<div class="bg-white rounded-lg shadow p-6">
			<h3 class="text-lg font-semibold mb-4">Current Quality Metrics - {selectedProject}</h3>
			<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
				<div class="text-center p-4 bg-blue-50 rounded-lg">
					<div class="text-2xl font-bold text-blue-600">{formatMetricValue(projectMetrics.code_coverage)}%</div>
					<div class="text-sm text-gray-600">Code Coverage</div>
				</div>
				<div class="text-center p-4 bg-green-50 rounded-lg">
					<div class="text-2xl font-bold text-green-600">{formatMetricValue(projectMetrics.cyclomatic_complexity)}</div>
					<div class="text-sm text-gray-600">Complexity</div>
				</div>
				<div class="text-center p-4 bg-purple-50 rounded-lg">
					<div class="text-2xl font-bold text-purple-600">{formatMetricValue(projectMetrics.maintainability_index)}</div>
					<div class="text-sm text-gray-600">Maintainability</div>
				</div>
				<div class="text-center p-4 bg-yellow-50 rounded-lg">
					<div class="text-2xl font-bold text-yellow-600">{formatMetricValue(projectMetrics.technical_debt_ratio)}%</div>
					<div class="text-sm text-gray-600">Tech Debt</div>
				</div>
				<div class="text-center p-4 bg-indigo-50 rounded-lg">
					<div class="text-2xl font-bold text-indigo-600">{formatMetricValue(projectMetrics.test_quality_score)}%</div>
					<div class="text-sm text-gray-600">Test Quality</div>
				</div>
				<div class="text-center p-4 bg-red-50 rounded-lg">
					<div class="text-2xl font-bold text-red-600">{formatMetricValue(projectMetrics.security_score)}%</div>
					<div class="text-sm text-gray-600">Security</div>
				</div>
			</div>
			<div class="mt-4 text-sm text-gray-500">
				Last updated: {formatTimestamp(projectMetrics.timestamp)}
			</div>
		</div>
	{/if}
	
	<!-- Alerts Section -->
	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex justify-between items-center mb-4">
			<h3 class="text-lg font-semibold">Quality Alerts</h3>
			
			<div class="flex items-center space-x-4">
				<!-- Alert Filters -->
				<select 
					bind:value={alertFilter}
					class="p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				>
					<option value="all">All Severities</option>
					<option value="critical">Critical</option>
					<option value="warning">Warning</option>
					<option value="info">Info</option>
				</select>
				
				<!-- Show Resolved Toggle -->
				<label class="flex items-center space-x-2">
					<input 
						type="checkbox" 
						bind:checked={showResolvedAlerts}
						class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
					>
					<span class="text-sm text-gray-700">Show Resolved</span>
				</label>
			</div>
		</div>
		
		<!-- Alerts List -->
		<div class="space-y-3 max-h-96 overflow-y-auto">
			{#each filteredAlerts as alert (alert.id)}
				<div class="border rounded-lg p-4 {getSeverityColor(alert.severity)} {alert.resolved ? 'opacity-60' : ''}">
					<div class="flex justify-between items-start">
						<div class="flex-1">
							<div class="flex items-center space-x-2 mb-2">
								<span class="px-2 py-1 text-xs font-semibold rounded-full {getSeverityColor(alert.severity)}">
									{alert.severity.toUpperCase()}
								</span>
								<span class="text-sm text-gray-600">{alert.alert_type.replace('_', ' ')}</span>
								<span class="text-sm text-gray-500">•</span>
								<span class="text-sm text-gray-600">{alert.project_id}</span>
								{#if alert.resolved}
									<span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">Resolved</span>
								{/if}
							</div>
							
							<div class="font-medium text-gray-900 mb-1">{alert.message}</div>
							
							<div class="text-sm text-gray-600 space-x-4">
								<span>Metric: {alert.metric_name}</span>
								{#if alert.current_value !== undefined}
									<span>Current: {alert.current_value.toFixed(2)}</span>
								{/if}
								{#if alert.threshold_value !== undefined}
									<span>Threshold: {alert.threshold_value.toFixed(2)}</span>
								{/if}
							</div>
							
							<div class="text-xs text-gray-500 mt-2">
								{formatTimestamp(alert.created_at)}
							</div>
						</div>
						
						{#if !alert.resolved}
							<button 
								on:click={() => resolveAlert(alert.id)}
								class="ml-4 px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
							>
								Resolve
							</button>
						{/if}
					</div>
				</div>
			{:else}
				<div class="text-center py-8 text-gray-500">
					No alerts found matching the current filters.
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.quality-monitoring-dashboard {
		min-height: 100vh;
		background-color: #f9fafb;
	}
</style>