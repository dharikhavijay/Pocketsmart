// PocketSmart AI Chart.js Helper

function initBudgetAllocationChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const modernPalette = [
        '#4F46E5', // Indigo
        '#06B6D4', // Cyan
        '#F59E0B', // Amber
        '#10B981', // Emerald
        '#EC4899', // Pink
        '#8B5CF6'  // Purple
    ];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: modernPalette.slice(0, labels.length),
                borderColor: '#FFFFFF',
                borderWidth: 2,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 14,
                        padding: 16,
                        font: { family: 'Inter', size: 12, weight: '500' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return ` ₹${value.toLocaleString('en-IN')} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '68%'
        }
    });
}
