<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	onMount(() => {
		currentPage.set('analysis');
	});
</script>

<svelte:head>
	<title>Threat Analysis - AITM</title>
</svelte:head>

<div class="space-y-6">
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Threat Analysis</h2>
		<p class="text-gray-600 dark:text-gray-300">
			AI-powered threat analysis workspace. Run comprehensive threat modeling analysis on your systems.
		</p>
		
		<div class="mt-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
			<h3 class="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">🎯 Analysis Features</h3>
			<p class="text-red-800 dark:text-red-200">
				The Analysis page will provide:
			</p>
			<ul class="list-disc list-inside mt-2 text-red-800 dark:text-red-200 space-y-1">
				<li>Multi-agent threat analysis</li>
				<li>Attack path identification</li>
				<li>Risk assessment and scoring</li>
				<li>Real-time analysis progress</li>
				<li>Interactive threat visualization</li>
			</ul>
		</div>
	</div>
</div>
