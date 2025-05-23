/* Dashboard JavaScript */

// Global variables
let charts = {};
let currentFilters = {
    bankType: 'All',
    bank: 'All',
    month: 'All'
};

// Format large numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filters
    initializeFilters();
    
    // Load initial data
    loadDashboardData();
    
    // Set up event listeners
    setupEventListeners();
});

// Initialize filter dropdowns
function initializeFilters() {
    // Bank type filter change event
    document.getElementById('bank-type-filter').addEventListener('change', function() {
        currentFilters.bankType = this.value;
        loadBanksByType(this.value);
        updateDashboard();
    });
    
    // Bank filter change event
    document.getElementById('bank-filter').addEventListener('change', function() {
        currentFilters.bank = this.value;
        updateDashboard();
    });
    
    // Month filter change event
    document.getElementById('month-filter').addEventListener('change', function() {
        currentFilters.month = this.value;
        updateDashboard();
    });
    
    // Load banks for initial bank type
    loadBanksByType('All');
}

// Load banks based on selected bank type
function loadBanksByType(bankType) {
    fetch(`/api/banks?bank_type=${encodeURIComponent(bankType)}`)
        .then(response => response.json())
        .then(banks => {
            const bankSelect = document.getElementById('bank-filter');
            bankSelect.innerHTML = '<option value="All">All Banks</option>';
            
            banks.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank;
                option.textContent = bank;
                bankSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading banks:', error);
            showNotification('Error loading bank list. Please try again.', 'error');
        });
}

// Set up event listeners
function setupEventListeners() {
    // Check for updates button
    document.getElementById('check-updates-btn').addEventListener('click', checkForUpdates);
    
    // Refresh data button
    document.getElementById('refresh-data-btn').addEventListener('click', refreshData);
    
    // Export CSV button
    document.getElementById('export-csv-btn').addEventListener('click', exportToCSV);
}

// Load all dashboard data
function loadDashboardData() {
    // Show loading indicators
    showLoadingState();
    
    // Load overview data
    loadOverviewData();
    
    // Load credit card data
    loadCreditCardData();
    
    // Load debit card data
    loadDebitCardData();
    
    // Load comparison data
    loadComparisonData();
    
    // Load growth analysis data
    loadGrowthAnalysisData();
    
    // Load detailed data table
    loadDetailedData();
}

// Show loading state for all charts and tables
function showLoadingState() {
    document.getElementById('total-credit-cards').textContent = 'Loading...';
    document.getElementById('total-debit-cards').textContent = 'Loading...';
    document.getElementById('top-credit-card-banks').innerHTML = '<tr><td colspan="2" class="text-center">Loading...</td></tr>';
    document.getElementById('top-debit-card-banks').innerHTML = '<tr><td colspan="2" class="text-center">Loading...</td></tr>';
    document.getElementById('detailed-data-table').innerHTML = '<tr><td colspan="5" class="text-center">Loading...</td></tr>';
}

// Update the entire dashboard based on current filters
function updateDashboard() {
    loadDashboardData();
}

// Load overview data
function loadOverviewData() {
    // Load total cards data
    fetch(`/api/credit_card_data?bank_type=${encodeURIComponent(currentFilters.bankType)}&bank_name=${encodeURIComponent(currentFilters.bank)}`)
        .then(response => response.json())
        .then(data => {
            // Calculate total credit cards
            const totalCreditCards = data.reduce((sum, item) => sum + item.credit_cards, 0);
            document.getElementById('total-credit-cards').textContent = formatNumber(totalCreditCards);
            
            // Load debit card data for overview
            return fetch(`/api/debit_card_data?bank_type=${encodeURIComponent(currentFilters.bankType)}&bank_name=${encodeURIComponent(currentFilters.bank)}`);
        })
        .then(response => response.json())
        .then(data => {
            // Calculate total debit cards
            const totalDebitCards = data.reduce((sum, item) => sum + item.debit_cards, 0);
            document.getElementById('total-debit-cards').textContent = formatNumber(totalDebitCards);
            
            // Create card distribution chart
            createCardDistributionChart(
                parseInt(document.getElementById('total-credit-cards').textContent.replace(/,/g, '')),
                parseInt(document.getElementById('total-debit-cards').textContent.replace(/,/g, ''))
            );
        })
        .catch(error => {
            console.error('Error loading overview data:', error);
            showNotification('Error loading overview data. Please try again.', 'error');
        });
}

