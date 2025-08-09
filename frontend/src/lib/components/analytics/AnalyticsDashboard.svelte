<script>
	import { onMount } from 'svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import MetricCard from './MetricCard.svelte';
	import ThreatHeatmap from './ThreatHeatmap.svelte';
import RiskTrendChartCanvas from './RiskTrendChartCanvas.svelte';
	import MitreCoverageChart from './MitreCoverageChart.svelte';
	import ThreatIntelFeed from './ThreatIntelFeed.svelte';
	import apiService from '$lib/api.js';

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

<div class="space-y-6">
	<!-- Header -->
	<div class="flex justify-between items-center">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Threat Intelligence Dashboard</h1>
			<p class="mt-2 text-gray-600 dark:text-gray-300">
				Real-time analytics and insights from your threat modeling projects
			</p>
		</div>
		
		<div class="flex space-x-3">
			<select 
				bind:value={selectedTimeRange} 
				on:change={loadDashboardData}
				class="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
			>
				{#each timeRanges as range}
					<option value={range.value}>{range.label}</option>
				{/each}
			</select>
			
			<button 
				on:click={loadDashboardData}
				class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
				disabled={loading}
			>
				{loading ? 'Refreshing...' : 'Refresh'}
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner />
		</div>
	{:else if error}
		<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
					</svg>
				</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error Loading Dashboard</h3>
					<p class="mt-2 text-sm text-red-700 dark:text-red-300">{error}</p>
					<button 
						on:click={loadDashboardData}
						class="mt-3 text-sm bg-red-100 dark:bg-red-800 hover:bg-red-200 dark:hover:bg-red-700 text-red-800 dark:text-red-200 px-3 py-1 rounded"
					>
						Try Again
					</button>
				</div>
			</div>
		</div>
	{:else if dashboardData}
		<!-- Key Metrics -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<MetricCard
				title="Total Projects"
				value={dashboardData.summary.totalProjects}
				subtitle="Active threat models"
				icon="📁"
				trend={null}
			/>
			<MetricCard
				title="Average Risk Score"
				value={formatPercentage(dashboardData.summary.averageRiskScore)}
				subtitle="Across all projects"
				icon="⚠️"
				trend={{ value: 0.05, direction: 'down' }}
				color="orange"
			/>
			<MetricCard
				title="Analysis Confidence"
				value={formatPercentage(dashboardData.summary.averageConfidence)}
				subtitle="AI confidence level"
				icon="🎯"
				trend={{ value: 0.12, direction: 'up' }}
				color="green"
			/>
			<MetricCard
				title="Attack Paths"
				value={dashboardData.summary.totalAttackPaths}
				subtitle="Identified threats"
				icon="🔗"
				trend={{ value: 3, direction: 'up' }}
				color="red"
			/>
		</div>

		<!-- Secondary Metrics -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
			<MetricCard
				title="MITRE Techniques"
				value={dashboardData.summary.totalTechniques}
				subtitle="Mapped to systems"
				icon="🛡️"
				size="compact"
			/>
			<MetricCard
				title="Recommendations"
				value={dashboardData.summary.totalRecommendations}
				subtitle="Security improvements"
				icon="💡"
				size="compact"
			/>
			<MetricCard
				title="Active Analyses"
				value={dashboardData.summary.runningAnalyses}
				subtitle="Currently processing"
				icon="⚡"
				color="blue"
				size="compact"
			/>
		</div>

		<!-- Navigation Tabs -->
		<div class="border-b border-gray-200 dark:border-gray-700">
			<nav class="-mb-px flex space-x-8">
				<button 
					class="py-2 px-1 border-b-2 font-medium text-sm {activeView === 'overview' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => activeView = 'overview'}
				>
					Overview
				</button>
				<button 
					class="py-2 px-1 border-b-2 font-medium text-sm {activeView === 'threats' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => activeView = 'threats'}
				>
					Threat Landscape
				</button>
				<button 
					class="py-2 px-1 border-b-2 font-medium text-sm {activeView === 'trends' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => activeView = 'trends'}
				>
					Risk Trends
				</button>
				<button 
					class="py-2 px-1 border-b-2 font-medium text-sm {activeView === 'mitre' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => activeView = 'mitre'}
				>
					MITRE Coverage
				</button>
			</nav>
		</div>

		<!-- Tab Content -->
		<div class="mt-6">
			{#if activeView === 'overview'}
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<ThreatHeatmap data={dashboardData.threatLandscape} />
					<ThreatIntelFeed />
				</div>
			{:else if activeView === 'threats'}
				<ThreatHeatmap data={dashboardData.threatLandscape} detailed={true} />
			{:else if activeView === 'trends'}
<RiskTrendChartCanvas historicalData={dashboardData.riskTrends.historical} futureData={dashboardData.riskTrends.future} />
			{:else if activeView === 'mitre'}
				<MitreCoverageChart data={dashboardData.mitreCoverage} />
			{/if}
		</div>
	{/if}
</div>
