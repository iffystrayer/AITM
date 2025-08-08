<script>
	import { onMount } from 'svelte';
	
	let backendStatus = 'checking...';
	let apiResponse = null;

	onMount(async () => {
		try {
			const response = await fetch('http://127.0.0.1:38527/health');
			if (response.ok) {
				apiResponse = await response.json();
				backendStatus = `✅ Backend Online (${apiResponse.status})`;
			} else {
				backendStatus = '❌ Backend not responding';
			}
		} catch (error) {
			backendStatus = '❌ Backend connection failed';
		}
	});
</script>

<svelte:head>
	<title>Test Page - AITM</title>
</svelte:head>

<div class="p-8 max-w-4xl mx-auto">
	<h1 class="text-3xl font-bold text-gray-900 mb-6">AITM Test Page</h1>
	
	<div class="bg-white shadow rounded-lg p-6">
		<h2 class="text-xl font-semibold mb-4">Backend Connection Test</h2>
		<p class="text-lg">Status: {backendStatus}</p>
		
		{#if apiResponse}
			<div class="mt-4 p-4 bg-gray-100 rounded">
				<h3 class="font-semibold">Backend Response:</h3>
				<pre class="text-sm mt-2">{JSON.stringify(apiResponse, null, 2)}</pre>
			</div>
		{/if}
	</div>
	
	<div class="mt-6">
		<a href="/" class="text-blue-600 hover:underline">← Back to Dashboard</a>
	</div>
</div>
