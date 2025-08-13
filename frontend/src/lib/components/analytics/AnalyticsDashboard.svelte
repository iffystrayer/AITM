<script>
	import { onMount } from 'svelte';
import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
import MetricCard from './MetricCard.svelte';
import EnhancedMetricCard from './EnhancedMetricCard.svelte';
import RiskChart from './RiskChart.svelte';
import ThreatDistributionChart from './ThreatDistributionChart.svelte';
import ThreatHeatmap from './ThreatHeatmap.svelte';
import RiskTrendChartCanvas from './RiskTrendChartCanvas.svelte';
import MitreCoverageChart from './MitreCoverageChart.svelte';
import ThreatIntelFeed from './ThreatIntelFeed.svelte';
	import apiService from '$lib/api.ts';

	let dashboardData = null;
	let loading = true;
	let error = null;
	let selectedTimeRange = '30d';
	let activeView = 'overview';

	const timeRanges = [
		{ value: '7d', label: '7 Days' },
		{ value: '30d', label: '30 Days' },
		{ value: '90d', label: '90 Days' },
		{ value: '1y', label: '1 Year' }
	];

	onMount(async () => {
		await loadDashboardData();
	});

	async function loadDashboardData() {
		try {
			loading = true;
			error = null;

			// Load projects and analysis data
			const [projectsResponse] = await Promise.all([
				apiService.getProjects()
			]);

			const projects = projectsResponse.data || projectsResponse;
			
			// Calculate analytics from project data
			dashboardData = await calculateAnalytics(projects);
			
		} catch (err) {
			error = err.message;
			console.error('Failed to load dashboard data:', err);
		} finally {
			loading = false;
		}
	}

	async function calculateAnalytics(projects) {
		const totalProjects = projects.length;
		const completedProjects = projects.filter(p => p.status === 'completed').length;
		const runningAnalyses = projects.filter(p => p.status === 'analyzing').length;
		const failedProjects = projects.filter(p => p.status === 'failed').length;

		// Get detailed analysis data for completed projects
		const analysisData = [];
		for (const project of projects.filter(p => p.status === 'completed')) {
			try {
				const results = await apiService.getAnalysisResults(project.id);
				analysisData.push({
					projectId: project.id,
					projectName: project.name,
					...results.data
				});
			} catch (err) {
				console.warn(`Failed to load analysis for project ${project.id}:`, err);
			}
		}

		// Calculate aggregate metrics
		const averageRiskScore = analysisData.length > 0 
			? analysisData.reduce((sum, a) => sum + a.overall_risk_score, 0) / analysisData.length
			: 0;

		const averageConfidence = analysisData.length > 0
			? analysisData.reduce((sum, a) => sum + a.confidence_score, 0) / analysisData.length
			: 0;

		const totalAttackPaths = analysisData.reduce((sum, a) => sum + (a.attack_paths?.length || 0), 0);
		const totalRecommendations = analysisData.reduce((sum, a) => sum + (a.recommendations?.length || 0), 0);
		const totalTechniques = analysisData.reduce((sum, a) => sum + (a.identified_techniques?.length || 0), 0);

		// Generate threat landscape data
		const threatLandscape = generateThreatLandscape(analysisData);
		const riskTrends = generateRiskTrends(analysisData);
		const mitreCoverage = generateMitreCoverage(analysisData);

		return {
			summary: {
				totalProjects,
				completedProjects,
				runningAnalyses,
				failedProjects,
				averageRiskScore,
				averageConfidence,
				totalAttackPaths,
				totalRecommendations,
				totalTechniques
			},
			threatLandscape,
			riskTrends,
			mitreCoverage,
			analysisData
		};
	}

	function generateThreatLandscape(analysisData) {
		const tacticCounts = {};
		const techniqueFrequency = {};

		analysisData.forEach(analysis => {
			if (analysis.identified_techniques) {
				analysis.identified_techniques.forEach(technique => {
					const tactic = technique.tactic;
					tacticCounts[tactic] = (tacticCounts[tactic] || 0) + 1;
					techniqueFrequency[technique.technique_id] = 
						(techniqueFrequency[technique.technique_id] || 0) + 1;
				});
			}
		});

		return {
			tacticCounts,
			techniqueFrequency,
			topTactics: Object.entries(tacticCounts)
				.sort(([,a], [,b]) => b - a)
				.slice(0, 10),
			topTechniques: Object.entries(techniqueFrequency)
				.sort(([,a], [,b]) => b - a)
				.slice(0, 15)
		};
	}

	function generateRiskTrends(analysisData) {
		// Mock time-series data for risk trends
		return Array.from({ length: 30 }, (_, i) => ({
			date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000),
			riskScore: Math.random() * 0.3 + 0.4, // Random between 0.4-0.7
			threats: Math.floor(Math.random() * 10) + 5,
			vulnerabilities: Math.floor(Math.random() * 15) + 8
		}));
	}

	function generateMitreCoverage(analysisData) {
		const mitreData = [
			{ tactic: 'Initial Access', techniques: 12, covered: 8 },
			{ tactic: 'Execution', techniques: 8, covered: 5 },
			{ tactic: 'Persistence', techniques: 15, covered: 9 },
			{ tactic: 'Privilege Escalation', techniques: 11, covered: 7 },
			{ tactic: 'Defense Evasion', techniques: 18, covered: 11 },
			{ tactic: 'Credential Access', techniques: 9, covered: 6 },
			{ tactic: 'Discovery', techniques: 14, covered: 10 },
			{ tactic: 'Lateral Movement', techniques: 7, covered: 4 },
			{ tactic: 'Collection', techniques: 10, covered: 6 },
			{ tactic: 'Exfiltration', techniques: 6, covered: 4 }
		];

		return mitreData.map(item => ({
			...item,
			coverage: (item.covered / item.techniques * 100).toFixed(1)
		}));
	}

	function formatNumber(num) {
		return num?.toFixed?.(2) || '0.00';
	}

	function formatPercentage(num) {
		return `${(num * 100).toFixed(1)}%`;
	}
