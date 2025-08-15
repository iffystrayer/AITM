<script>
	import { onMount, afterUpdate } from 'svelte';
	
	export let data = {};
	export let width = 400;
	export let height = 300;

	let canvas;
	let ctx;
	let heatmapData = [];

	onMount(() => {
		generateHeatmapData();
		drawHeatmap();
	});

	afterUpdate(() => {
		generateHeatmapData();
		drawHeatmap();
	});

	function generateHeatmapData() {
		if (!data || !data.codeQuality) return;

		// Create a grid representing different quality aspects
		heatmapData = [
			{
				label: 'Maintainability',
				value: data.codeQuality.maintainabilityIndex || 0,
				category: 'Code Quality'
			},
			{
				label: 'Complexity',
				value: Math.max(0, 100 - (data.codeQuality.cyclomaticComplexity || 0) * 5),
				category: 'Code Quality'
			},
			{
				label: 'Coverage',
				value: data.testQuality?.testCoverage || 0,
				category: 'Testing'
			},
			{
				label: 'Test Quality',
				value: data.testQuality?.testQualityScore || 0,
				category: 'Testing'
			},
			{
				label: 'Security',
				value: data.security?.securityScore || 0,
				category: 'Security'
			},
			{
				label: 'Vulnerabilities',
				value: Math.max(0, 100 - (data.security?.vulnerabilities?.critical || 0) * 20 - (data.security?.vulnerabilities?.high || 0) * 10),
				category: 'Security'
			},
			{
				label: 'Performance',
				value: data.performance?.performanceScore || 0,
				category: 'Performance'
			},
			{
				label: 'Bottlenecks',
				value: Math.max(0, 100 - (data.performance?.bottlenecks || 0) * 15),
				category: 'Performance'
			}
		];
	}

	function drawHeatmap() {
		if (!canvas || !ctx || heatmapData.length === 0) return;

		canvas.width = width;
		canvas.height = height;

		// Clear canvas
		ctx.clearRect(0, 0, width, height);

		// Calculate grid dimensions
		const cols = 4;
		const rows = 2;
		const cellWidth = width / cols;
		const cellHeight = height / rows;
		const padding = 2;

		// Draw heatmap cells
		heatmapData.forEach((item, index) => {
			const col = index % cols;
			const row = Math.floor(index / cols);
			
			const x = col * cellWidth + padding;
			const y = row * cellHeight + padding;
			const w = cellWidth - padding * 2;
			const h = cellHeight - padding * 2;

			// Calculate color based on value
			const color = getHeatmapColor(item.value);
			
			// Draw cell background
			ctx.fillStyle = color;
			ctx.fillRect(x, y, w, h);

			// Draw cell border
			ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
			ctx.lineWidth = 1;
			ctx.strokeRect(x, y, w, h);

			// Draw label
			ctx.fillStyle = item.value > 50 ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)';
			ctx.font = '12px Inter, sans-serif';
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			
			// Label
			ctx.fillText(item.label, x + w / 2, y + h / 2 - 8);
			
			// Value
			ctx.font = 'bold 14px Inter, sans-serif';
			ctx.fillText(`${item.value.toFixed(1)}`, x + w / 2, y + h / 2 + 8);
		});

		// Draw legend
		drawLegend();
	}

	function drawLegend() {
		const legendY = height - 30;
		const legendWidth = width - 40;
		const legendHeight = 20;
		const legendX = 20;

		// Draw legend background
		ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
		ctx.fillRect(legendX - 5, legendY - 5, legendWidth + 10, legendHeight + 10);

		// Draw gradient
		const gradient = ctx.createLinearGradient(legendX, 0, legendX + legendWidth, 0);
		gradient.addColorStop(0, '#ef4444'); // Red (0-20)
		gradient.addColorStop(0.2, '#f97316'); // Orange (20-40)
		gradient.addColorStop(0.4, '#eab308'); // Yellow (40-60)
		gradient.addColorStop(0.6, '#22c55e'); // Green (60-80)
		gradient.addColorStop(1, '#10b981'); // Emerald (80-100)

		ctx.fillStyle = gradient;
		ctx.fillRect(legendX, legendY, legendWidth, legendHeight);

		// Draw legend labels
		ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
		ctx.font = '10px Inter, sans-serif';
		ctx.textAlign = 'left';
		ctx.fillText('Poor', legendX, legendY - 8);
		ctx.textAlign = 'right';
		ctx.fillText('Excellent', legendX + legendWidth, legendY - 8);
	}

	function getHeatmapColor(value) {
		// Normalize value to 0-1 range
		const normalized = Math.max(0, Math.min(100, value)) / 100;
		
		if (normalized < 0.2) {
			// Red (0-20)
			return `rgba(239, 68, 68, ${0.3 + normalized * 0.7})`;
		} else if (normalized < 0.4) {
			// Orange (20-40)
			return `rgba(249, 115, 22, ${0.3 + normalized * 0.7})`;
		} else if (normalized < 0.6) {
			// Yellow (40-60)
			return `rgba(234, 179, 8, ${0.3 + normalized * 0.7})`;
		} else if (normalized < 0.8) {
			// Green (60-80)
			return `rgba(34, 197, 94, ${0.3 + normalized * 0.7})`;
		} else {
			// Emerald (80-100)
			return `rgba(16, 185, 129, ${0.3 + normalized * 0.7})`;
		}
	}

	// Initialize canvas context
	$: if (canvas) {
		ctx = canvas.getContext('2d');
		drawHeatmap();
	}
</script>

<div class="space-y-4">
	<div class="flex justify-between items-center">
		<h3 class="text-lg font-semibold text-white">Quality Heatmap</h3>
		<div class="text-sm text-gray-400">
			Visual overview of quality metrics
		</div>
	</div>
	
	<div class="bg-white/5 rounded-xl p-4 border border-white/10">
		<canvas 
			bind:this={canvas}
			{width}
			{height}
			class="w-full h-auto"
		></canvas>
	</div>

	<!-- Quality Categories Summary -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
		{#each ['Code Quality', 'Testing', 'Security', 'Performance'] as category}
			{@const categoryItems = heatmapData.filter(item => item.category === category)}
			{@const avgScore = categoryItems.length > 0 ? categoryItems.reduce((sum, item) => sum + item.value, 0) / categoryItems.length : 0}
			<div class="bg-white/5 rounded-lg p-3 border border-white/10">
				<div class="text-sm text-gray-400 mb-1">{category}</div>
				<div class="text-lg font-semibold text-white">{avgScore.toFixed(1)}</div>
				<div class="w-full bg-white/10 rounded-full h-2 mt-2">
					<div 
						class="h-2 rounded-full transition-all duration-500"
						style="width: {avgScore}%; background-color: {getHeatmapColor(avgScore).replace('rgba', 'rgb').replace(/, [\d.]+\)/, ')')}"
					></div>
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	canvas {
		background: transparent;
		border-radius: 8px;
	}
</style>