<script>
	export let title = '';
	export let value = '';
	export let unit = '';
	export let trend = 'stable'; // 'improving', 'declining', 'stable'
	export let color = 'blue'; // 'blue', 'green', 'orange', 'red', 'purple'
	export let icon = 'chart';
	export let subtitle = '';
	export let onClick = null;

	const colorClasses = {
		blue: {
			bg: 'from-blue-500/20 to-cyan-500/20',
			icon: 'bg-blue-500/30 text-blue-300',
			trend: {
				improving: 'text-green-400',
				declining: 'text-red-400',
				stable: 'text-gray-400'
			}
		},
		green: {
			bg: 'from-green-500/20 to-emerald-500/20',
			icon: 'bg-green-500/30 text-green-300',
			trend: {
				improving: 'text-green-400',
				declining: 'text-red-400',
				stable: 'text-gray-400'
			}
		},
		orange: {
			bg: 'from-orange-500/20 to-red-500/20',
			icon: 'bg-orange-500/30 text-orange-300',
			trend: {
				improving: 'text-green-400',
				declining: 'text-red-400',
				stable: 'text-gray-400'
			}
		},
		red: {
			bg: 'from-red-500/20 to-pink-500/20',
			icon: 'bg-red-500/30 text-red-300',
			trend: {
				improving: 'text-green-400',
				declining: 'text-red-400',
				stable: 'text-gray-400'
			}
		},
		purple: {
			bg: 'from-purple-500/20 to-pink-500/20',
			icon: 'bg-purple-500/30 text-purple-300',
			trend: {
				improving: 'text-green-400',
				declining: 'text-red-400',
				stable: 'text-gray-400'
			}
		}
	};

	const icons = {
		chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
		star: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
		shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
		warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z',
		wrench: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
		trending: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6'
	};

	const trendIcons = {
		improving: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
		declining: 'M13 17h8m0 0V9m0 8l-8-8-4 4-6-6',
		stable: 'M5 12h14'
	};

	function handleClick() {
		if (onClick) {
			onClick();
		}
	}
</script>

<div 
	class="bg-gradient-to-br {colorClasses[color].bg} backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:scale-105 transition-all duration-300 shadow-xl {onClick ? 'cursor-pointer' : ''}"
	on:click={handleClick}
	role={onClick ? 'button' : 'presentation'}
	tabindex={onClick ? 0 : -1}
	on:keydown={(e) => e.key === 'Enter' && handleClick()}
>
	<div class="flex items-center justify-between">
		<div class="flex-1">
			<p class="text-sm font-medium text-gray-300">{title}</p>
			<div class="flex items-baseline mt-2">
				<p class="text-3xl font-bold text-white">{value}</p>
				{#if unit}
					<span class="ml-1 text-lg text-gray-400">{unit}</span>
				{/if}
			</div>
			{#if subtitle}
				<p class="text-xs text-gray-400 mt-1">{subtitle}</p>
			{/if}
			
			<!-- Trend Indicator -->
			<div class="flex items-center mt-3">
				<svg class="w-4 h-4 mr-1 {colorClasses[color].trend[trend]}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={trendIcons[trend]}/>
				</svg>
				<span class="text-xs {colorClasses[color].trend[trend]} capitalize">{trend}</span>
			</div>
		</div>
		
		<!-- Icon -->
		<div class="w-12 h-12 {colorClasses[color].icon} rounded-xl flex items-center justify-center ml-4">
			<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={icons[icon]}/>
			</svg>
		</div>
	</div>
	
	<!-- Progress Bar (optional) -->
	{#if value && typeof value === 'string' && value.includes('%')}
		<div class="mt-4">
			<div class="w-full bg-white/10 rounded-full h-2">
				<div 
					class="bg-gradient-to-r {colorClasses[color].bg.replace('/20', '/60')} h-2 rounded-full transition-all duration-500"
					style="width: {value}"
				></div>
			</div>
		</div>
	{/if}
</div>