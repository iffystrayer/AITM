<script>
	export let analysisResults = null;
	
	let activeResultsTab = 'summary'; // summary, attack-paths, techniques, recommendations, report
	
	// Helper function to get severity color
	function getSeverityColor(severity) {
		switch (severity?.toLowerCase()) {
			case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200';
			case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-200';
			case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200';
			case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200';
			default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-200';
		}
	}
	
	// Helper function to get priority color
	function getPriorityColor(priority) {
		switch (priority?.toLowerCase()) {
			case 'urgent': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200';
			case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-200';
			case 'medium': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200';
			case 'low': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-200';
			default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-200';
		}
	}
	
	// Helper function to calculate overall risk score display
	function getRiskScoreColor(score) {
		if (score >= 0.8) return 'text-red-600 dark:text-red-400';
		if (score >= 0.6) return 'text-orange-600 dark:text-orange-400';
		if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400';
		return 'text-green-600 dark:text-green-400';
	}
	
	// Download report function
	async function downloadReport() {
		try {
			// This would be implemented with the actual download endpoint
			console.log('Downloading report...', analysisResults);
			// For now, create a JSON download
			const dataStr = JSON.stringify(analysisResults, null, 2);
			const dataBlob = new Blob([dataStr], {type: 'application/json'});
			const url = URL.createObjectURL(dataBlob);
			const link = document.createElement('a');
			link.href = url;
			link.download = 'threat-analysis-report.json';
			link.click();
			URL.revokeObjectURL(url);
		} catch (err) {
			console.error('Failed to download report:', err);
		}
	}
</script>

