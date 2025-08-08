<script>
	export let title;
	export let value;
	export let subtitle = '';
	export let icon = '📊';
	export let color = 'default';
	export let size = 'normal'; // normal, compact
	export let trend = null; // { value: number, direction: 'up' | 'down' }

	function getColorClasses(color) {
		switch (color) {
			case 'red':
				return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
			case 'green':
				return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
			case 'blue':
				return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
			case 'orange':
				return 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800';
			case 'purple':
				return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
			default:
				return 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700';
		}
	}

	function getTrendColor(direction) {
		return direction === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
	}

	$: cardClasses = `${getColorClasses(color)} border rounded-lg shadow-sm ${size === 'compact' ? 'p-4' : 'p-6'} transition-all duration-200 hover:shadow-md`;
</script>

<div class={cardClasses}>
	<div class="flex items-center justify-between">
		<div class="flex-1">
			<div class="flex items-center space-x-2">
				<span class="text-2xl">{icon}</span>
				<h3 class="text-sm font-medium text-gray-600 dark:text-gray-300 truncate">
					{title}
				</h3>
			</div>
			
			<div class="mt-2">
				<div class="flex items-baseline space-x-2">
					<p class="text-2xl font-semibold text-gray-900 dark:text-white">
						{value}
					</p>
					{#if trend}
						<div class="flex items-center space-x-1">
							<svg 
								class="w-4 h-4 {getTrendColor(trend.direction)}" 
								fill="none" 
								stroke="currentColor" 
								viewBox="0 0 24 24"
							>
								{#if trend.direction === 'up'}
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
								{:else}
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"/>
								{/if}
							</svg>
							<span class="text-sm font-medium {getTrendColor(trend.direction)}">
								{typeof trend.value === 'number' && trend.value < 1 
									? `${(trend.value * 100).toFixed(1)}%` 
									: trend.value}
							</span>
						</div>
					{/if}
				</div>
				
				{#if subtitle}
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
						{subtitle}
					</p>
				{/if}
			</div>
		</div>
	</div>
</div>
