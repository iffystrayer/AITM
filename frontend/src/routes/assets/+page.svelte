<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	onMount(() => {
		currentPage.set('assets');
	});
</script>

<svelte:head>
	<title>Asset Management - AITM</title>
</svelte:head>

<div class="space-y-6">
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Asset Management</h2>
		<p class="text-gray-600 dark:text-gray-300">
			Manage and categorize your system assets for comprehensive threat modeling coverage.
		</p>
		
		<div class="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
			<h3 class="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">💎 Asset Features</h3>
			<p class="text-green-800 dark:text-green-200">
				Asset management capabilities include:
			</p>
			<ul class="list-disc list-inside mt-2 text-green-800 dark:text-green-200 space-y-1">
				<li>Asset inventory and classification</li>
				<li>Criticality assessment</li>
				<li>Technology stack mapping</li>
				<li>Asset relationship modeling</li>
				<li>Vulnerability tracking</li>
			</ul>
		</div>
	</div>
</div>