// Create card distribution chart
function createCardDistributionChart(creditCards, debitCards) {
    const ctx = document.getElementById('card-distribution-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (charts.cardDistribution) {
        charts.cardDistribution.destroy();
    }
    
    // Create new chart
    charts.cardDistribution = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Credit Cards', 'Debit Cards'],
            datasets: [{
                data: [creditCards, debitCards],
                backgroundColor: ['#0d6efd', '#198754'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw;
                            const percentage = Math.round((value / (creditCards + debitCards)) * 100);
                            return `${label}: ${formatNumber(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Load credit card data
function loadCreditCardData() {
    // Load trend data
    fetch(`/api/trend_data?card_type=credit&bank_type=${encodeURIComponent(currentFilters.bankType)}`)
        .then(response => response.json())
        .then(data => {
            createTrendChart('credit-card-trend-chart', data, 'Credit Cards', '#0d6efd');
        })
        .catch(error => {
            console.error('Error loading credit card trend data:', error);
        });
    
    // Load top banks data
    fetch(`/api/top_banks?card_type=credit&limit=10`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('top-credit-card-banks');
            tableBody.innerHTML = '';
            
            data.forEach(bank => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${bank.bank_name}</td>
                    <td>${formatNumber(bank.credit_cards)}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading top credit card banks:', error);
        });
}

// Load debit card data
function loadDebitCardData() {
    // Load trend data
    fetch(`/api/trend_data?card_type=debit&bank_type=${encodeURIComponent(currentFilters.bankType)}`)
        .then(response => response.json())
        .then(data => {
            createTrendChart('debit-card-trend-chart', data, 'Debit Cards', '#198754');
        })
        .catch(error => {
            console.error('Error loading debit card trend data:', error);
        });
    
    // Load top banks data
    fetch(`/api/top_banks?card_type=debit&limit=10`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('top-debit-card-banks');
            tableBody.innerHTML = '';
            
            data.forEach(bank => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${bank.bank_name}</td>
                    <td>${formatNumber(bank.debit_cards)}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading top debit card banks:', error);
        });
}

// Create trend chart
function createTrendChart(canvasId, data, label, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Sort data by month
    data.sort((a, b) => new Date(a.month_str) - new Date(b.month_str));
    
    // Extract labels and values
    const labels = data.map(item => item.month_str);
    const values = data.map(item => item.value);
    
    // Destroy existing chart if it exists
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    // Create new chart
    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: color,
                borderColor: color,
                borderWidth: 2,
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatNumber(context.raw)}`;
                        }
                    }
                }
            }
        }
    });
}

// Load comparison data
function loadComparisonData() {
    fetch(`/api/comparison_data?bank_name=${encodeURIComponent(currentFilters.bank)}`)
        .then(response => response.json())
        .then(data => {
            createComparisonChart(data);
        })
        .catch(error => {
            console.error('Error loading comparison data:', error);
        });
}

// Create comparison chart
function createComparisonChart(data) {
    const ctx = document.getElementById('comparison-chart').getContext('2d');
    
    // Sort data by month
    data.sort((a, b) => new Date(a.month_str) - new Date(b.month_str));
    
    // Extract labels and values
    const labels = data.map(item => item.month_str);
    const creditCardValues = data.map(item => item.credit_cards);
    const debitCardValues = data.map(item => item.debit_cards);
    
    // Destroy existing chart if it exists
    if (charts.comparison) {
        charts.comparison.destroy();
    }
    
    // Create new chart
    charts.comparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Credit Cards',
                    data: creditCardValues,
                    backgroundColor: '#0d6efd',
                    borderColor: '#0d6efd',
                    borderWidth: 1
                },
                {
                    label: 'Debit Cards',
                    data: debitCardValues,
                    backgroundColor: '#198754',
                    borderColor: '#198754',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatNumber(context.raw)}`;
                        }
                    }
                }
            }
        }
    });
}

// Load growth analysis data
function loadGrowthAnalysisData() {
    // Load credit card growth data
    fetch(`/api/credit_card_data?bank_type=${encodeURIComponent(currentFilters.bankType)}&bank_name=${encodeURIComponent(currentFilters.bank)}&include_growth=true`)
        .then(response => response.json())
        .then(data => {
            createGrowthChart('credit-card-growth-chart', data, 'Credit Card Growth (%)', '#0d6efd');
        })
        .catch(error => {
            console.error('Error loading credit card growth data:', error);
        });
    
    // Load debit card growth data
    fetch(`/api/debit_card_data?bank_type=${encodeURIComponent(currentFilters.bankType)}&bank_name=${encodeURIComponent(currentFilters.bank)}&include_growth=true`)
        .then(response => response.json())
        .then(data => {
            createGrowthChart('debit-card-growth-chart', data, 'Debit Card Growth (%)', '#198754');
        })
        .catch(error => {
            console.error('Error loading debit card growth data:', error);
        });
}

// Create growth chart
function createGrowthChart(canvasId, data, label, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Filter out entries without growth data and sort by month
    const filteredData = data.filter(item => item.growth !== null && !isNaN(item.growth));
    filteredData.sort((a, b) => new Date(a.month_str) - new Date(b.month_str));
    
    // Group by month and calculate average growth
    const monthlyGrowth = {};
    filteredData.forEach(item => {
        if (!monthlyGrowth[item.month_str]) {
            monthlyGrowth[item.month_str] = {
                sum: 0,
                count: 0
            };
        }
        monthlyGrowth[item.month_str].sum += item.growth;
        monthlyGrowth[item.month_str].count += 1;
    });
    
    // Calculate average growth for each month
    const labels = [];
    const values = [];
    for (const month in monthlyGrowth) {
        labels.push(month);
        values.push(monthlyGrowth[month].sum / monthlyGrowth[month].count);
    }
    
    // Destroy existing chart if it exists
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    // Create new chart
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: color,
                borderColor: color,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2) + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks:
(Content truncated due to size limit. Use line ranges to read in chunks)