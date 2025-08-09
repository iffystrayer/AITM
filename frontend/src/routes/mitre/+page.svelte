<script>
	import { currentPage } from '$lib/stores';
	import { onMount } from 'svelte';

	// Sample MITRE ATT&CK data structure
	let selectedTactic = null;
	let searchTerm = '';
	let viewMode = 'matrix'; // 'matrix', 'techniques', 'details'
	let selectedTechnique = null;

	const tactics = [
		{ id: 'TA0001', name: 'Initial Access', description: 'Adversary is trying to get into your network', color: 'bg-red-500' },
		{ id: 'TA0002', name: 'Execution', description: 'Adversary is trying to run malicious code', color: 'bg-orange-500' },
		{ id: 'TA0003', name: 'Persistence', description: 'Adversary is trying to maintain their foothold', color: 'bg-yellow-500' },
		{ id: 'TA0004', name: 'Privilege Escalation', description: 'Adversary is trying to gain higher-level permissions', color: 'bg-green-500' },
		{ id: 'TA0005', name: 'Defense Evasion', description: 'Adversary is trying to avoid being detected', color: 'bg-blue-500' },
		{ id: 'TA0006', name: 'Credential Access', description: 'Adversary is trying to steal account names and passwords', color: 'bg-indigo-500' },
		{ id: 'TA0007', name: 'Discovery', description: 'Adversary is trying to figure out your environment', color: 'bg-purple-500' },
		{ id: 'TA0008', name: 'Lateral Movement', description: 'Adversary is trying to move through your environment', color: 'bg-pink-500' },
		{ id: 'TA0009', name: 'Collection', description: 'Adversary is trying to gather data of interest', color: 'bg-gray-500' },
		{ id: 'TA0011', name: 'Command and Control', description: 'Adversary is trying to communicate with compromised systems', color: 'bg-red-600' },
		{ id: 'TA0010', name: 'Exfiltration', description: 'Adversary is trying to steal data', color: 'bg-orange-600' },
		{ id: 'TA0040', name: 'Impact', description: 'Adversary is trying to manipulate, interrupt, or destroy systems', color: 'bg-red-700' }
	];

	const techniques = [
		{ id: 'T1566', name: 'Phishing', tactic: 'TA0001', subtechniques: 3, mitigations: 5, detections: 8 },
		{ id: 'T1078', name: 'Valid Accounts', tactic: 'TA0001', subtechniques: 4, mitigations: 7, detections: 6 },
		{ id: 'T1190', name: 'Exploit Public-Facing Application', tactic: 'TA0001', subtechniques: 0, mitigations: 4, detections: 5 },
		{ id: 'T1059', name: 'Command and Scripting Interpreter', tactic: 'TA0002', subtechniques: 8, mitigations: 6, detections: 12 },
		{ id: 'T1053', name: 'Scheduled Task/Job', tactic: 'TA0003', subtechniques: 5, mitigations: 3, detections: 7 },
		{ id: 'T1055', name: 'Process Injection', tactic: 'TA0004', subtechniques: 12, mitigations: 4, detections: 9 },
		{ id: 'T1027', name: 'Obfuscated Files or Information', tactic: 'TA0005', subtechniques: 9, mitigations: 2, detections: 6 },
		{ id: 'T1003', name: 'OS Credential Dumping', tactic: 'TA0006', subtechniques: 8, mitigations: 8, detections: 11 }
	];

	onMount(() => {
		currentPage.set('mitre');
	});

	function selectTactic(tactic) {
		selectedTactic = tactic;
		viewMode = 'techniques';
	}

	function selectTechnique(technique) {
		selectedTechnique = technique;
		viewMode = 'details';
	}

	function getTacticName(tacticId) {
		return tactics.find(t => t.id === tacticId)?.name || 'Unknown';
	}

	function getFilteredTechniques() {
		let filtered = techniques;
		if (selectedTactic) {
			filtered = filtered.filter(t => t.tactic === selectedTactic.id);
		}
		if (searchTerm) {
			filtered = filtered.filter(t => 
				t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
				t.id.toLowerCase().includes(searchTerm.toLowerCase())
			);
		}
		return filtered;
	}

	function getSeverityColor(detections) {
		if (detections >= 10) return 'bg-red-100 text-red-800';
		if (detections >= 6) return 'bg-orange-100 text-orange-800';
		return 'bg-green-100 text-green-800';
	}
</script>

