<script>
	export let data;
	export let detailed = false;

	function getIntensityColor(count, max) {
		const intensity = count / max;
		if (intensity === 0) return 'bg-gray-100 dark:bg-gray-800';
		if (intensity <= 0.2) return 'bg-red-100 dark:bg-red-900/20';
		if (intensity <= 0.4) return 'bg-red-200 dark:bg-red-900/40';
		if (intensity <= 0.6) return 'bg-red-300 dark:bg-red-900/60';
		if (intensity <= 0.8) return 'bg-red-400 dark:bg-red-900/80';
		return 'bg-red-500 dark:bg-red-900';
	}

	function getTacticDisplayName(tactic) {
		return tactic.replace(/([A-Z])/g, ' $1').trim();
	}

	$: maxTacticCount = Math.max(...data.topTactics.map(([, count]) => count), 1);
	$: maxTechniqueCount = Math.max(...data.topTechniques.map(([, count]) => count), 1);
</script>

<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
			{detailed ? 'Detailed Threat Landscape' : 'Threat Landscape Overview'}
		</h3>
		<div class="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
			<span>Low</span>
			<div class="flex space-x-1">
				<div class="w-3 h-3 bg-gray-100 dark:bg-gray-700 rounded"></div>
				<div class="w-3 h-3 bg-red-200 dark:bg-red-900/40 rounded"></div>
				<div class="w-3 h-3 bg-red-400 dark:bg-red-900/80 rounded"></div>
				<div class="w-3 h-3 bg-red-500 dark:bg-red-900 rounded"></div>
			</div>
			<span>High</span>
		</div>
	</div>

	<!-- MITRE ATT&CK Tactics Heatmap -->
	<div class="space-y-4">
		<div>
			<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
				Top Attack Tactics
			</h4>
			<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
				{#each data.topTactics as [tactic, count]}
					<div 
						class="p-3 rounded-lg border {getIntensityColor(count, maxTacticCount)} transition-all hover:scale-105 cursor-pointer"
						title="{getTacticDisplayName(tactic)}: {count} occurrences"
					>
						<div class="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
							{getTacticDisplayName(tactic)}
						</div>
						<div class="text-lg font-bold text-gray-900 dark:text-white mt-1">
							{count}
						</div>
					</div>
				{/each}
			</div>
		</div>

		{#if detailed}
			<div>
				<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
					Most Common Techniques
				</h4>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each data.topTechniques as [techniqueId, count]}
						<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
							<div>
								<div class="text-sm font-medium text-gray-900 dark:text-white">
									{techniqueId}
								</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">
									Used in {count} project{count !== 1 ? 's' : ''}
								</div>
							</div>
							<div class="text-lg font-bold text-blue-600 dark:text-blue-400">
								{count}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Summary Statistics -->
		<div class="border-t border-gray-200 dark:border-gray-700 pt-4">
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
				<div>
					<div class="text-2xl font-bold text-gray-900 dark:text-white">
						{Object.keys(data.tacticCounts).length}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Tactics Covered</div>
				</div>
				<div>
					<div class="text-2xl font-bold text-gray-900 dark:text-white">
						{Object.keys(data.techniqueFrequency).length}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Techniques Identified</div>
				</div>
				<div>
					<div class="text-2xl font-bold text-gray-900 dark:text-white">
						{data.topTactics[0]?.[1] || 0}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Most Common Tactic</div>
				</div>
				<div>
					<div class="text-2xl font-bold text-gray-900 dark:text-white">
						{Math.round(Object.values(data.tacticCounts).reduce((a, b) => a + b, 0) / Object.keys(data.tacticCounts).length) || 0}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Avg per Tactic</div>
				</div>
			</div>
		</div>
	</div>
</div>
