<script>
	export let data;

	function getCoverageColor(coverage) {
		if (coverage >= 80) return 'bg-green-500 dark:bg-green-600';
		if (coverage >= 60) return 'bg-yellow-500 dark:bg-yellow-600';
		if (coverage >= 40) return 'bg-orange-500 dark:bg-orange-600';
		return 'bg-red-500 dark:bg-red-600';
	}

	function getCoverageTextColor(coverage) {
		if (coverage >= 80) return 'text-green-600 dark:text-green-400';
		if (coverage >= 60) return 'text-yellow-600 dark:text-yellow-400';
		if (coverage >= 40) return 'text-orange-600 dark:text-orange-400';
		return 'text-red-600 dark:text-red-400';
	}

	$: totalTechniques = data.reduce((sum, item) => sum + item.techniques, 0);
	$: totalCovered = data.reduce((sum, item) => sum + item.covered, 0);
	$: overallCoverage = (totalCovered / totalTechniques * 100).toFixed(1);
</script>

<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
	<div class="flex items-center justify-between mb-6">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white">MITRE ATT&CK Coverage</h3>
		<div class="text-sm text-gray-500 dark:text-gray-400">
			{overallCoverage}% overall coverage
		</div>
	</div>

	<!-- Coverage Overview -->
	<div class="space-y-4">
		{#each data as item}
			<div class="space-y-2">
				<div class="flex items-center justify-between">
					<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
						{item.tactic}
					</span>
					<div class="flex items-center space-x-2">
						<span class="text-sm text-gray-500 dark:text-gray-400">
							{item.covered}/{item.techniques}
						</span>
						<span class="text-sm font-semibold {getCoverageTextColor(item.coverage)}">
							{item.coverage}%
						</span>
					</div>
				</div>
				<div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
					<div 
						class="h-2 rounded-full {getCoverageColor(item.coverage)} transition-all duration-300"
						style="width: {item.coverage}%"
					></div>
				</div>
			</div>
		{/each}

		<!-- Summary Statistics -->
		<div class="border-t border-gray-200 dark:border-gray-700 pt-4 mt-6">
			<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
				<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
					<div class="text-lg font-bold text-gray-900 dark:text-white">
						{data.length}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Tactics Analyzed</div>
				</div>
				<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
					<div class="text-lg font-bold text-gray-900 dark:text-white">
						{totalTechniques}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Total Techniques</div>
				</div>
				<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
					<div class="text-lg font-bold text-gray-900 dark:text-white">
						{totalCovered}
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Covered Techniques</div>
				</div>
				<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
					<div class="text-lg font-bold {getCoverageTextColor(overallCoverage)}">
						{overallCoverage}%
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">Overall Coverage</div>
				</div>
			</div>
		</div>

		<!-- Top and Bottom Performers -->
		<div class="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				<div>
					<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
						🏆 Best Coverage
					</h4>
					{#each data.sort((a, b) => b.coverage - a.coverage).slice(0, 3) as item}
						<div class="flex items-center justify-between py-1">
							<span class="text-sm text-gray-600 dark:text-gray-300">{item.tactic}</span>
							<span class="text-sm font-semibold {getCoverageTextColor(item.coverage)}">
								{item.coverage}%
							</span>
						</div>
					{/each}
				</div>
				<div>
					<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
						⚠️ Needs Attention
					</h4>
					{#each data.sort((a, b) => a.coverage - b.coverage).slice(0, 3) as item}
						<div class="flex items-center justify-between py-1">
							<span class="text-sm text-gray-600 dark:text-gray-300">{item.tactic}</span>
							<span class="text-sm font-semibold {getCoverageTextColor(item.coverage)}">
								{item.coverage}%
							</span>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>
