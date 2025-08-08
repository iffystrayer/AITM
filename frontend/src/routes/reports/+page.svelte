<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	onMount(() => {
		currentPage.set('reports');
	});
</script>

<svelte:head>
	<title>Reports - AITM</title>
</svelte:head>

<div class="space-y-6">
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Reports</h2>
		<p class="text-gray-600 dark:text-gray-300">
			Generate comprehensive threat modeling reports with executive summaries and technical details.
		</p>
		
		<div class="mt-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
			<h3 class="text-lg font-semibold text-purple-900 dark:text-purple-100 mb-2">📊 Report Features</h3>
			<p class="text-purple-800 dark:text-purple-200">
				Comprehensive reporting includes:
			</p>
			<ul class="list-disc list-inside mt-2 text-purple-800 dark:text-purple-200 space-y-1">
				<li>Executive summaries</li>
				<li>Technical analysis reports</li>
				<li>Risk assessment matrices</li>
				<li>Mitigation recommendations</li>
				<li>MITRE ATT&CK mapping</li>
				<li>Export to PDF/JSON formats</li>
			</ul>
		</div>
	</div>
</div>
