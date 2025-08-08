<script>
	import { onMount } from 'svelte';

	let threats = [];
	let loading = true;

	onMount(() => {
		// Mock threat intelligence data
		threats = [
			{
				id: 1,
				title: 'CVE-2024-1234: Remote Code Execution in Web Frameworks',
				severity: 'critical',
				timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
				source: 'NIST NVD',
				description: 'New vulnerability affecting popular web application frameworks',
				techniques: ['T1190', 'T1059.007'],
				affected_systems: ['Web Applications', 'API Services']
			},
			{
				id: 2,
				title: 'APT Group Observed Using New Lateral Movement Technique',
				severity: 'high',
				timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
				source: 'Threat Research',
				description: 'Advanced persistent threat group leveraging Windows services for lateral movement',
				techniques: ['T1021.001', 'T1543.003'],
				affected_systems: ['Windows Networks']
			},
			{
				id: 3,
				title: 'Increased Phishing Activity Targeting Finance Sector',
				severity: 'medium',
				timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4 hours ago
				source: 'Industry Alert',
				description: 'Coordinated phishing campaign using banking-themed lures',
				techniques: ['T1566.002', 'T1056.001'],
				affected_systems: ['Email Systems', 'User Workstations']
			},
			{
				id: 4,
				title: 'Supply Chain Attack Affecting Multiple Vendors',
				severity: 'high',
				timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
				source: 'Security Advisory',
				description: 'Compromised software update mechanism spreading malware',
				techniques: ['T1195.002', 'T1553.002'],
				affected_systems: ['Third-party Software']
			},
			{
				id: 5,
				title: 'Cloud Misconfiguration Leading to Data Exposure',
				severity: 'medium',
				timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8), // 8 hours ago
				source: 'Cloud Security',
				description: 'Common cloud storage misconfiguration patterns identified',
				techniques: ['T1530', 'T1078.004'],
				affected_systems: ['Cloud Storage', 'Cloud Services']
			}
		];
		loading = false;
	});

	function formatTimestamp(date) {
		const now = new Date();
		const diff = now - date;
		const minutes = Math.floor(diff / (1000 * 60));
		const hours = Math.floor(diff / (1000 * 60 * 60));
		
		if (hours > 0) {
			return `${hours}h ago`;
		} else {
			return `${minutes}m ago`;
		}
	}

	function getSeverityColor(severity) {
		switch (severity) {
			case 'critical':
				return 'bg-red-500 text-white';
			case 'high':
				return 'bg-orange-500 text-white';
			case 'medium':
				return 'bg-yellow-500 text-white';
			case 'low':
				return 'bg-green-500 text-white';
			default:
				return 'bg-gray-500 text-white';
		}
	}

	function getSeverityIcon(severity) {
		switch (severity) {
			case 'critical':
				return '🚨';
			case 'high':
				return '⚠️';
			case 'medium':
				return '⚡';
			case 'low':
				return 'ℹ️';
			default:
				return '📢';
		}
	}
</script>

<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
			🔍 Threat Intelligence Feed
		</h3>
		<div class="flex items-center space-x-2">
			<div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
			<span class="text-xs text-gray-500 dark:text-gray-400">Live</span>
		</div>
	</div>

	{#if loading}
		<div class="space-y-3">
			{#each Array(3) as _}
				<div class="animate-pulse">
					<div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
					<div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="space-y-4 max-h-96 overflow-y-auto">
			{#each threats as threat}
				<div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<div class="flex items-center space-x-2 mb-2">
								<span class="text-lg">{getSeverityIcon(threat.severity)}</span>
								<span class="px-2 py-1 text-xs font-semibold rounded-full {getSeverityColor(threat.severity)}">
									{threat.severity.toUpperCase()}
								</span>
								<span class="text-xs text-gray-500 dark:text-gray-400">
									{threat.source}
								</span>
							</div>
							
							<h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
								{threat.title}
							</h4>
							
							<p class="text-xs text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
								{threat.description}
							</p>
							
							<div class="flex flex-wrap gap-2 mb-3">
								{#each threat.techniques as technique}
									<span class="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
										{technique}
									</span>
								{/each}
							</div>
							
							<div class="flex items-center justify-between text-xs">
								<div class="flex flex-wrap gap-1">
									{#each threat.affected_systems as system}
										<span class="text-gray-500 dark:text-gray-400">
											{system}{threat.affected_systems.indexOf(system) < threat.affected_systems.length - 1 ? ',' : ''}
										</span>
									{/each}
								</div>
								<span class="text-gray-500 dark:text-gray-400">
									{formatTimestamp(threat.timestamp)}
								</span>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Footer Actions -->
		<div class="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
			<div class="flex items-center justify-between">
				<div class="text-xs text-gray-500 dark:text-gray-400">
					Last updated: {formatTimestamp(new Date(Date.now() - 1000 * 60 * 5))}
				</div>
				<button class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
					View All Threats →
				</button>
			</div>
		</div>
	{/if}
</div>
