<script>
    import { onMount, afterUpdate } from 'svelte';
    import Chart from 'chart.js/auto';

    export let historicalData = [];
    export let futureData = [];

    let chart;

    function renderChart() {
        if (!chart) {
            const ctx = document.getElementById('riskTrendChartCanvas').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [...historicalData.map(d => new Date(d.date).toLocaleDateString()), ...futureData.map(d => new Date(d.date).toLocaleDateString())],
                    datasets: [{
                        label: 'Historical Risk Score',
                        data: historicalData.map(d => d.riskScore),
                        fill: false,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }, {
                        label: 'Predicted Risk Score',
                        data: [...new Array(historicalData.length).fill(null), ...futureData.map(d => d.riskScore)],
                        fill: false,
                        borderColor: 'rgb(255, 99, 132)',
                        borderDash: [5, 5],
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        } else {
            chart.data.labels = [...historicalData.map(d => new Date(d.date).toLocaleDateString()), ...futureData.map(d => new Date(d.date).toLocaleDateString())];
            chart.data.datasets[0].data = historicalData.map(d => d.riskScore);
            chart.data.datasets[1].data = [...new Array(historicalData.length).fill(null), ...futureData.map(d => d.riskScore)];
            chart.update();
        }
    }

    onMount(() => {
        renderChart();
    });

    afterUpdate(() => {
        renderChart();
    });
</script>

<canvas id="riskTrendChartCanvas"></canvas>
