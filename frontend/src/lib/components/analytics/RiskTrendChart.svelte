<script>
	export let data;

	function formatDate(date) {
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function getRiskColor(risk) {
		if (risk <= 0.3) return 'text-green-600';
		if (risk <= 0.6) return 'text-yellow-600';
		return 'text-red-600';
	}

	$: maxRisk = Math.max(...data.map(d => d.riskScore));
	$: avgRisk = data.reduce((sum, d) => sum + d.riskScore, 0) / data.length;
</script>

<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
	<div class="flex items-center justify-between mb-6">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Risk Trends</h3>
		<div class="text-sm text-gray-500 dark:text-gray-400">
			Last 30 days
		</div>
	</div>

	<!-- Chart Area (Simplified visualization) -->
	<div class="space-y-4">
		<!-- Mini Chart -->
		<div class="h-32 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 relative">
			<div class="absolute inset-4">
				<div class="flex items-end justify-between h-full">
					{#each data.slice(-14) as point, i}
						<div class="flex flex-col items-center space-y-1">
							<div 
								class="w-2 bg-blue-500 rounded-t" 
								style="height: {(point.riskScore / maxRisk) * 100}%"
								title="{formatDate(point.date)}: {(point.riskScore * 100).toFixed(1)}%"
							></div>
							{#if i % 3 === 0}
								<span class="text-xs text-gray-500 dark:text-gray-400 transform -rotate-45">
									{formatDate(point.date)}
								</span>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- Summary Stats -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
			<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
				<div class="text-lg font-bold {getRiskColor(avgRisk)}">
					{(avgRisk * 100).toFixed(1)}%
				</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">Average Risk</div>
			</div>
			<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
				<div class="text-lg font-bold {getRiskColor(maxRisk)}">
					{(maxRisk * 100).toFixed(1)}%
				</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">Peak Risk</div>
			</div>
			<div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
				<div class="text-lg font-bold text-blue-600 dark:text-blue-400">
					{data[data.length - 1]?.threats || 0}
				</div>
				<div class="text-xs text-gray-500 dark:text-gray-400">Active Threats</div>
			</div>
		</div>

		<!-- Recent Data Points -->
		<div class="border-t border-gray-200 dark:border-gray-700 pt-4">
			<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
				Recent Activity
			</h4>
			<div class="space-y-2">
				{#each data.slice(-5).reverse() as point}
					<div class="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded">
						<div class="flex items-center space-x-3">
							<div class="w-2 h-2 rounded-full bg-blue-500"></div>
							<span class="text-sm text-gray-600 dark:text-gray-300">
								{formatDate(point.date)}
							</span>
						</div>
						<div class="flex items-center space-x-4 text-sm">
							<span class="text-gray-500 dark:text-gray-400">
								{point.threats} threats
							</span>
							<span class="{getRiskColor(point.riskScore)} font-medium">
								{(point.riskScore * 100).toFixed(1)}%
							</span>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>
