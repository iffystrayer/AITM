<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	let assets = [
		{ id: 1, name: 'Web Server', type: 'Server', criticality: 'High', technology: 'Nginx', status: 'Active' },
		{ id: 2, name: 'Database Server', type: 'Database', criticality: 'Critical', technology: 'PostgreSQL', status: 'Active' },
		{ id: 3, name: 'API Gateway', type: 'Service', criticality: 'High', technology: 'Kong', status: 'Active' },
		{ id: 4, name: 'Load Balancer', type: 'Infrastructure', criticality: 'Medium', technology: 'HAProxy', status: 'Active' },
		{ id: 5, name: 'Authentication Service', type: 'Service', criticality: 'Critical', technology: 'Auth0', status: 'Active' }
	];

	let showAddForm = false;
	let newAsset = { name: '', type: '', criticality: 'Medium', technology: '', status: 'Active' };

	onMount(() => {
		currentPage.set('assets');
	});

	function addAsset() {
		if (newAsset.name && newAsset.type && newAsset.technology) {
			assets = [...assets, { ...newAsset, id: Date.now() }];
			newAsset = { name: '', type: '', criticality: 'Medium', technology: '', status: 'Active' };
			showAddForm = false;
		}
	}

	function getCriticalityColor(criticality) {
		switch(criticality) {
			case 'Critical': return 'bg-red-100 text-red-800';
			case 'High': return 'bg-orange-100 text-orange-800';
			case 'Medium': return 'bg-yellow-100 text-yellow-800';
			case 'Low': return 'bg-green-100 text-green-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>Asset Management - AITM</title>
</svelte:head>

<div class="space-y-6">
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<div class="flex justify-between items-center mb-6">
			<div>
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white">Asset Management</h2>
				<p class="text-gray-600 dark:text-gray-300 mt-1">
					Manage and categorize your system assets for threat modeling
				</p>
			</div>
			<button 
				class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
				on:click={() => showAddForm = true}
			>
				💎 Add Asset
			</button>
		</div>

		<div class="overflow-x-auto">
			<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
				<thead class="bg-gray-50 dark:bg-gray-700">
					<tr>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Asset</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Criticality</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Technology</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
					</tr>
				</thead>
				<tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
					{#each assets as asset}
					<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
						<td class="px-6 py-4 whitespace-nowrap">
							<div class="text-sm font-medium text-gray-900 dark:text-white">{asset.name}</div>
						</td>
						<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{asset.type}</td>
						<td class="px-6 py-4 whitespace-nowrap">
							<span class="px-2 py-1 text-xs font-semibold rounded-full {getCriticalityColor(asset.criticality)}">
								{asset.criticality}
							</span>
						</td>
						<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{asset.technology}</td>
						<td class="px-6 py-4 whitespace-nowrap">
							<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">{asset.status}</span>
						</td>
					</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>

	<!-- Add Asset Modal -->
	{#if showAddForm}
		<div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Add New Asset</h3>
				<div class="space-y-4">
					<input bind:value={newAsset.name} placeholder="Asset Name" class="w-full border rounded-lg px-3 py-2" />
					<select bind:value={newAsset.type} class="w-full border rounded-lg px-3 py-2">
						<option value="">Select Type...</option>
						<option value="Server">Server</option>
						<option value="Database">Database</option>
						<option value="Service">Service</option>
						<option value="Infrastructure">Infrastructure</option>
					</select>
					<select bind:value={newAsset.criticality} class="w-full border rounded-lg px-3 py-2">
						<option value="Critical">Critical</option>
						<option value="High">High</option>
						<option value="Medium">Medium</option>
						<option value="Low">Low</option>
					</select>
					<input bind:value={newAsset.technology} placeholder="Technology/Platform" class="w-full border rounded-lg px-3 py-2" />
				</div>
				<div class="flex justify-end space-x-3 mt-6">
					<button class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg" on:click={() => showAddForm = false}>Cancel</button>
					<button class="px-4 py-2 bg-blue-600 text-white rounded-lg" on:click={addAsset}>Add Asset</button>
				</div>
			</div>
		</div>
	{/if}
</div>
