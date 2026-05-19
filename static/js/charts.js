document.addEventListener("DOMContentLoaded", function() {
    // Doughnut Chart for Expenses by Category
    if (document.getElementById('expensesChart') && window.expensesLabels && window.expensesData) {
        const ctxExpenses = document.getElementById('expensesChart').getContext('2d');
        new Chart(ctxExpenses, {
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
                        position: 'right',
                    }
                }
            }
        });
    }

    // Grouped Bar Chart for Monthly Income vs Expense (starting from May)
    if (document.getElementById('balanceChart') && window.barLabels && window.barIncome && window.barExpense) {
        const ctxBalance = document.getElementById('balanceChart').getContext('2d');

        new Chart(ctxBalance, {
            type: 'bar',
            data: {
                labels: window.barLabels,
                datasets: [
                    {
                        label: 'Income ($)',
                        data: window.barIncome,
                        backgroundColor: 'rgba(34, 197, 94, 0.7)',
                        borderColor: '#16a34a',
                        borderWidth: 1,
                        borderRadius: 4,
                    },
                    {
                        label: 'Expense ($)',
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
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ctx.dataset.label.replace('($)', '') + ': $' + ctx.raw.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    }
});
