<script>
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { currentPage } from '$lib/stores';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import SystemInputForm from '$lib/components/project/SystemInputForm.svelte';
	import AnalysisConfig from '$lib/components/project/AnalysisConfig.svelte';
	import AnalysisResults from '$lib/components/project/AnalysisResults.svelte';

	export let data;

	let project = null;
	let loading = true;
	let error = null;
	let activeTab = 'overview';
	let systemInputs = [];
	let analysisResults = null;
	let analysisStatus = 'idle'; // idle, running, completed, failed
	let showInputForm = false;
	let showAnalysisConfig = false;
	let statusPollingInterval = null;
	let analysisProgress = { phase: null, percentage: 0, message: '' };

	$: projectId = $page.params.id;

	onMount(async () => {
		currentPage.set('projects');
		await loadProject();
		await loadSystemInputs();
		await checkAnalysisStatus();
		
		// Start polling if analysis is running
		if (analysisStatus === 'running') {
			startStatusPolling();
		}
		
		return () => {
			if (statusPollingInterval) {
				clearInterval(statusPollingInterval);
			}
		};
	});

	async function loadProject() {
		try {
			loading = true;
			const response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}`);
			if (response.ok) {
				project = await response.json();
				error = null;
			} else if (response.status === 404) {
				error = 'Project not found';
			} else {
				error = 'Failed to load project';
			}
		} catch (err) {
			error = 'Connection error: ' + err.message;
		} finally {
			loading = false;
		}
	}

	async function loadSystemInputs() {
		try {
			const response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}/inputs`);
			if (response.ok) {
				const data = await response.json();
				systemInputs = data.data || [];
			}
		} catch (err) {
			console.error('Failed to load system inputs:', err);
		}
	}

	async function checkAnalysisStatus() {
		try {
			const response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}/analysis/status`);
			if (response.ok) {
				const data = await response.json();
				analysisStatus = data.status || 'idle';
				
				// Update progress information if available
				if (data.progress) {
					analysisProgress = {
						phase: data.progress.current_phase || null,
						percentage: data.progress.percentage || 0,
						message: data.progress.message || ''
					};
				}
				
				// Handle status changes
				if (analysisStatus === 'completed') {
					stopStatusPolling();
					await loadAnalysisResults();
				} else if (analysisStatus === 'running') {
					startStatusPolling();
				} else if (analysisStatus === 'failed') {
					stopStatusPolling();
				}
			}
		} catch (err) {
			console.error('Failed to check analysis status:', err);
		}
	}
	
	function startStatusPolling() {
		if (statusPollingInterval) return; // Already polling
		
		statusPollingInterval = setInterval(async () => {
			await checkAnalysisStatus();
		}, 2000); // Poll every 2 seconds
	}
	
	function stopStatusPolling() {
		if (statusPollingInterval) {
			clearInterval(statusPollingInterval);
			statusPollingInterval = null;
		}
	}

	async function loadAnalysisResults() {
		try {
			const response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}/analysis/results`);
			if (response.ok) {
				analysisResults = await response.json();
			}
		} catch (err) {
			console.error('Failed to load analysis results:', err);
		}
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusColor(status) {
		switch (status) {
			case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200';
			case 'analyzing': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200';
			case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200';
			case 'running': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200';
			default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-200';
		}
	}
</script>

