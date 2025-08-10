<script>
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import LoadingSpinner from '../ui/LoadingSpinner.svelte';
	import { AIAnalysisIcon, BrainIcon, ShieldIcon, TrendingUpIcon, AlertTriangleIcon } from 'lucide-svelte';
	
	const dispatch = createEventDispatcher();
	
	export let systemDescription = '';
	export let analysisMode = 'STANDARD';
	export let context = null;
	
	let loading = false;
	let analysisResults = null;
	let error = null;
	let analysisId = null;
	
	// Analysis modes configuration
	const analysisModes = {
		LIGHTNING: {
			name: 'Lightning',
			description: 'Rapid analysis for quick assessments',
			duration: '~5 seconds',
			color: 'text-yellow-500',
			icon: '⚡'
		},
		STANDARD: {
			name: 'Standard', 
			description: 'Comprehensive pattern recognition and risk assessment',
			duration: '~15 seconds',
			color: 'text-blue-500',
			icon: '🔍'
		},
		DEEP: {
			name: 'Deep',
			description: 'Detailed technical analysis with comprehensive findings',
			duration: '~45 seconds',
			color: 'text-purple-500',
			icon: '🔬'
		},
		COMPREHENSIVE: {
			name: 'Comprehensive',
			description: 'Full-spectrum analysis with all available features',
			duration: '~90 seconds',
			color: 'text-green-500',
			icon: '🎯'
		}
	};
	
	async function performAnalysis() {
		if (!systemDescription.trim()) {
			error = 'Please provide a system description';
			return;
		}
		
		loading = true;
		error = null;
		analysisResults = null;
		
		try {
			const response = await fetch('/api/v1/enhanced-ai/analyze/advanced', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					system_description: systemDescription,
					analysis_mode: analysisMode,
					context: context,
					cache_results: true
				})
			});
			
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || `Analysis failed with status ${response.status}`);
			}
			
			analysisResults = await response.json();
			analysisId = analysisResults.analysis_id;
			
			// Dispatch event for parent components
			dispatch('analysisComplete', {
				results: analysisResults,
				mode: analysisMode
			});
			
		} catch (err) {
			error = err.message;
			console.error('Advanced AI analysis failed:', err);
		} finally {
			loading = false;
		}
	}
	
	function getRiskLevelColor(riskLevel) {
		switch (riskLevel) {
			case 'LOW': return 'text-green-500 bg-green-50';
			case 'MEDIUM': return 'text-yellow-500 bg-yellow-50';
			case 'HIGH': return 'text-orange-500 bg-orange-50';
			case 'CRITICAL': return 'text-red-500 bg-red-50';
			default: return 'text-gray-500 bg-gray-50';
		}
	}
	
	function getSeverityColor(severity) {
		switch (severity) {
			case 'low': return 'text-green-500';
			case 'medium': return 'text-yellow-500';
			case 'high': return 'text-orange-500';
			case 'critical': return 'text-red-500';
			default: return 'text-gray-500';
		}
	}
	
	function formatConfidence(confidence) {
		return `${(confidence * 100).toFixed(1)}%`;
	}
</script>