{#if analysisResults}
	<div class="space-y-6">
		<!-- Results Navigation -->
		<div class="border-b border-gray-200 dark:border-gray-700">
			<nav class="flex space-x-8">
				<button
					class="py-2 px-1 border-b-2 font-medium text-sm {activeResultsTab === 'summary' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
					on:click={() => activeResultsTab = 'summary'}
				>
					Executive Summary
				</button>
				<button
					class="py-2 px-1 border-b-2 font-medium text-sm {activeResultsTab === 'attack-paths' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
					on:click={() => activeResultsTab = 'attack-paths'}
				>
					Attack Paths
					<span class="ml-1 inline-flex items-center justify-center w-4 h-4 text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full">
						{analysisResults.attack_paths?.length || 0}
					</span>
				</button>
				<button
					class="py-2 px-1 border-b-2 font-medium text-sm {activeResultsTab === 'techniques' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
					on:click={() => activeResultsTab = 'techniques'}
				>
					MITRE Techniques
					<span class="ml-1 inline-flex items-center justify-center w-4 h-4 text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full">
						{analysisResults.identified_techniques?.length || 0}
					</span>
				</button>
				<button
					class="py-2 px-1 border-b-2 font-medium text-sm {activeResultsTab === 'recommendations' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
					on:click={() => activeResultsTab = 'recommendations'}
				>
					Recommendations
					<span class="ml-1 inline-flex items-center justify-center w-4 h-4 text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full">
						{analysisResults.recommendations?.length || 0}
					</span>
				</button>
				<button
					class="py-2 px-1 border-b-2 font-medium text-sm {activeResultsTab === 'report' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
					on:click={() => activeResultsTab = 'report'}
				>
					Full Report
				</button>
			</nav>
		</div>

		<!-- Tab Content -->
		{#if activeResultsTab === 'summary'}
			<!-- Executive Summary -->
			<div class="space-y-6">
				<!-- Key Metrics -->
				<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
					<div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
						<h3 class="text-sm font-medium text-red-900 dark:text-red-100">Overall Risk Score</h3>
						<p class="text-2xl font-bold mt-2 {getRiskScoreColor(analysisResults.overall_risk_score || 0)}">
							{((analysisResults.overall_risk_score || 0) * 100).toFixed(0)}%
						</p>
						<p class="text-xs text-red-700 dark:text-red-300">Risk Assessment</p>
					</div>
					
					<div class="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg border border-orange-200 dark:border-orange-800">
						<h3 class="text-sm font-medium text-orange-900 dark:text-orange-100">Attack Paths</h3>
						<p class="text-2xl font-bold text-orange-600 dark:text-orange-400 mt-2">
							{analysisResults.attack_paths?.length || 0}
						</p>
						<p class="text-xs text-orange-700 dark:text-orange-300">Identified Threats</p>
					</div>
					
					<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
						<h3 class="text-sm font-medium text-blue-900 dark:text-blue-100">MITRE Techniques</h3>
						<p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">
							{analysisResults.identified_techniques?.length || 0}
						</p>
						<p class="text-xs text-blue-700 dark:text-blue-300">Unique Techniques</p>
					</div>
					
					<div class="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
						<h3 class="text-sm font-medium text-purple-900 dark:text-purple-100">Recommendations</h3>
						<p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-2">
							{analysisResults.recommendations?.length || 0}
						</p>
						<p class="text-xs text-purple-700 dark:text-purple-300">Security Actions</p>
					</div>
				</div>

				<!-- Executive Summary Content -->
				{#if analysisResults.executive_summary}
					<div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
						<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Executive Summary</h3>
						<div class="prose dark:prose-invert max-w-none">
							<p class="text-gray-700 dark:text-gray-300">{analysisResults.executive_summary.overview}</p>
							
							{#if analysisResults.executive_summary.key_findings}
								<div class="mt-4">
									<h4 class="font-semibold text-gray-900 dark:text-white">Key Findings:</h4>
									<ul class="mt-2 space-y-1">
										{#each analysisResults.executive_summary.key_findings as finding}
											<li class="text-gray-700 dark:text-gray-300">• {finding}</li>
										{/each}
									</ul>
								</div>
							{/if}

							{#if analysisResults.executive_summary.priority_actions}
								<div class="mt-4">
									<h4 class="font-semibold text-gray-900 dark:text-white">Priority Actions:</h4>
									<ul class="mt-2 space-y-1">
										{#each analysisResults.executive_summary.priority_actions as action}
											<li class="text-gray-700 dark:text-gray-300">• {action}</li>
										{/each}
									</ul>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>

		{:else if activeResultsTab === 'attack-paths'}
			<!-- Attack Paths -->
			<div class="space-y-4">
				<div class="flex justify-between items-center">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Identified Attack Paths</h3>
				</div>

				{#if analysisResults.attack_paths && analysisResults.attack_paths.length > 0}
					<div class="space-y-4">
						{#each analysisResults.attack_paths as path, i}
							<div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
								<div class="flex justify-between items-start mb-4">
									<div>
										<h4 class="text-lg font-semibold text-gray-900 dark:text-white">{path.name}</h4>
										<p class="text-sm text-gray-600 dark:text-gray-300 mt-1">{path.description}</p>
									</div>
									<div class="flex space-x-2">
										<span class="px-2 py-1 text-xs font-semibold rounded-full {getSeverityColor(path.impact)}">
											{path.impact} Impact
										</span>
										<span class="px-2 py-1 text-xs font-semibold rounded-full {getSeverityColor(path.likelihood)}">
											{path.likelihood} Likelihood
										</span>
									</div>
								</div>

								{#if path.techniques && path.techniques.length > 0}
									<div>
										<h5 class="font-medium text-gray-900 dark:text-white mb-3">Attack Steps:</h5>
										<div class="space-y-2">
											{#each path.techniques as technique}
												<div class="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
													<div class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
														<span class="text-sm font-semibold text-blue-600 dark:text-blue-400">{technique.step}</span>
													</div>
													<div class="flex-1">
														<p class="font-medium text-gray-900 dark:text-white">
															{technique.technique_id}: {technique.technique_name}
														</p>
														<p class="text-sm text-gray-600 dark:text-gray-300">
															Target: {technique.target_component}
														</p>
														{#if technique.description}
															<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{technique.description}</p>
														{/if}
													</div>
													<div class="text-xs text-gray-500 dark:text-gray-400">
														{technique.tactic}
													</div>
												</div>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-12">
						<p class="text-gray-500 dark:text-gray-400">No attack paths identified in the analysis.</p>
					</div>
				{/if}
			</div>

		{:else if activeResultsTab === 'techniques'}
			<!-- MITRE Techniques -->
			<div class="space-y-4">
				<div class="flex justify-between items-center">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">MITRE ATT&CK Techniques</h3>
				</div>

				{#if analysisResults.identified_techniques && analysisResults.identified_techniques.length > 0}
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						{#each analysisResults.identified_techniques as technique}
							<div class="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
								<div class="flex justify-between items-start mb-3">
									<div>
										<h4 class="font-semibold text-gray-900 dark:text-white">
											{technique.technique_id}: {technique.technique_name}
										</h4>
										<p class="text-sm text-gray-600 dark:text-gray-300">{technique.tactic}</p>
									</div>
									{#if technique.applicability_score}
										<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200 rounded">
											{(technique.applicability_score * 100).toFixed(0)}% relevant
										</span>
									{/if}
								</div>

								{#if technique.system_component}
									<p class="text-sm text-gray-700 dark:text-gray-300 mb-2">
										<strong>Target:</strong> {technique.system_component}
									</p>
								{/if}

								{#if technique.rationale}
									<p class="text-sm text-gray-600 dark:text-gray-400 mb-3">{technique.rationale}</p>
								{/if}

								{#if technique.prerequisites && technique.prerequisites.length > 0}
									<div>
										<p class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Prerequisites:</p>
										<div class="flex flex-wrap gap-1">
											{#each technique.prerequisites as prereq}
												<span class="px-2 py-1 text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded">
													{prereq}
												</span>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-12">
						<p class="text-gray-500 dark:text-gray-400">No MITRE techniques identified in the analysis.</p>
					</div>
				{/if}
			</div>

		{:else if activeResultsTab === 'recommendations'}
			<!-- Recommendations -->
			<div class="space-y-4">
				<div class="flex justify-between items-center">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Security Recommendations</h3>
				</div>

				{#if analysisResults.recommendations && analysisResults.recommendations.length > 0}
					<div class="space-y-4">
						{#each analysisResults.recommendations as recommendation}
							<div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
								<div class="flex justify-between items-start mb-4">
									<div class="flex-1">
										<h4 class="text-lg font-semibold text-gray-900 dark:text-white">{recommendation.title}</h4>
										<p class="text-gray-600 dark:text-gray-300 mt-2">{recommendation.description}</p>
									</div>
									<div class="ml-4 flex flex-col space-y-2">
										<span class="px-3 py-1 text-sm font-semibold rounded-full {getPriorityColor(recommendation.priority)}">
											{recommendation.priority} Priority
										</span>
										{#if recommendation.attack_technique}
											<span class="px-2 py-1 text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded">
												{recommendation.attack_technique}
											</span>
										{/if}
									</div>
								</div>

								{#if recommendation.affected_assets && recommendation.affected_assets.length > 0}
									<div class="mb-4">
										<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Affected Assets:</p>
										<div class="flex flex-wrap gap-2">
											{#each recommendation.affected_assets as asset}
												<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200 rounded">
													{asset}
												</span>
											{/each}
										</div>
									</div>
								{/if}

								<div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
									{#if recommendation.implementation_effort}
										<div>
											<p class="font-medium text-gray-700 dark:text-gray-300">Implementation Effort</p>
											<p class="text-gray-600 dark:text-gray-400">{recommendation.implementation_effort}</p>
										</div>
									{/if}
									{#if recommendation.cost_estimate}
										<div>
											<p class="font-medium text-gray-700 dark:text-gray-300">Cost Estimate</p>
											<p class="text-gray-600 dark:text-gray-400">{recommendation.cost_estimate}</p>
										</div>
									{/if}
									{#if recommendation.timeline}
										<div>
											<p class="font-medium text-gray-700 dark:text-gray-300">Timeline</p>
											<p class="text-gray-600 dark:text-gray-400">{recommendation.timeline}</p>
										</div>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-12">
						<p class="text-gray-500 dark:text-gray-400">No recommendations generated in the analysis.</p>
					</div>
				{/if}
			</div>

		{:else if activeResultsTab === 'report'}
			<!-- Full Report -->
			<div class="space-y-6">
				<div class="flex justify-between items-center">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Full Threat Analysis Report</h3>
					<button
						class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
						on:click={downloadReport}
					>
						Download Report
					</button>
				</div>

				<div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
					<div class="prose dark:prose-invert max-w-none">
						<h4>Analysis Summary</h4>
						<p>This comprehensive threat analysis was conducted using AI-powered agents and the MITRE ATT&CK framework to identify potential security risks and provide actionable recommendations.</p>
						
						<div class="grid grid-cols-2 gap-6 my-6 not-prose">
							<div>
								<h5 class="font-semibold text-gray-900 dark:text-white mb-2">Analysis Scope</h5>
								<ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
									<li>• System components analyzed: {analysisResults.system_analysis_results?.length || 0}</li>
									<li>• MITRE techniques evaluated: {analysisResults.identified_techniques?.length || 0}</li>
									<li>• Attack paths identified: {analysisResults.attack_paths?.length || 0}</li>
									<li>• Security recommendations: {analysisResults.recommendations?.length || 0}</li>
								</ul>
							</div>
							<div>
								<h5 class="font-semibold text-gray-900 dark:text-white mb-2">Risk Assessment</h5>
								<ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
									<li>• Overall Risk Score: {((analysisResults.overall_risk_score || 0) * 100).toFixed(0)}%</li>
									<li>• High Priority Issues: {analysisResults.recommendations?.filter(r => r.priority === 'high').length || 0}</li>
									<li>• Critical Techniques: {analysisResults.identified_techniques?.filter(t => t.applicability_score > 0.8).length || 0}</li>
									<li>• Analysis Confidence: {((analysisResults.confidence_score || 0) * 100).toFixed(0)}%</li>
								</ul>
							</div>
						</div>

						{#if analysisResults.report}
							<div class="mt-6 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
								<pre class="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">{JSON.stringify(analysisResults.report, null, 2)}</pre>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
{:else}
	<div class="text-center py-12">
		<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 dark:bg-gray-700">
			<svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
			</svg>
		</div>
		<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No Analysis Results</h3>
		<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
			Run a threat analysis to see detailed results here.
		</p>
	</div>
{/if}
