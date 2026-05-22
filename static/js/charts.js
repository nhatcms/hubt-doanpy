document.addEventListener("DOMContentLoaded", function() {
    // Store chart instances globally so we can destroy before recreating
    window._chartInstances = window._chartInstances || [];

    // Destroy all existing chart instances
    function destroyCharts() {
        window._chartInstances.forEach(function(chart) {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        window._chartInstances = [];
    }

    // Function to create all charts
    function createCharts() {
        // Destroy any existing charts first
        destroyCharts();

        const isMobile = window.innerWidth <= 640;

        // Pie Chart for Income by Category
        if (document.getElementById('incomeChart') && window.incomeLabels && window.incomeData) {
            const ctxIncome = document.getElementById('incomeChart').getContext('2d');
            const incomeChart = new Chart(ctxIncome, {
                type: 'pie',
                data: {
                    labels: window.incomeLabels,
                    datasets: [{
                        data: window.incomeData,
                        backgroundColor: [
                            '#22c55e',
                            '#10b981',
                            '#059669',
                            '#047857',
                            '#065f46',
                            '#064e3b'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: isMobile ? 'bottom' : 'right',
                            labels: {
                                boxWidth: isMobile ? 12 : 15,
                                padding: isMobile ? 8 : 15,
                                font: {
                                    size: isMobile ? 10 : 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.label + ': $' + ctx.raw.toFixed(2);
                                }
                            }
                        }
                    },
                    layout: {
                        padding: isMobile ? 10 : 20
                    }
                }
            });
            window._chartInstances.push(incomeChart);
        }

        // Doughnut Chart for Expenses by Category
        if (document.getElementById('expensesChart') && window.expensesLabels && window.expensesData) {
            const ctxExpenses = document.getElementById('expensesChart').getContext('2d');
            const expensesChart = new Chart(ctxExpenses, {
                type: 'doughnut',
                data: {
                    labels: window.expensesLabels,
                    datasets: [{
                        data: window.expensesData,
                        backgroundColor: [
                            '#ff6384',
                            '#36a2eb',
                            '#ffce56',
                            '#4bc0c0',
                            '#9966ff',
                            '#ff9f40'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: isMobile ? 'bottom' : 'right',
                            labels: {
                                boxWidth: isMobile ? 12 : 15,
                                padding: isMobile ? 8 : 15,
                                font: {
                                    size: isMobile ? 10 : 12
                                }
                            }
                        }
                    },
                    layout: {
                        padding: isMobile ? 10 : 20
                    }
                }
            });
            window._chartInstances.push(expensesChart);
        }

        // Grouped Bar Chart for Monthly Income vs Expense
        if (document.getElementById('balanceChart') && window.barLabels && window.barIncome && window.barExpense) {
            const ctxBalance = document.getElementById('balanceChart').getContext('2d');
            const monthLabels = (isMobile && window.barLabelsShort)
                ? window.barLabelsShort
                : window.barLabels;
            const balanceChart = new Chart(ctxBalance, {
                type: 'bar',
                data: {
                    labels: monthLabels,
                    datasets: [
                        {
                            label: 'Income',
                            data: window.barIncome,
                            backgroundColor: 'rgba(34, 197, 94, 0.7)',
                            borderColor: '#16a34a',
                            borderWidth: 1,
                            borderRadius: 4,
                        },
                        {
                            label: 'Expense',
                            data: window.barExpense,
                            backgroundColor: 'rgba(239, 68, 68, 0.7)',
                            borderColor: '#dc2626',
                            borderWidth: 1,
                            borderRadius: 4,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: isMobile ? 'y' : 'x',
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                boxWidth: isMobile ? 12 : 15,
                                padding: isMobile ? 8 : 15,
                                font: {
                                    size: isMobile ? 10 : 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': $' + ctx.raw.toFixed(2);
                                }
                            }
                        }
                    },
                    scales: isMobile ? {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value;
                                },
                                font: { size: 10 }
                            }
                        },
                        y: {
                            ticks: {
                                autoSkip: false,
                                callback: function(value) {
                                    return this.getLabelForValue(value);
                                },
                                font: { size: 10 }
                            }
                        }
                    } : {
                        x: {
                            ticks: {
                                autoSkip: false,
                                callback: function(value) {
                                    return this.getLabelForValue(value);
                                },
                                font: { size: 12 }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value;
                                },
                                font: { size: 12 }
                            }
                        }
                    }
                }
            });
            window._chartInstances.push(balanceChart);
        }
    }

    // Initial chart creation
    createCharts();

    // Debounced resize handler - recreate charts when crossing the mobile breakpoint
    let resizeTimer;
    let wasMobile = window.innerWidth <= 640;

    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            const isMobileNow = window.innerWidth <= 640;
            // Only recreate if we crossed the mobile/desktop boundary
            if (isMobileNow !== wasMobile) {
                wasMobile = isMobileNow;
                createCharts();
            }
        }, 300);
    });
});
