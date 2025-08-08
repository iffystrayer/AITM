<script>
	import { onMount } from 'svelte';
	
	let backendStatus = 'checking...';
	let apiResponse = null;

	onMount(async () => {
		try {
			const response = await fetch('http://127.0.0.1:38527/health');
			if (response.ok) {
				apiResponse = await response.json();
				backendStatus = '✅ Connected';
			} else {
				backendStatus = '❌ Error';
			}
		} catch (error) {
			backendStatus = '❌ Not Connected';
			console.error('Backend connection error:', error);
		}
	});
</script>

<svelte:head>
	<title>AITM - AI-Powered Threat Modeler</title>
</svelte:head>

<div class="space-y-8">
	<!-- Hero Section -->
	<div class="text-center">
		<h1 class="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
			AITM
		</h1>
		<p class="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
			AI-Powered Threat Modeler using multi-agent systems and MITRE ATT&CK framework
		</p>
	</div>

	<!-- Status Cards -->
	<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
		<!-- Backend Status -->
		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-bold">API</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">
								Backend Status
							</dt>
							<dd class="text-lg font-medium text-gray-900">
								{backendStatus}
							</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>

		<!-- Frontend Status -->
		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-bold">UI</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">
								Frontend Status
							</dt>
							<dd class="text-lg font-medium text-gray-900">
								✅ Active
							</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>

		<!-- Environment -->
		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-bold">ENV</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">
								Environment
							</dt>
							<dd class="text-lg font-medium text-gray-900">
								Development
							</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Features -->
	<div class="bg-white shadow overflow-hidden sm:rounded-md">
		<div class="px-4 py-5 sm:p-6">
			<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
				MVP Features Ready
			</h3>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<div class="flex items-start">
					<div class="flex-shrink-0">
						<span class="text-green-500">✅</span>
					</div>
					<div class="ml-3">
						<h4 class="text-sm font-medium text-gray-900">Multi-Agent System</h4>
						<p class="text-sm text-gray-500">SAA, AMA, CEA agents with orchestrator</p>
					</div>
				</div>
				<div class="flex items-start">
					<div class="flex-shrink-0">
						<span class="text-green-500">✅</span>
					</div>
					<div class="ml-3">
						<h4 class="text-sm font-medium text-gray-900">LLM Integration</h4>
						<p class="text-sm text-gray-500">Gemini, OpenAI, Ollama, LiteLLM support</p>
					</div>
				</div>
				<div class="flex items-start">
					<div class="flex-shrink-0">
						<span class="text-green-500">✅</span>
					</div>
					<div class="ml-3">
						<h4 class="text-sm font-medium text-gray-900">MITRE ATT&CK</h4>
						<p class="text-sm text-gray-500">Knowledge base integration</p>
					</div>
				</div>
				<div class="flex items-start">
					<div class="flex-shrink-0">
						<span class="text-green-500">✅</span>
					</div>
					<div class="ml-3">
						<h4 class="text-sm font-medium text-gray-900">REST API</h4>
						<p class="text-sm text-gray-500">Complete threat modeling endpoints</p>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Quick Links -->
	<div class="bg-white shadow overflow-hidden sm:rounded-md">
		<div class="px-4 py-5 sm:p-6">
			<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
				Quick Access
			</h3>
			<div class="flex space-x-4">
				<a 
					href="http://127.0.0.1:38527/docs" 
					target="_blank"
					class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				>
					📚 API Documentation
				</a>
				<a 
					href="http://127.0.0.1:38527/health" 
					target="_blank"
					class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				>
					🔍 Health Check
				</a>
			</div>
		</div>
	</div>

	<!-- API Response Debug -->
	{#if apiResponse}
		<div class="bg-gray-100 overflow-hidden sm:rounded-md">
			<div class="px-4 py-5 sm:p-6">
				<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
					Backend Response
				</h3>
				<pre class="text-sm text-gray-600 whitespace-pre-wrap">{JSON.stringify(apiResponse, null, 2)}</pre>
			</div>
		</div>
	{/if}
</div>