<svelte:head>
	<title>{project ? `${project.name} - AITM` : 'Project - AITM'}</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center min-h-96">
		<LoadingSpinner />
	</div>
{:else if error}
	<div class="max-w-4xl mx-auto p-6">
		<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
					</svg>
				</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error Loading Project</h3>
					<div class="mt-2 text-sm text-red-700 dark:text-red-300">
						<p>{error}</p>
					</div>
					<div class="mt-4">
						<a
							href="/projects"
							class="bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:hover:bg-red-700 text-red-800 dark:text-red-200 px-3 py-1 rounded text-sm"
						>
							← Back to Projects
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
{:else if project}
	<div class="max-w-6xl mx-auto space-y-6">
		<!-- Project Header -->
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
			<div class="flex items-center justify-between mb-4">
				<div class="flex items-center space-x-4">
					<a
						href="/projects"
						class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
						</svg>
					</a>
					<div>
						<h1 class="text-3xl font-bold text-gray-900 dark:text-white">{project.name}</h1>
						<p class="text-gray-600 dark:text-gray-300 mt-1">{project.description || 'No description provided'}</p>
					</div>
				</div>
				<div class="flex items-center space-x-3">
					<span class="px-3 py-1 text-sm font-semibold rounded-full {getStatusColor(project.status)}">
						{project.status}
					</span>
					<span class="text-sm text-gray-500 dark:text-gray-400">
						Created: {formatDate(project.created_at)}
					</span>
				</div>
			</div>
		</div>

		<!-- Navigation Tabs -->
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg">
			<div class="border-b border-gray-200 dark:border-gray-700">
				<nav class="px-6 flex space-x-8">
					<button
						class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'overview' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
						on:click={() => activeTab = 'overview'}
					>
						Overview
					</button>
					<button
						class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'inputs' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
						on:click={() => activeTab = 'inputs'}
					>
						System Inputs ({systemInputs.length})
					</button>
					<button
						class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'analysis' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
						on:click={() => activeTab = 'analysis'}
					>
						Analysis
						{#if analysisStatus === 'running'}
							<span class="ml-2 inline-flex items-center">
								<div class="animate-spin h-3 w-3 border border-blue-500 border-t-transparent rounded-full"></div>
							</span>
						{/if}
					</button>
					<button
						class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'results' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
						on:click={() => activeTab = 'results'}
					>
						Results
						{#if analysisResults}
							<span class="ml-1 inline-flex items-center justify-center w-4 h-4 text-xs bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200 rounded-full">
								✓
							</span>
						{/if}
					</button>
				</nav>
			</div>

			<!-- Tab Content -->
			<div class="p-6">
				{#if activeTab === 'overview'}
					<!-- Overview Tab -->
					<div class="space-y-6">
						<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
							<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
								<h3 class="text-lg font-semibold text-blue-900 dark:text-blue-100">System Inputs</h3>
								<p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">{systemInputs.length}</p>
								<p class="text-sm text-blue-700 dark:text-blue-300">System descriptions added</p>
							</div>
							<div class="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
								<h3 class="text-lg font-semibold text-purple-900 dark:text-purple-100">Analysis Status</h3>
								<p class="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-2 capitalize">{analysisStatus}</p>
								<p class="text-sm text-purple-700 dark:text-purple-300">Current analysis state</p>
							</div>
							<div class="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
								<h3 class="text-lg font-semibold text-green-900 dark:text-green-100">Threats Found</h3>
								<p class="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
									{analysisResults?.threats_found || 0}
								</p>
								<p class="text-sm text-green-700 dark:text-green-300">Identified attack paths</p>
							</div>
						</div>

						<div class="border-t border-gray-200 dark:border-gray-700 pt-6">
							<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Project Details</h3>
							<dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div>
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Project Name</dt>
									<dd class="text-sm text-gray-900 dark:text-white mt-1">{project.name}</dd>
								</div>
								<div>
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Status</dt>
									<dd class="mt-1">
										<span class="px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(project.status)}">
											{project.status}
										</span>
									</dd>
								</div>
								<div>
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</dt>
									<dd class="text-sm text-gray-900 dark:text-white mt-1">{formatDate(project.created_at)}</dd>
								</div>
								<div>
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</dt>
									<dd class="text-sm text-gray-900 dark:text-white mt-1">{formatDate(project.updated_at)}</dd>
								</div>
								{#if project.description}
									<div class="md:col-span-2">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</dt>
										<dd class="text-sm text-gray-900 dark:text-white mt-1">{project.description}</dd>
									</div>
								{/if}
							</dl>
						</div>
					</div>
				{:else if activeTab === 'inputs'}
					<div>
						<div class="flex justify-between items-center mb-4">
							<h3 class="text-xl font-semibold text-gray-900 dark:text-white">System Inputs</h3>
							<button
								class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
								on:click={() => showInputForm = true}
							>
								+ Add Input
							</button>
						</div>

						{#if systemInputs.length === 0}
							<div class="text-center py-12 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
								<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 dark:bg-gray-700">
									<svg class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
									</svg>
								</div>
								<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No system inputs added yet</h3>
								<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
									Add system descriptions and documentation for analysis.
								</p>
								<div class="mt-6">
									<button
										class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
										on:click={() => showInputForm = true}
									>
										Add First Input
									</button>
								</div>
							</div>
						{:else}
							<div class="space-y-4">
								{#each systemInputs as input (input.id)}
									<div class="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
										<div class="flex justify-between items-start">
											<div>
												<h4 class="font-semibold text-gray-900 dark:text-white">{input.title}</h4>
												<p class="text-sm text-gray-600 dark:text-gray-300">{input.description}</p>
											</div>
											<div class="text-sm text-gray-500 dark:text-gray-400">
												{formatDate(input.created_at)}
											</div>
										</div>
										<div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
											<p class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{input.content || 'File content not shown'}</p>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{:else if activeTab === 'analysis'}
					<!-- Analysis Tab -->
					<div class="text-center py-12">
						<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-purple-100 dark:bg-purple-900/20">
							<svg class="h-6 w-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
							</svg>
						</div>
						<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Threat Analysis</h3>
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
							Status: <span class="capitalize font-medium">{analysisStatus}</span>
						</p>
						<div class="mt-6">
							{#if analysisStatus === 'idle'}
								<button
									class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium"
									on:click={() => showAnalysisConfig = true}
									disabled={systemInputs.length === 0}
								>
									Start Threat Analysis
								</button>
								{#if systemInputs.length === 0}
									<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
										Add system inputs before starting analysis
									</p>
								{/if}
							{:else if analysisStatus === 'running'}
									<div class="space-y-4">
										<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
											<div class="bg-purple-600 h-2.5 rounded-full" style="width: {analysisProgress.percentage}%"></div>
										</div>
										<p class="text-sm text-gray-500 dark:text-gray-400">
											{analysisProgress.phase}: {analysisProgress.message} ({analysisProgress.percentage.toFixed(0)}%)
										</p>
									</div>
								{:else if analysisStatus === 'completed'}
								<button
									class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium"
									on:click={() => activeTab = 'results'}
								>
									View Results
								</button>
							{/if}
						</div>
					</div>
				{:else if activeTab === 'results'}
					<!-- Results Tab -->
					<AnalysisResults {analysisResults} />
				{/if}
			</div>
		</div>
	</div>
	
	<SystemInputForm 
		bind:show={showInputForm} 
		projectId={project.id} 
		on:inputAdded={loadSystemInputs}
	/>

	<AnalysisConfig 
		bind:show={showAnalysisConfig} 
		projectId={project.id} 
		systemInputs={systemInputs}
		on:analysisStarted={(e) => {
			analysisStatus = 'running';
			setTimeout(() => checkAnalysisStatus(), 1000);
		}}
	/>
{/if}
