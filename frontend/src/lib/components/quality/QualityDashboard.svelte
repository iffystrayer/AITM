<script>
	import { onMount, onDestroy } from 'svelte';
	import { writable } from 'svelte/stores';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import QualityMetricCard from './QualityMetricCard.svelte';
	import QualityTrendChart from './QualityTrendChart.svelte';
	import QualityIssuesList from './QualityIssuesList.svelte';
	import QualityHeatmap from './QualityHeatmap.svelte';
	import DashboardLayout from './DashboardLayout.svelte';
	import apiService from '$lib/api.ts';

	// Props
	export let projectId = null;
	export let timeRange = '30d';
	export let metricTypes = ['all'];
	export let refreshInterval = 30000; // 30 seconds

	// State
	let qualityData = null;
	let loading = true;
	let error = null;
	let selectedView = 'overview';
	let websocket = null;
	let refreshTimer = null;

	// Reactive stores for real-time updates
	const metricsStore = writable(null);
	const issuesStore = writable([]);
	const trendsStore = writable([]);

	const timeRanges = [
		{ value: '7d', label: '7 Days' },
		{ value: '30d', label: '30 Days' },
		{ value: '90d', label: '90 Days' },
		{ value: '1y', label: '1 Year' }
	];

	const viewTabs = [
		{ id: 'overview', label: 'Overview', icon: 'dashboard' },
		{ id: 'metrics', label: 'Metrics', icon: 'chart' },
		{ id: 'issues', label: 'Issues', icon: 'warning' },
		{ id: 'trends', label: 'Trends', icon: 'trending' }
	];

	onMount(async () => {
		await loadQualityData();
		setupWebSocket();
		setupRefreshTimer();
	});

	onDestroy(() => {
		if (websocket) {
			websocket.close();
		}
		if (refreshTimer) {
			clearInterval(refreshTimer);
		}
	});

	async function loadQualityData() {
		try {
			loading = true;
			error = null;

			// Load quality metrics
			const metricsResponse = await fetchQualityMetrics();
			const issuesResponse = await fetchQualityIssues();
			const trendsResponse = await fetchQualityTrends();

			qualityData = {
				metrics: metricsResponse,
				issues: issuesResponse,
				trends: trendsResponse,
				summary: calculateSummaryMetrics(metricsResponse, issuesResponse)
			};

			// Update stores
			metricsStore.set(metricsResponse);
			issuesStore.set(issuesResponse);
			trendsStore.set(trendsResponse);

		} catch (err) {
			error = err.message;
			console.error('Failed to load quality data:', err);
		} finally {
			loading = false;
		}
	}

	async function fetchQualityMetrics() {
		// Mock implementation - replace with actual API call
		return {
			codeQuality: {
				maintainabilityIndex: 85.2,
				cyclomaticComplexity: 12.4,
				codeCoverage: 78.5,
				technicalDebt: 2.3,
				duplicateCodeRatio: 5.1
			},
			testQuality: {
				testCoverage: 78.5,
				testCount: 245,
				flakyTests: 3,
				testQualityScore: 82.1
			},
			security: {
				securityScore: 91.3,
				vulnerabilities: {
					critical: 0,
					high: 2,
					medium: 5,
					low: 12
				}
			},
			performance: {
				performanceScore: 88.7,
				bottlenecks: 4,
				memoryLeaks: 1
			}
		};
	}

	async function fetchQualityIssues() {
		try {
			const response = await apiService.client.get('/quality/issues', {
				params: {
					project_id: projectId,
					page: 1,
					page_size: 100
				}
			});
			return response.data.data?.issues || [];
		} catch (err) {
			console.warn('Failed to fetch quality issues:', err);
			// Return mock data for demo
			return [
				{
					id: '1',
					title: 'High cyclomatic complexity in auth module',
					severity: 'high',
					type: 'complexity',
					status: 'open',
					autoFixable: false,
					filePath: 'backend/app/core/auth.py',
					lineNumber: 45,
					createdAt: new Date().toISOString()
				},
				{
					id: '2',
					title: 'Missing test coverage for user service',
					severity: 'medium',
					type: 'coverage',
					status: 'open',
					autoFixable: false,
					filePath: 'backend/app/services/user_service.py',
					lineNumber: null,
					createdAt: new Date().toISOString()
				},
				{
					id: '3',
					title: 'Code formatting inconsistency',
					severity: 'low',
					type: 'style',
					status: 'open',
					autoFixable: true,
					filePath: 'backend/app/models/user.py',
					lineNumber: 23,
					createdAt: new Date().toISOString()
				}
			];
		}
	}

	async function fetchQualityTrends() {
		// Mock implementation - replace with actual API call
		const now = new Date();
		return Array.from({ length: 30 }, (_, i) => ({
			date: new Date(now.getTime() - (29 - i) * 24 * 60 * 60 * 1000),
			maintainabilityIndex: 80 + Math.random() * 10,
			codeCoverage: 70 + Math.random() * 15,
			technicalDebt: 2 + Math.random() * 2,
			securityScore: 85 + Math.random() * 10,
			issueCount: Math.floor(Math.random() * 20) + 5
		}));
	}

	function calculateSummaryMetrics(metrics, issues) {
		const openIssues = issues.filter(i => i.status === 'open').length;
		const criticalIssues = issues.filter(i => i.severity === 'critical').length;
		const autoFixableIssues = issues.filter(i => i.autoFixable).length;
		
		return {
			totalIssues: issues.length,
			openIssues,
			criticalIssues,
			autoFixableIssues,
			overallScore: calculateOverallScore(metrics),
			qualityTrend: calculateQualityTrend(metrics)
		};
	}

	function calculateOverallScore(metrics) {
		if (!metrics) return 0;
		
		const weights = {
			maintainability: 0.3,
			coverage: 0.25,
			security: 0.25,
			performance: 0.2
		};
		
		return (
			metrics.codeQuality.maintainabilityIndex * weights.maintainability +
			metrics.testQuality.testCoverage * weights.coverage +
			metrics.security.securityScore * weights.security +
			metrics.performance.performanceScore * weights.performance
		);
	}

	function calculateQualityTrend(metrics) {
		// Simplified trend calculation
		return Math.random() > 0.5 ? 'improving' : 'declining';
	}

	function setupWebSocket() {
		try {
			const wsUrl = `ws://localhost:38527/ws/quality/${projectId || 'global'}`;
			websocket = new WebSocket(wsUrl);
			
			websocket.onmessage = (event) => {
				const data = JSON.parse(event.data);
				handleRealTimeUpdate(data);
			};
			
			websocket.onerror = (error) => {
				console.warn('WebSocket error:', error);
			};
		} catch (err) {
			console.warn('Failed to setup WebSocket:', err);
		}
	}

	function handleRealTimeUpdate(data) {
		if (data.type === 'metrics_update') {
			metricsStore.update(current => ({ ...current, ...data.metrics }));
		} else if (data.type === 'issue_update') {
			issuesStore.update(current => {
				const updated = [...current];
				const index = updated.findIndex(i => i.id === data.issue.id);
				if (index >= 0) {
					updated[index] = data.issue;
				} else {
					updated.push(data.issue);
				}
				return updated;
			});
		}
	}

	function setupRefreshTimer() {
		if (refreshInterval > 0) {
			refreshTimer = setInterval(loadQualityData, refreshInterval);
		}
	}

	async function handleRefresh() {
		await loadQualityData();
	}

	function handleTimeRangeChange(event) {
		timeRange = event.target.value;
		loadQualityData();
	}

	function handleViewChange(viewId) {
		selectedView = viewId;
	}

	function formatScore(score) {
		return score?.toFixed?.(1) || '0.0';
	}

	function formatPercentage(value) {
		return `${(value || 0).toFixed(1)}%`;
	}
