<script>
	import '../app.css';
</script>

<div class="min-h-screen bg-gray-50">
	<nav class="bg-white shadow-sm border-b">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between h-16">
				<div class="flex items-center">
					<h1 class="text-xl font-bold text-gray-900">
						AITM - AI-Powered Threat Modeler
					</h1>
				</div>
				<div class="flex items-center space-x-4">
					<span class="text-sm text-gray-500">MVP Version</span>
				</div>
			</div>
		</div>
	</nav>
	
	<main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
		<slot />
	</main>
</div>

<style>
	:global(html, body) {
		height: 100%;
		margin: 0;
		padding: 0;
	}
</style>
