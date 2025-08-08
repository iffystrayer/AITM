<script>
	import { createEventDispatcher } from 'svelte';

	export let projectId;
	export let show = false;
	export let systemInputs = [];

	const dispatch = createEventDispatcher();

	let selectedInputs = [];
	let analysisConfig = {
		depth: 'standard', // basic, standard, comprehensive
		includeModeling: true,
		includeMitigations: true,
		includeCompliance: false,
		priorityLevel: 'high' // low, medium, high, critical
	};
	let starting = false;
	let error = null;

	// Select all inputs by default
	$: if (systemInputs.length > 0 && selectedInputs.length === 0) {
		selectedInputs = systemInputs.map(input => input.id);
	}

	async function handleStartAnalysis() {
		if (selectedInputs.length === 0) {
			error = 'Please select at least one system input for analysis';
			return;
		}

		try {
			starting = true;
			error = null;

			const analysisData = {
				project_id: projectId,
				input_ids: selectedInputs,
				config: {
					analysis_depth: analysisConfig.depth,
					include_threat_modeling: analysisConfig.includeModeling,
					include_mitigations: analysisConfig.includeMitigations,
					include_compliance_check: analysisConfig.includeCompliance,
					priority_level: analysisConfig.priorityLevel
				}
			};

			const response = await fetch(`http://localhost:38527/api/v1/projects/${projectId}/analysis/start`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(analysisData)
			});

			if (response.ok) {
				const result = await response.json();
				dispatch('analysisStarted', result);
				show = false;
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Failed to start analysis';
			}
		} catch (err) {
			error = 'Connection error: ' + err.message;
		} finally {
			starting = false;
		}
	}

	function handleCancel() {
		error = null;
		show = false;
	}

	function toggleInputSelection(inputId) {
		if (selectedInputs.includes(inputId)) {
			selectedInputs = selectedInputs.filter(id => id !== inputId);
		} else {
			selectedInputs = [...selectedInputs, inputId];
		}
	}

	function selectAllInputs() {
		selectedInputs = systemInputs.map(input => input.id);
	}

	function clearAllInputs() {
		selectedInputs = [];
	}

	function getDepthDescription(depth) {
		switch (depth) {
			case 'basic':
				return 'Quick analysis focusing on major threats (5-10 min)';
			case 'standard':
				return 'Comprehensive analysis with MITRE ATT&CK mapping (15-30 min)';
			case 'comprehensive':
				return 'Deep analysis with detailed attack paths and mitigations (30-60 min)';
			default:
				return '';
		}
	}
</script>

{#if show}
	<!-- Modal Backdrop -->
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
			<div class="flex justify-between items-center mb-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Configure Threat Analysis</h3>
				<button
					on:click={handleCancel}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			{#if error}
				<div class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
					<p class="text-sm text-red-800 dark:text-red-200">{error}</p>
				</div>
			{/if}

			<form on:submit|preventDefault={handleStartAnalysis} class="space-y-6">
				<!-- Input Selection -->
				<div>
					<div class="flex justify-between items-center mb-3">
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
							System Inputs to Analyze ({selectedInputs.length} selected)
						</label>
						<div class="space-x-2">
							<button
								type="button"
								class="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
								on:click={selectAllInputs}
							>
								Select All
							</button>
							<button
								type="button"
								class="text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
								on:click={clearAllInputs}
							>
								Clear All
							</button>
						</div>
					</div>
					
					<div class="space-y-2 max-h-32 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded p-3">
						{#each systemInputs as input (input.id)}
							<label class="flex items-center space-x-3">
								<input
									type="checkbox"
									checked={selectedInputs.includes(input.id)}
									on:change={() => toggleInputSelection(input.id)}
									class="text-blue-600"
								>
								<div>
									<span class="text-sm font-medium text-gray-900 dark:text-white">{input.title}</span>
									{#if input.description}
										<p class="text-xs text-gray-500 dark:text-gray-400">{input.description}</p>
									{/if}
								</div>
							</label>
						{/each}
					</div>
				</div>

				<!-- Analysis Depth -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Analysis Depth</label>
					<div class="space-y-3">
						{#each [
							{ value: 'basic', label: 'Basic Analysis', color: 'green' },
							{ value: 'standard', label: 'Standard Analysis', color: 'blue' },
							{ value: 'comprehensive', label: 'Comprehensive Analysis', color: 'purple' }
						] as option}
							<label class="flex items-start space-x-3 p-3 border rounded-lg cursor-pointer {analysisConfig.depth === option.value ? 'border-' + option.color + '-500 bg-' + option.color + '-50 dark:bg-' + option.color + '-900/20' : 'border-gray-200 dark:border-gray-600'}">
								<input
									type="radio"
									bind:group={analysisConfig.depth}
									value={option.value}
									class="mt-1 text-{option.color}-600"
								>
								<div>
									<span class="text-sm font-medium text-gray-900 dark:text-white">{option.label}</span>
									<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
										{getDepthDescription(option.value)}
									</p>
								</div>
							</label>
						{/each}
					</div>
				</div>

				<!-- Analysis Options -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Analysis Options</label>
					<div class="space-y-3">
						<label class="flex items-center space-x-3">
							<input
								type="checkbox"
								bind:checked={analysisConfig.includeModeling}
								class="text-blue-600"
							>
							<div>
								<span class="text-sm text-gray-900 dark:text-white">Threat Modeling</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">Generate attack trees and threat scenarios</p>
							</div>
						</label>
						
						<label class="flex items-center space-x-3">
							<input
								type="checkbox"
								bind:checked={analysisConfig.includeMitigations}
								class="text-blue-600"
							>
							<div>
								<span class="text-sm text-gray-900 dark:text-white">Security Mitigations</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">Recommend security controls and mitigations</p>
							</div>
						</label>
						
						<label class="flex items-center space-x-3">
							<input
								type="checkbox"
								bind:checked={analysisConfig.includeCompliance}
								class="text-blue-600"
							>
							<div>
								<span class="text-sm text-gray-900 dark:text-white">Compliance Check</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">Check against common security frameworks</p>
							</div>
						</label>
					</div>
				</div>

				<!-- Priority Level -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Priority Level</label>
					<select
						bind:value={analysisConfig.priorityLevel}
						class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
					>
						<option value="low">Low - Focus on critical threats only</option>
						<option value="medium">Medium - Balanced analysis</option>
						<option value="high">High - Detailed threat coverage</option>
						<option value="critical">Critical - Maximum security focus</option>
					</select>
				</div>

				<!-- Form Actions -->
				<div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-600">
					<button
						type="button"
						on:click={handleCancel}
						class="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg"
						disabled={starting}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={starting || selectedInputs.length === 0}
					>
						{#if starting}
							<div class="flex items-center space-x-2">
								<div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
								<span>Starting Analysis...</span>
							</div>
						{:else}
							Start Threat Analysis
						{/if}
					</button>
				</div>
			</form>

			<!-- Estimated Time -->
			<div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
				<p class="text-sm text-blue-800 dark:text-blue-200">
					<strong>Estimated time:</strong> {getDepthDescription(analysisConfig.depth)}
				</p>
				<p class="text-xs text-blue-600 dark:text-blue-300 mt-1">
					You'll receive real-time updates as the AI agents analyze your system.
				</p>
			</div>
		</div>
	</div>
{/if}
