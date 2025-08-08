<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	onMount(() => {
		currentPage.set('mitre');
	});
</script>

<svelte:head>
	<title>MITRE ATT&CK - AITM</title>
</svelte:head>

<div class="space-y-6">
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">MITRE ATT&CK Framework</h2>
		<p class="text-gray-600 dark:text-gray-300">
			Explore and map threats using the comprehensive MITRE ATT&CK knowledge base of adversary tactics and techniques.
		</p>
		
		<div class="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
			<h3 class="text-lg font-semibold text-yellow-900 dark:text-yellow-100 mb-2">🛡️ MITRE Integration</h3>
			<p class="text-yellow-800 dark:text-yellow-200">
				MITRE ATT&CK integration provides:
			</p>
			<ul class="list-disc list-inside mt-2 text-yellow-800 dark:text-yellow-200 space-y-1">
				<li>Complete technique and tactic database</li>
				<li>Advanced search and filtering</li>
				<li>Threat mapping and visualization</li>
				<li>Mitigation recommendations</li>
				<li>Detection strategies</li>
				<li>Coverage gap analysis</li>
			</ul>
		</div>
		
		<div class="mt-6">
			<a 
				href="https://attack.mitre.org/" 
				target="_blank" 
				rel="noopener noreferrer"
				class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
			>
				<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
				</svg>
				Visit MITRE ATT&CK Website
			</a>
		</div>
	</div>
</div>
