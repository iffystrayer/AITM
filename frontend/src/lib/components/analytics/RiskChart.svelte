<script lang="ts">
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';
	import type { ChartConfiguration } from 'chart.js';

	Chart.register(...registerables);

	export let data: any[] = [];
	export let title = 'Risk Score Trends';
	export let height = '400px';

	let canvas: HTMLCanvasElement;
	let chart: Chart;

	// Sample data if none provided
	const sampleData = [
		{ date: '2025-01-01', riskScore: 7.2, projects: 12, highRisk: 3 },
		{ date: '2025-01-07', riskScore: 6.8, projects: 15, highRisk: 2 },
		{ date: '2025-01-14', riskScore: 5.9, projects: 18, highRisk: 2 },
		{ date: '2025-01-21', riskScore: 6.1, projects: 22, highRisk: 3 },
		{ date: '2025-01-28', riskScore: 5.4, projects: 25, highRisk: 1 },
		{ date: '2025-02-04', riskScore: 4.8, projects: 28, highRisk: 1 },
		{ date: '2025-02-11', riskScore: 4.2, projects: 31, highRisk: 0 }
	];

	const chartData = data.length > 0 ? data : sampleData;

	onMount(() => {
		const config: ChartConfiguration = {
			type: 'line',
			data: {
				labels: chartData.map(d => new Date(d.date).toLocaleDateString()),
				datasets: [
					{
						label: 'Average Risk Score',
						data: chartData.map(d => d.riskScore),
						borderColor: 'rgb(239, 68, 68)',
						backgroundColor: 'rgba(239, 68, 68, 0.1)',
						borderWidth: 3,
						fill: true,
						tension: 0.4,
						yAxisID: 'y'
					},
					{
						label: 'Total Projects',
						data: chartData.map(d => d.projects),
						borderColor: 'rgb(59, 130, 246)',
						backgroundColor: 'rgba(59, 130, 246, 0.1)',
						borderWidth: 2,
						fill: false,
						tension: 0.4,
						yAxisID: 'y1'
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: {
					mode: 'index',
					intersect: false
				},
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
						position: 'top'
					}
				},
				scales: {
					x: {
						display: true,
						title: {
							display: true,
							text: 'Date'
						}
					},
					y: {
						type: 'linear',
						display: true,
						position: 'left',
						title: {
							display: true,
							text: 'Risk Score'
						},
						min: 0,
						max: 10
					},
					y1: {
						type: 'linear',
						display: true,
						position: 'right',
						title: {
							display: true,
							text: 'Project Count'
						},
						grid: {
							drawOnChartArea: false
						}
					}
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
</div>

<style>
	.chart-container {
		position: relative;
		width: 100%;
	}
</style>
