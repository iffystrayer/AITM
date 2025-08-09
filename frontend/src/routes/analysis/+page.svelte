<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	let projects = [];
	let selectedProject = null;
	let analysisStatus = 'idle';
	let analysisResults = null;
	let loading = false;
	let showConfig = false;

	onMount(() => {
		currentPage.set('analysis');
		loadProjects();
	});

	async function loadProjects() {
		try {
			const response = await fetch('http://localhost:38527/api/v1/projects/');
			if (response.ok) {
				projects = await response.json();
			}
		} catch (err) {
			console.error('Failed to load projects:', err);
		}
	}

	async function startAnalysis() {
		if (!selectedProject) return;
		
		loading = true;
		analysisStatus = 'running';
		
		// Simulate analysis process
		setTimeout(() => {
			analysisStatus = 'completed';
			analysisResults = {
				threatCount: Math.floor(Math.random() * 15) + 5,
				riskScore: Math.floor(Math.random() * 40) + 60,
				mitigations: Math.floor(Math.random() * 8) + 4,
				attackPaths: Math.floor(Math.random() * 6) + 2
			};
			loading = false;
		}, 3000);
	}

	function resetAnalysis() {
		analysisStatus = 'idle';
		analysisResults = null;
		selectedProject = null;
		showConfig = false;
	}
</script>

<svelte:head>
	<title>Threat Analysis - AITM</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<div class="flex justify-between items-center">
			<div>
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Threat Analysis</h2>
				<p class="text-gray-600 dark:text-gray-300">
					AI-powered threat analysis workspace with multi-agent system
				</p>
			</div>
			<div class="flex space-x-3">
				<button 
					class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
					on:click={() => showConfig = true}
					disabled={loading}
				>
					🎯 New Analysis
				</button>
				{#if analysisResults}
					<button 
						class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
						on:click={resetAnalysis}
					>
						🔄 Reset
					</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- Analysis Configuration Modal -->
	{#if showConfig}
		<div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Configure Analysis</h3>
				
				<div class="space-y-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Select Project</label>
						<select 
							bind:value={selectedProject}
							class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						>
							<option value={null}>Choose a project...</option>
							{#each projects as project}
								<option value={project}>{project.name}</option>
							{/each}
						</select>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Analysis Depth</label>
						<select class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
							<option value="basic">Basic Analysis</option>
							<option value="standard" selected>Standard Analysis</option>
							<option value="comprehensive">Comprehensive Analysis</option>
						</select>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">LLM Provider</label>
						<select class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
							<option value="gemini" selected>Google Gemini</option>
							<option value="openai">OpenAI GPT</option>
							<option value="ollama">Ollama (Local)</option>
						</select>
					</div>
				</div>

				<div class="flex justify-end space-x-3 mt-6">
					<button
						type="button"
						class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
						on:click={() => showConfig = false}
					>
						Cancel
					</button>
					<button
						type="button"
						class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
						on:click={() => { showConfig = false; startAnalysis(); }}
						disabled={!selectedProject}
					>
						Start Analysis
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Analysis Status -->
	{#if analysisStatus !== 'idle'}
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Analysis Status</h3>
			
			{#if analysisStatus === 'running'}
				<div class="space-y-4">
					<div class="flex items-center space-x-3">
						<div class="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
						<span class="text-blue-600 font-medium">Analyzing: {selectedProject.name}</span>
					</div>
					<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
						<h4 class="font-medium text-blue-900 dark:text-blue-200 mb-2">Multi-Agent Analysis in Progress</h4>
						<ul class="text-sm text-blue-800 dark:text-blue-300 space-y-1">
							<li>🤖 System Analyst Agent: Parsing system architecture...</li>
							<li>🎯 ATT&CK Mapper Agent: Identifying threat techniques...</li>
							<li>🛡️ Control Evaluation Agent: Assessing security controls...</li>
						</ul>
					</div>
				</div>
			{:else if analysisStatus === 'completed'}
				<div class="space-y-4">
					<div class="flex items-center space-x-3">
						<div class="h-5 w-5 bg-green-500 rounded-full flex items-center justify-center">
							<svg class="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
							</svg>
						</div>
						<span class="text-green-600 font-medium">Analysis Complete: {selectedProject.name}</span>
					</div>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Analysis Results -->
	{#if analysisResults}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-red-100 rounded-md flex items-center justify-center">
							<span class="text-red-600 text-lg">⚠️</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Threats Identified</dt>
							<dd class="text-2xl font-bold text-gray-900 dark:text-white">{analysisResults.threatCount}</dd>
						</dl>
					</div>
				</div>
			</div>

			<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-orange-100 rounded-md flex items-center justify-center">
							<span class="text-orange-600 text-lg">📊</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Risk Score</dt>
							<dd class="text-2xl font-bold text-gray-900 dark:text-white">{analysisResults.riskScore}/100</dd>
						</dl>
					</div>
				</div>
			</div>

			<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
							<span class="text-blue-600 text-lg">🛡️</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Mitigations</dt>
							<dd class="text-2xl font-bold text-gray-900 dark:text-white">{analysisResults.mitigations}</dd>
						</dl>
					</div>
				</div>
			</div>

			<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
							<span class="text-purple-600 text-lg">🎯</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Attack Paths</dt>
							<dd class="text-2xl font-bold text-gray-900 dark:text-white">{analysisResults.attackPaths}</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>

		<!-- Detailed Results -->
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Analysis Details</h3>
			
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<div>
					<h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">🎯 Top Attack Techniques</h4>
					<div class="space-y-2">
						<div class="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
							<div class="flex justify-between items-center">
								<span class="font-medium text-red-900 dark:text-red-200">T1059.001 - PowerShell</span>
								<span class="text-sm text-red-700 dark:text-red-300">High Risk</span>
							</div>
						</div>
						<div class="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
							<div class="flex justify-between items-center">
								<span class="font-medium text-orange-900 dark:text-orange-200">T1566.001 - Spearphishing</span>
								<span class="text-sm text-orange-700 dark:text-orange-300">Medium Risk</span>
							</div>
						</div>
						<div class="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
							<div class="flex justify-between items-center">
								<span class="font-medium text-yellow-900 dark:text-yellow-200">T1078 - Valid Accounts</span>
								<span class="text-sm text-yellow-700 dark:text-yellow-300">Medium Risk</span>
							</div>
						</div>
					</div>
				</div>

				<div>
					<h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">🛡️ Recommended Mitigations</h4>
					<div class="space-y-2">
						<div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
							<span class="font-medium text-green-900 dark:text-green-200">Implement PowerShell execution policies</span>
						</div>
						<div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
							<span class="font-medium text-green-900 dark:text-green-200">Deploy email security filters</span>
						</div>
						<div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
							<span class="font-medium text-green-900 dark:text-green-200">Enable multi-factor authentication</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
