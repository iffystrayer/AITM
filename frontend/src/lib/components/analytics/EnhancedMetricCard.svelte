<script>
	import { onMount } from 'svelte';
	import { TrendingUp, TrendingDown, Minus, AlertTriangle, Shield, Activity, Users } from 'lucide-svelte';

	export let title;
	export let value;
	export let change = null;
	export let changeType = 'neutral';
	export let icon = 'activity';
	export let color = 'blue';
	export let loading = false;

	// Icon mapping
	const iconComponents = {
		'trending-up': TrendingUp,
		'trending-down': TrendingDown,
		'alert': AlertTriangle,
		'shield': Shield,
		'activity': Activity,
		'users': Users
	};

	$: iconComponent = iconComponents[icon] || Activity;

	$: colorClasses = {
		red: 'bg-red-50 text-red-600 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800',
		green: 'bg-green-50 text-green-600 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800',
		blue: 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800',
		yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400 dark:border-yellow-800',
		purple: 'bg-purple-50 text-purple-600 border-purple-200 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-800',
		gray: 'bg-gray-50 text-gray-600 border-gray-200 dark:bg-gray-900/20 dark:text-gray-400 dark:border-gray-800'
	}[color];

	$: changeColorClasses = changeType === 'increase' 
		? 'text-green-600 dark:text-green-400' 
		: changeType === 'decrease' 
		? 'text-red-600 dark:text-red-400' 
		: 'text-gray-600 dark:text-gray-400';

	$: changeIcon = changeType === 'increase' 
		? TrendingUp 
		: changeType === 'decrease' 
		? TrendingDown 
		: Minus;

	// Format large numbers
	function formatValue(val) {
		if (typeof val === 'string') return val;
		
		if (val >= 1000000) {
			return (val / 1000000).toFixed(1) + 'M';
		}
		if (val >= 1000) {
			return (val / 1000).toFixed(1) + 'K';
		}
		return val.toString();
	}

	// Animate number counting
	let displayValue = 0;
	let targetValue = typeof value === 'number' ? value : 0;

	onMount(() => {
		if (typeof value === 'number') {
			const duration = 1000; // 1 second
			const steps = 60;
			const stepValue = targetValue / steps;
			const stepDuration = duration / steps;

			let currentStep = 0;
			const interval = setInterval(() => {
				currentStep++;
				displayValue = Math.min(stepValue * currentStep, targetValue);
				
				if (currentStep >= steps) {
					clearInterval(interval);
					displayValue = targetValue;
				}
			}, stepDuration);

			return () => clearInterval(interval);
		}
	});

	$: animatedValue = typeof value === 'number' ? Math.round(displayValue) : value;
</script>

<div class="metric-card bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow duration-200">
	<!-- Header -->
	<div class="flex items-center justify-between mb-4">
		<div class="flex items-center space-x-3">
			<div class="p-2 rounded-lg {colorClasses}">
				<svelte:component this={iconComponent} class="w-5 h-5" />
			</div>
			<h3 class="text-sm font-medium text-gray-600 dark:text-gray-300">{title}</h3>
		</div>
		
		{#if change !== null}
			<div class="flex items-center space-x-1 {changeColorClasses}">
				<svelte:component this={changeIcon} class="w-4 h-4" />
				<span class="text-sm font-medium">
					{change > 0 ? '+' : ''}{change}%
				</span>
			</div>
		{/if}
	</div>

	<!-- Main Value -->
	<div class="mb-2">
		{#if loading}
			<div class="animate-pulse">
				<div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
			</div>
		{:else}
			<div class="text-3xl font-bold text-gray-900 dark:text-white">
				{formatValue(animatedValue)}
			</div>
		{/if}
	</div>

	<!-- Additional Info -->
	<div class="text-xs text-gray-500 dark:text-gray-400">
		{#if changeType === 'increase'}
			<span class="text-green-600 dark:text-green-400">↗</span> Trending up
		{:else if changeType === 'decrease'}
			<span class="text-red-600 dark:text-red-400">↘</span> Trending down
		{:else}
			<span>No significant change</span>
		{/if}
	</div>
</div>

<style>
	.metric-card {
		min-height: 150px;
	}
</style>
