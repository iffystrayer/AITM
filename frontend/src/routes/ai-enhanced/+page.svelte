<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import AdvancedAIAnalysis from '$lib/components/ai/AdvancedAIAnalysis.svelte';
	import NaturalLanguageQuery from '$lib/components/ai/NaturalLanguageQuery.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import { BrainIcon, SparklesIcon, TrendingUpIcon, ShieldIcon, MessageCircleIcon, BarChart3Icon } from 'lucide-svelte';

	let activeTab = 'analysis';
	let capabilities = null;
	let trendingInsights = null;
	let loading = true;
	let analysisContext = null;

	const tabs = [
		{
			id: 'analysis',
			label: 'Advanced Analysis',
			icon: BrainIcon,
			description: 'AI-powered threat analysis with multi-model intelligence'
		},
		{
			id: 'query',
			label: 'AI Assistant',
			icon: MessageCircleIcon,
			description: 'Natural language queries about security and threats'
		},
		{
			id: 'insights',
			label: 'Trending Threats',
			icon: TrendingUpIcon,
			description: 'Latest threat intelligence and security insights'
		},
		{
			id: 'capabilities',
			label: 'AI Capabilities',
			icon: SparklesIcon,
			description: 'Available AI features and analysis modes'
		}
	];

	onMount(async () => {
		await loadCapabilities();
		await loadTrendingInsights();
		loading = false;
	});

	async function loadCapabilities() {
		try {
			const response = await fetch('/api/v1/enhanced-ai/capabilities');
			if (response.ok) {
				capabilities = await response.json();
			}
		} catch (error) {
			console.error('Failed to load AI capabilities:', error);
		}
	}

	async function loadTrendingInsights() {
		try {
			const response = await fetch('/api/v1/enhanced-ai/insights/trending?limit=5');
			if (response.ok) {
				trendingInsights = await response.json();
			}
		} catch (error) {
			console.error('Failed to load trending insights:', error);
		}
	}

	function handleAnalysisComplete(event) {
		const { results } = event.detail;
		// Update context for AI assistant
		analysisContext = {
			analysis_results: results,
			detected_patterns: results.pattern_analysis?.detected_patterns || [],
			threat_intelligence: results.threat_intelligence || [],
			ai_insights: results.ai_insights || []
		};
		
		// Optionally switch to query tab to ask follow-up questions
		// activeTab = 'query';
	}

	function getSeverityColor(severity) {
		switch (severity) {
			case 'low': return 'text-green-500 bg-green-50 border-green-200';
			case 'medium': return 'text-yellow-500 bg-yellow-50 border-yellow-200';
			case 'high': return 'text-orange-500 bg-orange-50 border-orange-200';
			case 'critical': return 'text-red-500 bg-red-50 border-red-200';
			default: return 'text-gray-500 bg-gray-50 border-gray-200';
		}
	}

	function formatConfidence(confidence) {
		return `${(confidence * 100).toFixed(1)}%`;
	}
</script>

<svelte:head>
	<title>Enhanced AI Features - AITM</title>
	<meta name="description" content="Advanced AI-powered threat analysis and security intelligence" />