</script>

<!-- Quality Dashboard Container -->
<div class="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
	<!-- Animated background elements -->
	<div class="absolute inset-0 overflow-hidden">
		<div class="absolute -top-40 -right-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
		<div class="absolute -bottom-40 -left-40 w-80 h-80 bg-green-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
		<div class="absolute top-40 left-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
	</div>

	<div class="relative space-y-8 p-6">
		<!-- Header -->
		<div class="flex justify-between items-center">
			<div>
				<h1 class="text-4xl font-bold bg-gradient-to-r from-blue-400 via-green-400 to-purple-400 bg-clip-text text-transparent">
					Code Quality Dashboard
				</h1>
				<p class="mt-3 text-lg text-gray-300">
					Real-time code quality metrics, issues tracking, and automated improvements
				</p>
			</div>
			
			<div class="flex space-x-4">
				<select 
					bind:value={timeRange} 
					on:change={handleTimeRangeChange}
					class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
				>
					{#each timeRanges as range}
						<option value={range.value} class="bg-gray-800 text-white">{range.label}</option>
					{/each}
				</select>
				
				<button 
					on:click={handleRefresh}
					class="px-6 py-2 bg-gradient-to-r from-blue-500 to-green-600 text-white rounded-xl hover:from-blue-600 hover:to-green-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transform transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl"
					disabled={loading}
				>
					{#if loading}
						<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Refreshing...
					{:else}
						<span class="flex items-center">
							<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
							</svg>
							Refresh
						</span>
					{/if}
				</button>
			</div>
		</div>

		{#if loading}
			<div class="flex items-center justify-center py-16">
				<div class="text-center">
					<div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-green-600 rounded-full mb-4">
						<LoadingSpinner />
					</div>
					<p class="text-gray-300 text-lg">Loading quality metrics...</p>
				</div>
			</div>
		{:else if error}
			<div class="bg-red-500/10 backdrop-blur-sm border border-red-400/30 rounded-2xl p-8">
				<div class="flex">
					<div class="flex-shrink-0">
						<div class="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
							<svg class="w-6 h-6 text-red-400" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
							</svg>
						</div>
					</div>
					<div class="ml-4">
						<h3 class="text-lg font-semibold text-red-200">Error Loading Quality Data</h3>
						<p class="mt-2 text-red-300">{error}</p>
						<button 
							on:click={handleRefresh}
							class="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-xl transition-colors duration-200"
						>
							Try Again
						</button>
					</div>
				</div>
			</div>
		{:else if qualityData}
			<!-- Key Metrics Cards -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				<QualityMetricCard
					title="Overall Score"
					value={formatScore(qualityData.summary.overallScore)}
					unit=""
					trend={qualityData.summary.qualityTrend}
					color="blue"
					icon="star"
				/>
				<QualityMetricCard
					title="Code Coverage"
					value={formatPercentage(qualityData.metrics.testQuality.testCoverage)}
					unit=""
					trend="improving"
					color="green"
					icon="shield"
				/>
				<QualityMetricCard
					title="Open Issues"
					value={qualityData.summary.openIssues}
					unit=""
					trend={qualityData.summary.openIssues > 10 ? 'declining' : 'stable'}
					color="orange"
					icon="warning"
				/>
				<QualityMetricCard
					title="Auto-fixable"
					value={qualityData.summary.autoFixableIssues}
					unit=""
					trend="stable"
					color="purple"
					icon="wrench"
				/>
			</div>

			<!-- Navigation Tabs -->
			<div class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-2">
				<nav class="flex space-x-2">
					{#each viewTabs as tab}
						<button 
							class="px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 flex items-center space-x-2 {selectedView === tab.id ? 'bg-gradient-to-r from-blue-500 to-green-600 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/10'}"
							on:click={() => handleViewChange(tab.id)}
						>
							<span>{tab.label}</span>
						</button>
					{/each}
				</nav>
			</div>

			<!-- Dashboard Content -->
			<DashboardLayout {selectedView}>
				{#if selectedView === 'overview'}
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<h2 class="text-xl font-bold text-white mb-6">Quality Trends</h2>
							<QualityTrendChart data={qualityData.trends} height="300px" />
						</div>
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<h2 class="text-xl font-bold text-white mb-6">Quality Heatmap</h2>
							<QualityHeatmap data={qualityData.metrics} />
						</div>
					</div>
				{:else if selectedView === 'metrics'}
					<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<h3 class="text-lg font-semibold text-white mb-4">Code Quality</h3>
							<div class="space-y-4">
								<div class="flex justify-between">
									<span class="text-gray-300">Maintainability</span>
									<span class="text-white font-semibold">{formatScore(qualityData.metrics.codeQuality.maintainabilityIndex)}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-300">Complexity</span>
									<span class="text-white font-semibold">{formatScore(qualityData.metrics.codeQuality.cyclomaticComplexity)}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-300">Technical Debt</span>
									<span class="text-white font-semibold">{formatScore(qualityData.metrics.codeQuality.technicalDebt)}h</span>
								</div>
							</div>
						</div>
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<h3 class="text-lg font-semibold text-white mb-4">Test Quality</h3>
							<div class="space-y-4">
								<div class="flex justify-between">
									<span class="text-gray-300">Coverage</span>
									<span class="text-white font-semibold">{formatPercentage(qualityData.metrics.testQuality.testCoverage)}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-300">Test Count</span>
									<span class="text-white font-semibold">{qualityData.metrics.testQuality.testCount}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-300">Flaky Tests</span>
									<span class="text-white font-semibold">{qualityData.metrics.testQuality.flakyTests}</span>
								</div>
							</div>
						</div>
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<h3 class="text-lg font-semibold text-white mb-4">Security</h3>
							<div class="space-y-4">
								<div class="flex justify-between">
									<span class="text-gray-300">Security Score</span>
									<span class="text-white font-semibold">{formatScore(qualityData.metrics.security.securityScore)}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-300">Critical</span>
									<span class="text-red-400 font-semibold">{qualityData.metrics.security.vulnerabilities.critical}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-300">High</span>
									<span class="text-orange-400 font-semibold">{qualityData.metrics.security.vulnerabilities.high}</span>
								</div>
							</div>
						</div>
					</div>
				{:else if selectedView === 'issues'}
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<QualityIssuesList issues={qualityData.issues} />
					</div>
				{:else if selectedView === 'trends'}
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<QualityTrendChart data={qualityData.trends} height="400px" detailed={true} />
					</div>
				{/if}
			</DashboardLayout>
		{/if}
	</div>
</div>

<style>
	@keyframes blob {
		0% {
			transform: translate(0px, 0px) scale(1);
		}
		33% {
			transform: translate(30px, -50px) scale(1.1);
		}
		66% {
			transform: translate(-20px, 20px) scale(0.9);
		}
		100% {
			transform: translate(0px, 0px) scale(1);
		}
	}
	
	.animate-blob {
		animation: blob 7s infinite;
	}
	
	.animation-delay-2000 {
		animation-delay: 2s;
	}
	
	.animation-delay-4000 {
		animation-delay: 4s;
	}
</style>