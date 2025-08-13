<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';
	import { apiService } from '$lib/api';

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
			const response = await apiService.getProjects();
			projects = response.data || response;
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
		<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
			<div class="flex justify-between items-center">
				<div>
					<h2 class="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-3">
						Threat Analysis
					</h2>
					<p class="text-gray-300 text-lg">
						AI-powered threat analysis workspace with multi-agent system
					</p>
				</div>
				<div class="flex space-x-4">
					<button 
						class="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl font-semibold transform transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
						on:click={() => showConfig = true}
						disabled={loading}
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
						</svg>
						<span>New Analysis</span>
					</button>
					{#if analysisResults}
						<button 
							class="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-semibold transition-all duration-200 flex items-center space-x-2"
							on:click={resetAnalysis}
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
							</svg>
							<span>Reset</span>
						</button>
					{/if}
				</div>
			</div>
		</div>

		<!-- Analysis Configuration Modal -->
		{#if showConfig}
			<div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
				<div class="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
					<h3 class="text-2xl font-bold text-white mb-6">Configure Analysis</h3>
					
					<div class="space-y-6">
						<div>
							<label class="block text-sm font-medium text-gray-200 mb-2">Select Project</label>
							<select 
								bind:value={selectedProject}
								class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
							>
								<option value={null} class="bg-gray-800 text-white">Choose a project...</option>
								{#each projects as project}
									<option value={project} class="bg-gray-800 text-white">{project.name}</option>
								{/each}
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-200 mb-2">Analysis Depth</label>
							<select class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200">
								<option value="basic" class="bg-gray-800 text-white">Basic Analysis</option>
								<option value="standard" selected class="bg-gray-800 text-white">Standard Analysis</option>
								<option value="comprehensive" class="bg-gray-800 text-white">Comprehensive Analysis</option>
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-200 mb-2">LLM Provider</label>
							<select class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent backdrop-blur-sm transition-all duration-200">
								<option value="gemini" selected class="bg-gray-800 text-white">Google Gemini</option>
								<option value="openai" class="bg-gray-800 text-white">OpenAI GPT</option>
								<option value="ollama" class="bg-gray-800 text-white">Ollama (Local)</option>
							</select>
						</div>
					</div>

					<div class="flex justify-end space-x-4 mt-8">
						<button
							type="button"
							class="px-6 py-3 text-gray-300 bg-white/10 hover:bg-white/20 rounded-xl transition-colors duration-200"
							on:click={() => showConfig = false}
						>
							Cancel
						</button>
						<button
							type="button"
							class="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-xl font-semibold transform transition-all duration-200 hover:scale-105 shadow-lg disabled:opacity-50"
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
			<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
				<h3 class="text-xl font-bold text-white mb-6">Analysis Status</h3>
				
				{#if analysisStatus === 'running'}
					<div class="space-y-6">
						<div class="flex items-center space-x-4">
							<div class="w-8 h-8 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
							<span class="text-cyan-400 font-semibold text-lg">Analyzing: {selectedProject.name}</span>
						</div>
						<div class="bg-cyan-500/10 backdrop-blur-sm border border-cyan-400/30 p-6 rounded-xl">
							<h4 class="font-semibold text-cyan-200 mb-4 flex items-center">
								<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
								</svg>
								Multi-Agent Analysis in Progress
							</h4>
							<ul class="text-cyan-300 space-y-2">
								<li class="flex items-center space-x-2">
									<div class="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
									<span>System Analyst Agent: Parsing system architecture...</span>
								</li>
								<li class="flex items-center space-x-2">
									<div class="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
									<span>ATT&CK Mapper Agent: Identifying threat techniques...</span>
								</li>
								<li class="flex items-center space-x-2">
									<div class="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></div>
									<span>Control Evaluation Agent: Assessing security controls...</span>
								</li>
							</ul>
						</div>
					</div>
				{:else if analysisStatus === 'completed'}
					<div class="space-y-4">
						<div class="flex items-center space-x-4">
							<div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
								<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
								</svg>
							</div>
							<span class="text-green-400 font-semibold text-lg">Analysis Complete: {selectedProject.name}</span>
						</div>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Analysis Results -->
		{#if analysisResults}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				<div class="bg-gradient-to-br from-red-500/20 to-orange-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Threats Identified</p>
							<p class="text-3xl font-bold text-white mt-2">{analysisResults.threatCount}</p>
						</div>
						<div class="w-12 h-12 bg-red-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-red-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
							</svg>
						</div>
					</div>
				</div>

				<div class="bg-gradient-to-br from-orange-500/20 to-yellow-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Risk Score</p>
							<p class="text-3xl font-bold text-white mt-2">{analysisResults.riskScore}/100</p>
						</div>
						<div class="w-12 h-12 bg-orange-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-orange-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
							</svg>
						</div>
					</div>
				</div>

				<div class="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Mitigations</p>
							<p class="text-3xl font-bold text-white mt-2">{analysisResults.mitigations}</p>
						</div>
						<div class="w-12 h-12 bg-blue-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
							</svg>
						</div>
					</div>
				</div>

				<div class="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-300">Attack Paths</p>
							<p class="text-3xl font-bold text-white mt-2">{analysisResults.attackPaths}</p>
						</div>
						<div class="w-12 h-12 bg-purple-500/30 rounded-xl flex items-center justify-center">
							<svg class="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			<!-- Detailed Results -->
			<div class="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl shadow-2xl p-8">
				<h3 class="text-xl font-bold text-white mb-6">Analysis Details</h3>
				
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
					<div>
						<h4 class="text-lg font-semibold text-white mb-4 flex items-center">
							<svg class="w-5 h-5 mr-2 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
							</svg>
							Top Attack Techniques
						</h4>
						<div class="space-y-3">
							<div class="p-4 bg-red-500/10 backdrop-blur-sm border border-red-400/30 rounded-xl">
								<div class="flex justify-between items-center">
									<span class="font-semibold text-red-200">T1059.001 - PowerShell</span>
									<span class="text-sm px-2 py-1 bg-red-500/20 text-red-300 rounded-lg">High Risk</span>
								</div>
							</div>
							<div class="p-4 bg-orange-500/10 backdrop-blur-sm border border-orange-400/30 rounded-xl">
								<div class="flex justify-between items-center">
									<span class="font-semibold text-orange-200">T1566.001 - Spearphishing</span>
									<span class="text-sm px-2 py-1 bg-orange-500/20 text-orange-300 rounded-lg">Medium Risk</span>
								</div>
							</div>
							<div class="p-4 bg-yellow-500/10 backdrop-blur-sm border border-yellow-400/30 rounded-xl">
								<div class="flex justify-between items-center">
									<span class="font-semibold text-yellow-200">T1078 - Valid Accounts</span>
									<span class="text-sm px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded-lg">Medium Risk</span>
								</div>
							</div>
						</div>
					</div>

					<div>
						<h4 class="text-lg font-semibold text-white mb-4 flex items-center">
							<svg class="w-5 h-5 mr-2 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
							</svg>
							Recommended Mitigations
						</h4>
						<div class="space-y-3">
							<div class="p-4 bg-green-500/10 backdrop-blur-sm border border-green-400/30 rounded-xl">
								<span class="font-semibold text-green-200">Implement PowerShell execution policies</span>
							</div>
							<div class="p-4 bg-green-500/10 backdrop-blur-sm border border-green-400/30 rounded-xl">
								<span class="font-semibold text-green-200">Deploy email security filters</span>
							</div>
							<div class="p-4 bg-green-500/10 backdrop-blur-sm border border-green-400/30 rounded-xl">
								<span class="font-semibold text-green-200">Enable multi-factor authentication</span>
							</div>
						</div>
					</div>
				</div>
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
