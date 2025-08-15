<script>
	import { onMount, afterUpdate } from 'svelte';
	
	export let data = [];
	export let height = '300px';
	export let detailed = false;
	export let metrics = ['maintainabilityIndex', 'codeCoverage', 'securityScore'];
	export let colors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444'];

	let chartContainer;
	let canvas;
	let ctx;
	let chartWidth = 800;
	let chartHeight = 300;
	let padding = { top: 20, right: 20, bottom: 40, left: 60 };

	onMount(() => {
		if (chartContainer) {
			const rect = chartContainer.getBoundingClientRect();
			chartWidth = rect.width;
			chartHeight = parseInt(height);
		}
		drawChart();
	});

	afterUpdate(() => {
		drawChart();
	});

	function drawChart() {
		if (!canvas || !ctx || !data || data.length === 0) return;

		// Clear canvas
		ctx.clearRect(0, 0, chartWidth, chartHeight);

		// Set canvas size
		canvas.width = chartWidth;
		canvas.height = chartHeight;

		// Calculate chart dimensions
		const chartArea = {
			x: padding.left,
			y: padding.top,
			width: chartWidth - padding.left - padding.right,
			height: chartHeight - padding.top - padding.bottom
		};

		// Draw background
		ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
		ctx.fillRect(chartArea.x, chartArea.y, chartArea.width, chartArea.height);

		// Draw grid
		drawGrid(chartArea);

		// Draw data lines
		metrics.forEach((metric, index) => {
			if (data.some(d => d[metric] !== undefined)) {
				drawLine(data, metric, colors[index % colors.length], chartArea);
			}
		});

		// Draw legend
		drawLegend(chartArea);

		// Draw axes
		drawAxes(chartArea);
	}

	function drawGrid(chartArea) {
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
		ctx.lineWidth = 1;

		// Vertical grid lines
		const xStep = chartArea.width / Math.max(1, data.length - 1);
		for (let i = 0; i <= data.length - 1; i++) {
			const x = chartArea.x + i * xStep;
			ctx.beginPath();
			ctx.moveTo(x, chartArea.y);
			ctx.lineTo(x, chartArea.y + chartArea.height);
			ctx.stroke();
		}

		// Horizontal grid lines
		const ySteps = 5;
		const yStep = chartArea.height / ySteps;
		for (let i = 0; i <= ySteps; i++) {
			const y = chartArea.y + i * yStep;
			ctx.beginPath();
			ctx.moveTo(chartArea.x, y);
			ctx.lineTo(chartArea.x + chartArea.width, y);
			ctx.stroke();
		}
	}

	function drawLine(data, metric, color, chartArea) {
		const values = data.map(d => d[metric]).filter(v => v !== undefined);
		if (values.length === 0) return;

		const minValue = Math.min(...values);
		const maxValue = Math.max(...values);
		const range = maxValue - minValue || 1;

		ctx.strokeStyle = color;
		ctx.lineWidth = 3;
		ctx.lineCap = 'round';
		ctx.lineJoin = 'round';

		// Draw line
		ctx.beginPath();
		data.forEach((point, index) => {
			if (point[metric] !== undefined) {
				const x = chartArea.x + (index / Math.max(1, data.length - 1)) * chartArea.width;
				const y = chartArea.y + chartArea.height - ((point[metric] - minValue) / range) * chartArea.height;
				
				if (index === 0 || data[index - 1][metric] === undefined) {
					ctx.moveTo(x, y);
				} else {
					ctx.lineTo(x, y);
				}
			}
		});
		ctx.stroke();

		// Draw points
		ctx.fillStyle = color;
		data.forEach((point, index) => {
			if (point[metric] !== undefined) {
				const x = chartArea.x + (index / Math.max(1, data.length - 1)) * chartArea.width;
				const y = chartArea.y + chartArea.height - ((point[metric] - minValue) / range) * chartArea.height;
				
				ctx.beginPath();
				ctx.arc(x, y, 4, 0, 2 * Math.PI);
				ctx.fill();
			}
		});

		// Draw area fill (optional)
		if (detailed) {
			const gradient = ctx.createLinearGradient(0, chartArea.y, 0, chartArea.y + chartArea.height);
			gradient.addColorStop(0, color + '40');
			gradient.addColorStop(1, color + '10');
			
			ctx.fillStyle = gradient;
			ctx.beginPath();
			
			let firstPoint = true;
			data.forEach((point, index) => {
				if (point[metric] !== undefined) {
					const x = chartArea.x + (index / Math.max(1, data.length - 1)) * chartArea.width;
					const y = chartArea.y + chartArea.height - ((point[metric] - minValue) / range) * chartArea.height;
					
					if (firstPoint) {
						ctx.moveTo(x, chartArea.y + chartArea.height);
						ctx.lineTo(x, y);
						firstPoint = false;
					} else {
						ctx.lineTo(x, y);
					}
				}
			});
			
			// Close the area
			const lastIndex = data.length - 1;
			const lastX = chartArea.x + chartArea.width;
			ctx.lineTo(lastX, chartArea.y + chartArea.height);
			ctx.closePath();
			ctx.fill();
		}
	}

	function drawLegend(chartArea) {
		const legendY = chartArea.y + chartArea.height + 15;
		let legendX = chartArea.x;

		ctx.font = '12px Inter, sans-serif';
		ctx.textAlign = 'left';

		metrics.forEach((metric, index) => {
			const color = colors[index % colors.length];
			const label = formatMetricName(metric);

			// Draw color indicator
			ctx.fillStyle = color;
			ctx.fillRect(legendX, legendY, 12, 12);

			// Draw label
			ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
			ctx.fillText(label, legendX + 18, legendY + 9);

			legendX += ctx.measureText(label).width + 40;
		});
	}

	function drawAxes(chartArea) {
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
		ctx.lineWidth = 2;

		// Y-axis
		ctx.beginPath();
		ctx.moveTo(chartArea.x, chartArea.y);
		ctx.lineTo(chartArea.x, chartArea.y + chartArea.height);
		ctx.stroke();

		// X-axis
		ctx.beginPath();
		ctx.moveTo(chartArea.x, chartArea.y + chartArea.height);
		ctx.lineTo(chartArea.x + chartArea.width, chartArea.y + chartArea.height);
		ctx.stroke();

		// Y-axis labels
		ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
		ctx.font = '11px Inter, sans-serif';
		ctx.textAlign = 'right';
		
		for (let i = 0; i <= 5; i++) {
			const y = chartArea.y + chartArea.height - (i / 5) * chartArea.height;
			const value = (i / 5) * 100;
			ctx.fillText(value.toFixed(0), chartArea.x - 10, y + 4);
		}

		// X-axis labels (dates)
		ctx.textAlign = 'center';
		const labelStep = Math.max(1, Math.floor(data.length / 6));
		
		data.forEach((point, index) => {
			if (index % labelStep === 0 || index === data.length - 1) {
				const x = chartArea.x + (index / Math.max(1, data.length - 1)) * chartArea.width;
				const date = new Date(point.date);
				const label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
				ctx.fillText(label, x, chartArea.y + chartArea.height + 20);
			}
		});
	}

	function formatMetricName(metric) {
		const names = {
			maintainabilityIndex: 'Maintainability',
			codeCoverage: 'Coverage',
			securityScore: 'Security',
			technicalDebt: 'Tech Debt',
			issueCount: 'Issues'
		};
		return names[metric] || metric;
	}

	// Initialize canvas context
	$: if (canvas) {
		ctx = canvas.getContext('2d');
		drawChart();
	}
</script>

<div bind:this={chartContainer} class="w-full" style="height: {height}">
	<canvas 
		bind:this={canvas}
		class="w-full h-full"
		style="height: {height}"
	></canvas>
</div>

<style>
	canvas {
		background: transparent;
	}
</style>