<svelte:head>
	<title>MITRE ATT&CK - AITM</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
		<div class="flex justify-between items-start mb-4">
			<div>
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white">MITRE ATT&CK Framework</h2>
				<p class="text-gray-600 dark:text-gray-300 mt-1">
					Analyze adversary tactics and techniques based on real-world observations
				</p>
			</div>
			<div class="flex space-x-2">
				<button 
					class="px-3 py-1 text-sm rounded {viewMode === 'matrix' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}"
					on:click={() => { viewMode = 'matrix'; selectedTactic = null; selectedTechnique = null; }}
				>
					🎯 Matrix
				</button>
				<button 
					class="px-3 py-1 text-sm rounded {viewMode === 'techniques' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}"
					on:click={() => { viewMode = 'techniques'; selectedTechnique = null; }}
				>
					📋 Techniques
				</button>
			</div>
		</div>

		<!-- Search -->
		<div class="mb-4">
			<input 
				bind:value={searchTerm}
				placeholder="Search techniques (e.g., T1566, Phishing)..."
				class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
			/>
		</div>
	</div>

	<!-- Tactics Matrix View -->
	{#if viewMode === 'matrix'}
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Tactics Overview</h3>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
				{#each tactics as tactic}
					<div 
						class="p-4 rounded-lg border-2 border-gray-200 dark:border-gray-600 hover:border-blue-500 cursor-pointer transition-all"
						on:click={() => selectTactic(tactic)}
					>
						<div class="flex items-center mb-2">
							<div class="w-3 h-3 rounded-full {tactic.color} mr-2"></div>
							<h4 class="font-semibold text-gray-900 dark:text-white text-sm">{tactic.name}</h4>
						</div>
						<p class="text-xs text-gray-600 dark:text-gray-300 mb-2">{tactic.id}</p>
						<p class="text-sm text-gray-700 dark:text-gray-400">{tactic.description}</p>
						<div class="mt-3 text-xs text-blue-600 dark:text-blue-400">
							{techniques.filter(t => t.tactic === tactic.id).length} techniques →
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Techniques List View -->
	{#if viewMode === 'techniques'}
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
			<div class="flex justify-between items-center mb-4">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
					{selectedTactic ? `${selectedTactic.name} Techniques` : 'All Techniques'}
				</h3>
				{#if selectedTactic}
					<button 
						class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
						on:click={() => { selectedTactic = null; viewMode = 'matrix'; }}
					>
						← Back to Matrix
					</button>
				{/if}
			</div>

			<div class="overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
					<thead class="bg-gray-50 dark:bg-gray-700">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Technique</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Tactic</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Sub-techniques</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Mitigations</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Detections</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Risk</th>
						</tr>
					</thead>
					<tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
						{#each getFilteredTechniques() as technique}
						<tr class="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer" on:click={() => selectTechnique(technique)}>
							<td class="px-6 py-4 whitespace-nowrap">
								<div class="text-sm font-medium text-gray-900 dark:text-white">{technique.name}</div>
								<div class="text-sm text-gray-500 dark:text-gray-400">{technique.id}</div>
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
								{getTacticName(technique.tactic)}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
								{technique.subtechniques}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
								{technique.mitigations}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
								{technique.detections}
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<span class="px-2 py-1 text-xs font-semibold rounded-full {getSeverityColor(technique.detections)}">
									{technique.detections >= 10 ? 'High' : technique.detections >= 6 ? 'Medium' : 'Low'}
								</span>
							</td>
						</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}

	<!-- Technique Details View -->
	{#if viewMode === 'details' && selectedTechnique}
		<div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
			<div class="flex justify-between items-start mb-6">
				<div>
					<h3 class="text-2xl font-bold text-gray-900 dark:text-white">{selectedTechnique.name}</h3>
					<p class="text-gray-600 dark:text-gray-300">{selectedTechnique.id} • {getTacticName(selectedTechnique.tactic)}</p>
				</div>
				<button 
					class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
					on:click={() => viewMode = 'techniques'}
				>
					← Back to Techniques
				</button>
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- Overview -->
				<div class="lg:col-span-2 space-y-6">
					<div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
						<h4 class="font-semibold text-blue-900 dark:text-blue-100 mb-2">Description</h4>
						<p class="text-blue-800 dark:text-blue-200 text-sm">
							Adversaries may send {selectedTechnique.name.toLowerCase()} messages to obtain access to victim systems. 
							This technique is commonly used as part of initial access campaigns and can be highly effective 
							when combined with social engineering tactics.
						</p>
					</div>

					<div class="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
						<h4 class="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">Detection Methods</h4>
						<ul class="text-yellow-800 dark:text-yellow-200 text-sm space-y-1">
							<li>• Monitor for suspicious email patterns and attachments</li>
							<li>• Analyze network traffic for malicious domains</li>
							<li>• Review authentication logs for unusual access patterns</li>
							<li>• Implement behavioral analysis for user activities</li>
						</ul>
					</div>

					<div class="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
						<h4 class="font-semibold text-green-900 dark:text-green-100 mb-2">Mitigation Strategies</h4>
						<ul class="text-green-800 dark:text-green-200 text-sm space-y-1">
							<li>• Implement email security gateways and filtering</li>
							<li>• Conduct regular security awareness training</li>
							<li>• Deploy multi-factor authentication</li>
							<li>• Maintain updated endpoint protection</li>
							<li>• Implement application sandboxing</li>
						</ul>
					</div>
				</div>

				<!-- Statistics -->
				<div class="space-y-4">
					<div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
						<h4 class="font-semibold text-gray-900 dark:text-white mb-3">Technique Statistics</h4>
						<div class="space-y-3">
							<div class="flex justify-between">
								<span class="text-sm text-gray-600 dark:text-gray-300">Sub-techniques</span>
								<span class="font-semibold text-gray-900 dark:text-white">{selectedTechnique.subtechniques}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-sm text-gray-600 dark:text-gray-300">Mitigations</span>
								<span class="font-semibold text-gray-900 dark:text-white">{selectedTechnique.mitigations}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-sm text-gray-600 dark:text-gray-300">Detections</span>
								<span class="font-semibold text-gray-900 dark:text-white">{selectedTechnique.detections}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-sm text-gray-600 dark:text-gray-300">Risk Level</span>
								<span class="px-2 py-1 text-xs font-semibold rounded-full {getSeverityColor(selectedTechnique.detections)}">
									{selectedTechnique.detections >= 10 ? 'High' : selectedTechnique.detections >= 6 ? 'Medium' : 'Low'}
								</span>
							</div>
						</div>
					</div>

					<div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
						<h4 class="font-semibold text-red-900 dark:text-red-100 mb-2">🚨 Threat Level</h4>
						<p class="text-red-800 dark:text-red-200 text-sm mb-2">Commonly used in APT campaigns</p>
						<div class="w-full bg-red-200 dark:bg-red-800 rounded-full h-2">
							<div class="bg-red-600 h-2 rounded-full" style="width: {Math.min((selectedTechnique.detections / 15) * 100, 100)}%"></div>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
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