<div class="advanced-ai-analysis">
	<!-- Header -->
	<div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-lg">
		<div class="flex items-center gap-3">
			<BrainIcon size={24} />
			<div>
				<h2 class="text-xl font-bold">Enhanced AI Analysis</h2>
				<p class="text-blue-100">Advanced threat modeling with multi-model intelligence</p>
			</div>
		</div>
	</div>
	
	<div class="bg-white border-x border-b border-gray-200 rounded-b-lg">
		<!-- Input Section -->
		<div class="p-6 border-b border-gray-200">
			<div class="space-y-4">
				<!-- System Description -->
				<div>
					<label for="systemDescription" class="block text-sm font-medium text-gray-700 mb-2">
						System Description
					</label>
					<textarea
						id="systemDescription"
						bind:value={systemDescription}
						placeholder="Describe your system architecture, technologies, data flows, and security context..."
						rows="6"
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						disabled={loading}
					></textarea>
				</div>
				
				<!-- Analysis Mode Selection -->
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-3">Analysis Mode</label>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
						{#each Object.entries(analysisModes) as [mode, config]}
							<div 
								class="relative border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md {analysisMode === mode ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}"
								on:click={() => analysisMode = mode}
								role="button"
								tabindex="0"
							>
								<div class="flex items-start gap-2">
									<span class="text-lg">{config.icon}</span>
									<div class="flex-1">
										<div class="font-semibold text-sm {config.color}">{config.name}</div>
										<div class="text-xs text-gray-600 mt-1">{config.description}</div>
										<div class="text-xs text-gray-500 mt-1">{config.duration}</div>
									</div>
								</div>
								{#if analysisMode === mode}
									<div class="absolute top-2 right-2 text-blue-500">✓</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
				
				<!-- Action Button -->
				<div class="flex justify-end">
					<button
						on:click={performAnalysis}
						disabled={loading || !systemDescription.trim()}
						class="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-semibold hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
					>
						{#if loading}
							<LoadingSpinner size={16} />
							Analyzing...
						{:else}
							<AIAnalysisIcon size={16} />
							Start Advanced Analysis
						{/if}
					</button>
				</div>
			</div>
		</div>
		
		<!-- Results Section -->
		{#if error}
			<div class="p-6">
				<div class="bg-red-50 border border-red-200 rounded-lg p-4">
					<div class="flex items-start gap-3">
						<AlertTriangleIcon size={20} class="text-red-500 mt-0.5" />
						<div>
							<h3 class="font-semibold text-red-800">Analysis Failed</h3>
							<p class="text-red-700 mt-1">{error}</p>
						</div>
					</div>
				</div>
			</div>
		{/if}
		
		{#if loading}
			<div class="p-6">
				<div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
					<div class="flex items-center justify-center gap-4">
						<LoadingSpinner size={24} />
						<div class="text-center">
							<h3 class="font-semibold text-blue-800 mb-2">AI Analysis in Progress</h3>
							<p class="text-blue-700">Running {analysisModes[analysisMode].name} analysis...</p>
							<p class="text-sm text-blue-600 mt-1">Expected duration: {analysisModes[analysisMode].duration}</p>
						</div>
					</div>
				</div>
			</div>
		{/if}
		
		{#if analysisResults}
			<div class="divide-y divide-gray-200">
				<!-- Analysis Metadata -->
				<div class="p-6">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-lg font-semibold text-gray-900">Analysis Results</h3>
						<div class="flex items-center gap-4 text-sm text-gray-600">
							<span>Analysis ID: <code class="bg-gray-100 px-2 py-1 rounded">{analysisId}</code></span>
							<span>Confidence: <strong>{formatConfidence(analysisResults.analysis_metadata.confidence_score)}</strong></span>
						</div>
					</div>
					
					<!-- Risk Overview -->
					{#if analysisResults.risk_analysis?.aggregated_risk_score}
						<div class="bg-gray-50 rounded-lg p-4 mb-6">
							<div class="flex items-center justify-between mb-3">
								<h4 class="font-semibold text-gray-900">Overall Risk Assessment</h4>
								<div class="flex items-center gap-2">
									<ShieldIcon size={16} class="text-gray-500" />
									<span class="text-sm text-gray-600">ML + Intelligence Fusion</span>
								</div>
							</div>
							
							<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
								<div class="text-center">
									<div class="text-2xl font-bold {getRiskLevelColor(analysisResults.risk_analysis.aggregated_risk_score.risk_level).split(' ')[0]} mb-1">
										{(analysisResults.risk_analysis.aggregated_risk_score.final_risk_score * 100).toFixed(1)}%
									</div>
									<div class="text-sm text-gray-600">Risk Score</div>
								</div>
								<div class="text-center">
									<div class="px-3 py-1 rounded-full text-sm font-semibold {getRiskLevelColor(analysisResults.risk_analysis.aggregated_risk_score.risk_level)}">
										{analysisResults.risk_analysis.aggregated_risk_score.risk_level}
									</div>
									<div class="text-sm text-gray-600 mt-1">Risk Level</div>
								</div>
								<div class="text-center">
									<div class="text-lg font-semibold text-gray-900 mb-1">
										{formatConfidence(analysisResults.risk_analysis.aggregated_risk_score.confidence)}
									</div>
									<div class="text-sm text-gray-600">Confidence</div>
								</div>
							</div>
						</div>
					{/if}
				</div>
				
				<!-- AI Insights -->
				{#if analysisResults.ai_insights && analysisResults.ai_insights.length > 0}
					<div class="p-6">
						<h4 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
							<BrainIcon size={16} class="text-blue-500" />
							AI-Generated Insights
						</h4>
						
						<div class="space-y-4">
							{#each analysisResults.ai_insights as insight}
								<div class="border border-gray-200 rounded-lg p-4">
									<div class="flex items-start justify-between mb-2">
										<h5 class="font-semibold text-gray-900">{insight.title}</h5>
										<div class="flex items-center gap-2 text-sm">
											<span class="text-gray-500">Priority:</span>
											<span class="font-semibold" style="color: {insight.priority_score > 0.7 ? '#ef4444' : insight.priority_score > 0.5 ? '#f59e0b' : '#10b981'}">
												{(insight.priority_score * 100).toFixed(0)}%
											</span>
										</div>
									</div>
									
									<p class="text-gray-700 mb-3">{insight.description}</p>
									
									{#if insight.recommendations && insight.recommendations.length > 0}
										<div class="mt-3">
											<h6 class="font-medium text-gray-800 mb-2">Recommendations:</h6>
											<ul class="space-y-1">
												{#each insight.recommendations as recommendation}
													<li class="flex items-start gap-2 text-sm text-gray-600">
														<span class="text-blue-500 mt-0.5">•</span>
														<span>{recommendation}</span>
													</li>
												{/each}
											</ul>
										</div>
									{/if}
									
									<div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
										<span class="text-xs text-gray-500 uppercase tracking-wide">{insight.insight_type.replace('_', ' ')}</span>
										<span class="text-xs text-gray-500">Confidence: {formatConfidence(insight.confidence)}</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
				
				<!-- Threat Intelligence -->
				{#if analysisResults.threat_intelligence && analysisResults.threat_intelligence.length > 0}
					<div class="p-6">
						<h4 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
							<AlertTriangleIcon size={16} class="text-red-500" />
							Threat Intelligence
						</h4>
						
						<div class="space-y-4">
							{#each analysisResults.threat_intelligence as threat}
								<div class="border border-gray-200 rounded-lg p-4">
									<div class="flex items-center justify-between mb-2">
										<h5 class="font-semibold text-gray-900">{threat.name}</h5>
										<div class="flex items-center gap-3">
											<span class="px-2 py-1 rounded text-xs font-semibold {getSeverityColor(threat.severity)} bg-opacity-10" style="background-color: {getSeverityColor(threat.severity).replace('text-', '').replace('-500', '-100')}">
												{threat.severity.toUpperCase()}
											</span>
											<span class="text-sm text-gray-500">
												{formatConfidence(threat.confidence)}
											</span>
										</div>
									</div>
									
									{#if threat.mitre_techniques && threat.mitre_techniques.length > 0}
										<div class="mb-3">
											<span class="text-sm font-medium text-gray-700">MITRE Techniques:</span>
											<div class="flex flex-wrap gap-2 mt-1">
												{#each threat.mitre_techniques as technique}
													<code class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">{technique}</code>
												{/each}
											</div>
										</div>
									{/if}
									
									{#if threat.attack_vectors && threat.attack_vectors.length > 0}
										<div class="mb-3">
											<span class="text-sm font-medium text-gray-700">Attack Vectors:</span>
											<ul class="mt-1 space-y-1">
												{#each threat.attack_vectors as vector}
													<li class="text-sm text-gray-600 flex items-start gap-2">
														<span class="text-red-400 mt-0.5">→</span>
														{vector}
													</li>
												{/each}
											</ul>
										</div>
									{/if}
									
									<div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
										<span class="text-xs text-gray-500">
											Likelihood: {(threat.likelihood_score * 100).toFixed(0)}%
										</span>
										<span class="text-xs text-gray-500">
											ID: {threat.threat_id.split('_').slice(-2).join('_')}
										</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
				
				<!-- Pattern Analysis -->
				{#if analysisResults.pattern_analysis?.detected_patterns && analysisResults.pattern_analysis.detected_patterns.length > 0}
					<div class="p-6">
						<h4 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
							<TrendingUpIcon size={16} class="text-green-500" />
							Detected Threat Patterns
						</h4>
						
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							{#each analysisResults.pattern_analysis.detected_patterns as pattern}
								<div class="border border-gray-200 rounded-lg p-4">
									<div class="flex items-center justify-between mb-2">
										<h5 class="font-medium text-gray-900">{pattern.name}</h5>
										<span class="text-sm font-semibold text-blue-600">
											{formatConfidence(pattern.confidence)}
										</span>
									</div>
									
									{#if pattern.matched_indicators && pattern.matched_indicators.length > 0}
										<div class="mb-3">
											<span class="text-sm font-medium text-gray-700">Indicators:</span>
											<div class="flex flex-wrap gap-1 mt-1">
												{#each pattern.matched_indicators as indicator}
													<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">{indicator}</span>
												{/each}
											</div>
										</div>
									{/if}
									
									{#if pattern.mitre_techniques}
										<div class="text-sm text-gray-600">
											<span class="font-medium">Techniques:</span>
											{pattern.mitre_techniques.join(', ')}
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
				
				<!-- Technical Analysis (if available) -->
				{#if analysisResults.technical_analysis}
					<div class="p-6">
						<h4 class="font-semibold text-gray-900 mb-4">Technical Analysis</h4>
						
						{#if analysisResults.technical_analysis.technical_findings}
							<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
								{#each Object.entries(analysisResults.technical_analysis.technical_findings) as [category, findings]}
									{#if findings.length > 0}
										<div>
											<h5 class="font-medium text-gray-800 mb-2 capitalize">{category.replace('_', ' ')}</h5>
											<ul class="space-y-2">
												{#each findings as finding}
													<li class="text-sm text-gray-600 flex items-start gap-2">
														<span class="text-gray-400 mt-0.5">•</span>
														<span>{finding}</span>
													</li>
												{/each}
											</ul>
										</div>
									{/if}
								{/each}
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.advanced-ai-analysis {
		@apply max-w-6xl mx-auto;
	}
	
	/* Custom scrollbar for long content */
	:global(.advanced-ai-analysis textarea) {
		resize: vertical;
	}
	
	/* Animation for loading states */
	.loading-pulse {
		animation: pulse 2s infinite;
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}
</style>
