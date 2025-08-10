<script>
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	export let data = [];
	export let title = 'Threat Distribution';
	export let height = '300px';

	let canvas;
	let chart;

	// Sample data based on MITRE ATT&CK tactics
	const sampleData = [
		{ category: 'Initial Access', count: 23, color: '#EF4444' },
		{ category: 'Execution', count: 18, color: '#F97316' },
		{ category: 'Persistence', count: 15, color: '#EAB308' },
		{ category: 'Privilege Escalation', count: 12, color: '#22C55E' },
		{ category: 'Defense Evasion', count: 28, color: '#06B6D4' },
		{ category: 'Credential Access', count: 10, color: '#3B82F6' },
		{ category: 'Discovery', count: 8, color: '#8B5CF6' },
		{ category: 'Lateral Movement', count: 6, color: '#EC4899' },
		{ category: 'Collection', count: 4, color: '#10B981' },
		{ category: 'Exfiltration', count: 3, color: '#F59E0B' }
	];

	const chartData = data.length > 0 ? data : sampleData;
	const totalThreats = chartData.reduce((sum, item) => sum + item.count, 0);

	onMount(() => {
		const config = {
			type: 'doughnut',
			data: {
				labels: chartData.map(d => d.category),
				datasets: [
					{
						data: chartData.map(d => d.count),
						backgroundColor: chartData.map(d => d.color),
						borderWidth: 2,
						borderColor: '#ffffff',
						hoverBorderWidth: 3
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					title: {
						display: true,
						text: title,
						font: {
							size: 16,
							weight: 'bold'
						}
					},
					legend: {
						position: 'right',
						labels: {
							usePointStyle: true,
							padding: 20,
							font: {
								size: 12
							},
						generateLabels: (chart) => {
							const data = chart.data;
							if (data.labels && data.labels.length && data.datasets.length) {
								return data.labels.map((label, i) => {
									const value = data.datasets[0].data[i];
									const percentage = ((value / totalThreats) * 100).toFixed(1);
									return {
										text: `${label} (${percentage}%)`,
										fillStyle: data.datasets[0].backgroundColor[i],
										strokeStyle: data.datasets[0].backgroundColor[i],
										lineWidth: 0,
										pointStyle: 'circle',
										hidden: false,
										index: i
									};
								});
							}
							return [];
						}
						}
					},
					tooltip: {
						callbacks: {
							label: function(context) {
								const label = context.label || '';
								const value = context.parsed;
								const percentage = ((value / totalThreats) * 100).toFixed(1);
								return `${label}: ${value} threats (${percentage}%)`;
							}
						}
					}
				},
				cutout: '60%',
				animation: {
					animateRotate: true,
					animateScale: true,
					duration: 1000
				}
			}
		};

		chart = new Chart(canvas, config);

		return () => {
			chart?.destroy();
		};
	});
</script>

<div class="chart-container" style="height: {height}">
	<canvas bind:this={canvas}></canvas>
	<div class="center-text">
		<div class="total-number">{totalThreats}</div>
		<div class="total-label">Total Threats</div>
	</div>
</div>

<style>
	.chart-container {
		position: relative;
		width: 100%;
	}

	.center-text {
		position: absolute;
		top: 50%;
		left: 40%;
		transform: translate(-50%, -50%);
		text-align: center;
		pointer-events: none;
	}

	.total-number {
		font-size: 2rem;
		font-weight: bold;
		color: #374151;
	}

	.total-label {
		font-size: 0.875rem;
		color: #6B7280;
		margin-top: 0.25rem;
	}

	:global(.dark) .total-number {
		color: #F9FAFB;
	}

	:global(.dark) .total-label {
		color: #9CA3AF;
	}
</style>