</svelte:head>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white border-b border-gray-200">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="py-6">
				<div class="flex items-center gap-4">
					<div class="bg-gradient-to-r from-blue-500 to-purple-500 p-3 rounded-lg">
						<SparklesIcon size={24} class="text-white" />
					</div>
					<div>
						<h1 class="text-2xl font-bold text-gray-900">Enhanced AI Features</h1>
						<p class="text-gray-600">Advanced threat analysis with multi-model AI intelligence</p>
					</div>
				</div>
				
				<!-- Feature Stats -->
				{#if capabilities}
					<div class="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
						<div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
							<div class="flex items-center gap-2 mb-1">
								<BrainIcon size={16} class="text-blue-500" />
								<span class="text-sm font-medium text-gray-600">Analysis Modes</span>
							</div>
							<div class="text-2xl font-bold text-gray-900">{Object.keys(capabilities.analysis_modes).length}</div>
						</div>
						<div class="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4">
							<div class="flex items-center gap-2 mb-1">
								<ShieldIcon size={16} class="text-green-500" />
								<span class="text-sm font-medium text-gray-600">Threat Patterns</span>
							</div>
							<div class="text-2xl font-bold text-gray-900">{capabilities.threat_patterns.total_patterns}</div>
						</div>
						<div class="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4">
							<div class="flex items-center gap-2 mb-1">
								<SparklesIcon size={16} class="text-purple-500" />
								<span class="text-sm font-medium text-gray-600">AI Insights</span>
							</div>
							<div class="text-2xl font-bold text-gray-900">{capabilities.ai_insights.insight_types.length}</div>
						</div>
						<div class="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-4">
							<div class="flex items-center gap-2 mb-1">
								<TrendingUpIcon size={16} class="text-orange-500" />
								<span class="text-sm font-medium text-gray-600">Prediction Accuracy</span>
							</div>
							<div class="text-xl font-bold text-gray-900">85%</div>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<LoadingSpinner size={32} />
				<span class="ml-3 text-gray-600">Loading AI capabilities...</span>
			</div>
		{:else}
			<!-- Tab Navigation -->
			<div class="mb-8">
				<div class="border-b border-gray-200">
					<nav class="-mb-px flex space-x-8">
						{#each tabs as tab}
							<button
								on:click={() => activeTab = tab.id}
								class="group relative min-w-0 flex-1 overflow-hidden py-4 px-6 text-center text-sm font-medium hover:text-gray-700 focus:z-10 {activeTab === tab.id ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'} transition-colors"
							>
								<div class="flex items-center justify-center gap-2">
									<svelte:component this={tab.icon} size={18} />
									<span class="hidden sm:inline">{tab.label}</span>
								</div>
								<p class="text-xs text-gray-500 mt-1 hidden lg:block">{tab.description}</p>
							</button>
						{/each}
					</nav>
				</div>
			</div>

			<!-- Tab Content -->
			<div class="space-y-8">
				{#if activeTab === 'analysis'}
					<AdvancedAIAnalysis 
						on:analysisComplete={handleAnalysisComplete}
						systemDescription="A cloud-based e-commerce platform built with microservices architecture, using Kubernetes for orchestration, PostgreSQL for data storage, Redis for caching, and REST APIs for communication between services. The system handles customer data, payment processing, and inventory management with external integrations to payment gateways and shipping providers."
					/>
				{/if}

				{#if activeTab === 'query'}
					<NaturalLanguageQuery 
						context={analysisContext}
						placeholder="Ask me anything about cybersecurity, threat modeling, or the analysis results above..."
					/>
				{/if}

				{#if activeTab === 'insights'}
					<div class="space-y-6">
						<div class="bg-white rounded-lg border border-gray-200">
							<div class="bg-gradient-to-r from-orange-600 to-red-600 text-white p-6 rounded-t-lg">
								<div class="flex items-center gap-3">
									<TrendingUpIcon size={24} />
									<div>
										<h2 class="text-xl font-bold">Trending Threat Intelligence</h2>
										<p class="text-orange-100">Latest security threats and attack patterns</p>
									</div>
								</div>
							</div>
							
							<div class="p-6">
								{#if trendingInsights}
									<div class="space-y-4">
										{#each trendingInsights.trending_insights as insight}
											<div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
												<div class="flex items-start justify-between mb-3">
													<div class="flex-1">
														<h3 class="font-semibold text-gray-900 mb-1">{insight.title}</h3>
														<p class="text-gray-700 text-sm mb-2">{insight.description}</p>
													</div>
													<div class="ml-4 flex flex-col items-end gap-2">
														<span class="px-3 py-1 rounded-full text-xs font-semibold border {getSeverityColor(insight.severity)}">
															{insight.severity.toUpperCase()}
														</span>
														<span class="text-sm text-gray-500">
															{formatConfidence(insight.confidence)} confidence
														</span>
													</div>
												</div>
												
												<div class="flex flex-wrap gap-2 mb-3">
													<span class="text-xs text-gray-600 font-medium">Sectors:</span>
													{#each insight.affected_sectors as sector}
														<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{sector}</span>
													{/each}
												</div>
												
												<div class="flex flex-wrap gap-2 mb-3">
													<span class="text-xs text-gray-600 font-medium">MITRE:</span>
													{#each insight.mitre_techniques as technique}
														<code class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">{technique}</code>
													{/each}
												</div>
												
												<div class="flex items-center justify-between text-xs text-gray-500">
													<span>First observed: {new Date(insight.first_observed).toLocaleDateString()}</span>
													<span class="flex items-center gap-1">
														<span class="w-2 h-2 bg-green-500 rounded-full"></span>
														{insight.trend_direction}
													</span>
												</div>
											</div>
										{/each}
									</div>
									
									<div class="mt-6 text-sm text-gray-500">
										<p>Last updated: {new Date(trendingInsights.last_updated).toLocaleString()}</p>
										<p>Data sources: {trendingInsights.data_sources.join(', ')}</p>
									</div>
								{:else}
									<div class="text-center py-8">
										<TrendingUpIcon size={48} class="text-gray-300 mx-auto mb-4" />
										<p class="text-gray-500">No trending insights available</p>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/if}

				{#if activeTab === 'capabilities'}
					<div class="space-y-6">
						{#if capabilities}
							<!-- Analysis Modes -->
							<div class="bg-white rounded-lg border border-gray-200">
								<div class="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-lg">
									<h2 class="text-xl font-bold flex items-center gap-2">
										<BrainIcon size={24} />
										Analysis Modes
									</h2>
									<p class="text-purple-100">Different levels of AI analysis depth</p>
								</div>
								<div class="p-6">
									<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
										{#each Object.entries(capabilities.analysis_modes) as [mode, config]}
											<div class="border border-gray-200 rounded-lg p-4">
												<div class="flex items-center justify-between mb-3">
													<h3 class="font-semibold text-gray-900">{mode}</h3>
													<span class="text-sm text-gray-500">~{config.avg_duration_seconds}s</span>
												</div>
												<p class="text-gray-600 text-sm mb-3">{config.description}</p>
												<div class="space-y-2">
													<div>
														<span class="text-xs font-medium text-gray-500">Features:</span>
														<div class="flex flex-wrap gap-1 mt-1">
															{#each config.features as feature}
																<span class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">{feature}</span>
															{/each}
														</div>
													</div>
													<div class="flex items-center justify-between text-xs text-gray-500">
														<span>API calls: ~{config.api_calls_estimated}</span>
													</div>
												</div>
											</div>
										{/each}
									</div>
								</div>
							</div>

							<!-- Threat Patterns -->
							<div class="bg-white rounded-lg border border-gray-200">
								<div class="bg-gradient-to-r from-red-600 to-orange-600 text-white p-6 rounded-t-lg">
									<h2 class="text-xl font-bold flex items-center gap-2">
										<ShieldIcon size={24} />
										Supported Threat Patterns
									</h2>
									<p class="text-red-100">Attack patterns the AI can identify and analyze</p>
								</div>
								<div class="p-6">
									<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
										{#each capabilities.threat_patterns.supported_patterns as pattern}
											<div class="bg-gray-50 rounded-lg p-3 text-center">
												<p class="font-medium text-gray-900 text-sm">{pattern}</p>
											</div>
										{/each}
									</div>
									<div class="mt-4">
										<div class="flex flex-wrap gap-2">
											<span class="text-sm font-medium text-gray-600">Categories:</span>
											{#each capabilities.threat_patterns.pattern_categories as category}
												<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{category}</span>
											{/each}
										</div>
									</div>
								</div>
							</div>

							<!-- AI Insights -->
							<div class="bg-white rounded-lg border border-gray-200">
								<div class="bg-gradient-to-r from-green-600 to-teal-600 text-white p-6 rounded-t-lg">
									<h2 class="text-xl font-bold flex items-center gap-2">
										<SparklesIcon size={24} />
										AI Insight Types
									</h2>
									<p class="text-green-100">Types of intelligent insights the AI generates</p>
								</div>
								<div class="p-6">
									<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
										{#each capabilities.ai_insights.insight_types as insightType}
											<div class="bg-gray-50 rounded-lg p-3">
												<p class="font-medium text-gray-900 text-sm capitalize">{insightType.replace('_', ' ')}</p>
											</div>
										{/each}
									</div>
									<div class="mt-4 flex items-center justify-between text-sm text-gray-600">
										<span>Confidence threshold: {(capabilities.ai_insights.confidence_threshold * 100).toFixed(0)}%</span>
										<span>Max insights per analysis: {capabilities.ai_insights.max_insights_per_analysis}</span>
									</div>
								</div>
							</div>

							<!-- Natural Language Processing -->
							<div class="bg-white rounded-lg border border-gray-200">
								<div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-t-lg">
									<h2 class="text-xl font-bold flex items-center gap-2">
										<MessageCircleIcon size={24} />
										Natural Language Capabilities
									</h2>
									<p class="text-indigo-100">AI assistant features and supported query types</p>
								</div>
								<div class="p-6">
									<div class="space-y-4">
										<div>
											<h3 class="font-medium text-gray-900 mb-2">Supported Query Types</h3>
											<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
												{#each capabilities.natural_language.supported_queries as queryType}
													<div class="bg-gray-50 rounded-lg p-3">
														<p class="text-sm text-gray-700">{queryType}</p>
													</div>
												{/each}
											</div>
										</div>
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
											<div>
												<span class="font-medium">Languages:</span>
												{capabilities.natural_language.response_languages.join(', ')}
											</div>
											<div>
												<span class="font-medium">Max query length:</span>
												{capabilities.natural_language.max_query_length} characters
											</div>
										</div>
									</div>
								</div>
							</div>

							<!-- Risk Prediction -->
							<div class="bg-white rounded-lg border border-gray-200">
								<div class="bg-gradient-to-r from-yellow-600 to-orange-600 text-white p-6 rounded-t-lg">
									<h2 class="text-xl font-bold flex items-center gap-2">
										<BarChart3Icon size={24} />
										Risk Prediction Capabilities
									</h2>
									<p class="text-yellow-100">Predictive modeling and risk forecasting features</p>
								</div>
								<div class="p-6">
									<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
										<div>
											<h3 class="font-medium text-gray-900 mb-2">Prediction Horizons</h3>
											<div class="space-y-2">
												{#each capabilities.risk_prediction.prediction_horizons as horizon}
													<div class="bg-gray-50 rounded p-2 text-center text-sm">
														{horizon} days
													</div>
												{/each}
											</div>
										</div>
										<div>
											<h3 class="font-medium text-gray-900 mb-2">Scenario Types</h3>
											<div class="space-y-2">
												{#each capabilities.risk_prediction.scenario_types as scenario}
													<div class="bg-gray-50 rounded p-2 text-center text-sm capitalize">
														{scenario}
													</div>
												{/each}
											</div>
										</div>
										<div>
											<h3 class="font-medium text-gray-900 mb-2">Accuracy</h3>
											<div class="bg-green-50 rounded p-4 text-center">
												<div class="text-2xl font-bold text-green-600">85%</div>
												<div class="text-sm text-green-700">Historical validation</div>
											</div>
										</div>
									</div>
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	/* Custom scrollbar styles */
	:global(.overflow-y-auto) {
		scrollbar-width: thin;
		scrollbar-color: #cbd5e1 #f1f5f9;
	}
	
	:global(.overflow-y-auto)::-webkit-scrollbar {
		width: 6px;
	}
	
	:global(.overflow-y-auto)::-webkit-scrollbar-track {
		background: #f1f5f9;
	}
	
	:global(.overflow-y-auto)::-webkit-scrollbar-thumb {
		background: #cbd5e1;
		border-radius: 3px;
	}
	
	:global(.overflow-y-auto)::-webkit-scrollbar-thumb:hover {
		background: #94a3b8;
	}
</style>