</script>

<!-- Background with gradient and animated elements -->
<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
	<!-- Animated background elements -->
	<div class="absolute inset-0 overflow-hidden">
		<div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
		<div class="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
		<div class="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
	</div>

	<div class="relative space-y-8 p-6">
		<!-- Header -->
		<div class="flex justify-between items-center">
			<div>
				<h1 class="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
					Threat Intelligence Dashboard
				</h1>
				<p class="mt-3 text-lg text-gray-300">
					Real-time analytics and insights from your threat modeling projects
				</p>
			</div>
			
			<div class="flex space-x-4">
				<select 
					bind:value={selectedTimeRange} 
					on:change={loadDashboardData}
					class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
				>
					{#each timeRanges as range}
						<option value={range.value} class="bg-gray-800 text-white">{range.label}</option>
					{/each}
				</select>
				
				<button 
					on:click={loadDashboardData}
					class="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl hover:from-cyan-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transform transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl"
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
					<div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full mb-4">
						<svg class="animate-spin w-8 h-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
					</div>
					<p class="text-gray-300 text-lg">Loading dashboard data...</p>
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
						<h3 class="text-lg font-semibold text-red-200">Error Loading Dashboard</h3>
						<p class="mt-2 text-red-300">{error}</p>
						<button 
							on:click={loadDashboardData}
							class="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-xl transition-colors duration-200"
						>
							Try Again
						</button>
					</div>
				</div>
			</div>
		{:else if dashboardData}
			<!-- Key Metrics -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				<div class="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Total Projects</p>
							<p class="text-3xl font-bold text-white mt-2">{dashboardData.summary.totalProjects}</p>
							<p class="text-xs text-gray-400 mt-1">Active threat models</p>
						</div>
						<div class="w-12 h-12 bg-blue-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
							</svg>
						</div>
					</div>
				</div>

				<div class="bg-gradient-to-br from-orange-500/20 to-red-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Average Risk Score</p>
							<p class="text-3xl font-bold text-white mt-2">{formatPercentage(dashboardData.summary.averageRiskScore)}</p>
							<p class="text-xs text-gray-400 mt-1">Across all projects</p>
						</div>
						<div class="w-12 h-12 bg-orange-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-orange-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
							</svg>
						</div>
					</div>
				</div>

				<div class="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Analysis Confidence</p>
							<p class="text-3xl font-bold text-white mt-2">{formatPercentage(dashboardData.summary.averageConfidence)}</p>
							<p class="text-xs text-gray-400 mt-1">AI confidence level</p>
						</div>
						<div class="w-12 h-12 bg-green-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						</div>
					</div>
				</div>

				<div class="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Attack Paths</p>
							<p class="text-3xl font-bold text-white mt-2">{dashboardData.summary.totalAttackPaths}</p>
							<p class="text-xs text-gray-400 mt-1">Identified threats</p>
						</div>
						<div class="w-12 h-12 bg-purple-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			<!-- Secondary Metrics -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				<div class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-300">
					<div class="flex items-center space-x-3">
						<div class="w-10 h-10 bg-indigo-500/30 rounded-lg flex items-center justify-center">
							<svg class="w-5 h-5 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
							</svg>
						</div>
						<div>
							<p class="text-lg font-semibold text-white">{dashboardData.summary.totalTechniques}</p>
							<p class="text-sm text-gray-400">MITRE Techniques</p>
						</div>
					</div>
				</div>

				<div class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-300">
					<div class="flex items-center space-x-3">
						<div class="w-10 h-10 bg-yellow-500/30 rounded-lg flex items-center justify-center">
							<svg class="w-5 h-5 text-yellow-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
							</svg>
						</div>
						<div>
							<p class="text-lg font-semibold text-white">{dashboardData.summary.totalRecommendations}</p>
							<p class="text-sm text-gray-400">Recommendations</p>
						</div>
					</div>
				</div>

				<div class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-300">
					<div class="flex items-center space-x-3">
						<div class="w-10 h-10 bg-cyan-500/30 rounded-lg flex items-center justify-center">
							<svg class="w-5 h-5 text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
							</svg>
						</div>
						<div>
							<p class="text-lg font-semibold text-white">{dashboardData.summary.runningAnalyses}</p>
							<p class="text-sm text-gray-400">Active Analyses</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Navigation Tabs -->
			<div class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-2">
				<nav class="flex space-x-2">
					<button 
						class="px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 {activeView === 'overview' ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/10'}"
						on:click={() => activeView = 'overview'}
					>
						Overview
					</button>
					<button 
						class="px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 {activeView === 'threats' ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/10'}"
						on:click={() => activeView = 'threats'}
					>
						Threat Landscape
					</button>
					<button 
						class="px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 {activeView === 'trends' ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/10'}"
						on:click={() => activeView = 'trends'}
					>
						Risk Trends
					</button>
					<button 
						class="px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 {activeView === 'mitre' ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/10'}"
						on:click={() => activeView = 'mitre'}
					>
						MITRE Coverage
					</button>
				</nav>
			</div>

			<!-- Enhanced Charts Section -->
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
				<!-- Risk Trends Chart -->
				<div class="lg:col-span-2">
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<h2 class="text-xl font-bold text-white mb-6 flex items-center">
							<div class="w-8 h-8 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center mr-3">
								<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
								</svg>
							</div>
							Risk Score Trends
						</h2>
						<RiskChart data={dashboardData.riskTrends} height="320px" />
					</div>
				</div>

				<!-- Threat Distribution Chart -->
				<div class="lg:col-span-1">
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<h2 class="text-xl font-bold text-white mb-6 flex items-center">
							<div class="w-8 h-8 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg flex items-center justify-center mr-3">
								<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/>
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/>
								</svg>
							</div>
							Threat Categories
						</h2>
						<ThreatDistributionChart data={dashboardData.threatLandscape.topTactics.map(([tactic, count]) => ({ category: tactic, count, color: '#' + Math.floor(Math.random()*16777215).toString(16) }))} height="320px" />
					</div>
				</div>
			</div>

			<!-- Tab Content -->
			<div class="mt-8">
				{#if activeView === 'overview'}
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<ThreatHeatmap data={dashboardData.threatLandscape} />
						</div>
						<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
							<ThreatIntelFeed />
						</div>
					</div>
				{:else if activeView === 'threats'}
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<ThreatHeatmap data={dashboardData.threatLandscape} detailed={true} />
					</div>
				{:else if activeView === 'trends'}
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<RiskTrendChartCanvas historicalData={dashboardData.riskTrends.historical} futureData={dashboardData.riskTrends.future} />
					</div>
				{:else if activeView === 'mitre'}
					<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
						<MitreCoverageChart data={dashboardData.mitreCoverage} />
					</div>
				{/if}
			</div>
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
