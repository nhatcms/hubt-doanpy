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

    // Mock Line Chart for Balance History (7 days)
    if (document.getElementById('balanceChart')) {
        const ctxBalance = document.getElementById('balanceChart').getContext('2d');
        
        // Mock data
        const today = new Date();
        const dates = [];
        const balances = [1000, 1200, 1150, 1100, 1300, 1250, 1500]; // Mock balance
        
        for (let i = 6; i >= 0; i--) {
            const d = new Date(today);
            d.setDate(today.getDate() - i);
            dates.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        }

        new Chart(ctxBalance, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Balance ($)',
                    data: balances,
                    borderColor: '#36a2eb',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
});
