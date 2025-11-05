// Analytics Charts with real data from APIs

let serviceChart;

// Get filter parameters from URL
function getFilterParams() {
    const urlParams = new URLSearchParams(window.location.search);
    return {
        start_date: urlParams.get('start_date') || '',
        end_date: urlParams.get('end_date') || '',
        service: urlParams.get('service') || '',
        entity: urlParams.get('entity') || ''
    };
}

// Load Service Chart
async function loadServiceChart() {
    const filters = getFilterParams();
    const params = new URLSearchParams(filters);
    
    try {
        const response = await fetch(`/app/api/analytics-service/?${params}`);
        const data = await response.json();
        
        const ctx = document.getElementById('serviceChart');
        if (!ctx) return;
        
        if (serviceChart) {
            serviceChart.destroy();
        }
        
        serviceChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: [
                        '#8b5cf6',
                        '#10b981',
                        '#3b82f6',
                        '#f59e0b',
                        '#ef4444',
                        '#6366f1',
                        '#ec4899',
                        '#14b8a6',
                        '#f97316',
                        '#84cc16'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toLocaleString() + ' GNF';
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    } catch (error) {
        console.error('Error loading service chart:', error);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Load chart
    loadServiceChart();
});
