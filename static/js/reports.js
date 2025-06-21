let chart; // Declare the chart object globally

document.addEventListener('DOMContentLoaded', function() {
    // Generate chart data
    const generateChartData = () => {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'];
        const packageData = [];
        const theftData = [];
        
        for (let i = 0; i < months.length; i++) {
            packageData.push(Math.floor(Math.random() * 25) + 10);
            theftData.push(Math.floor(Math.random() * 8) + 1);
        }
        
        return {
            labels: months,
            packageData,
            theftData
        };
    };
    
    // Generate detection records
    const generateDetectionRecords = () => {
        const locations = ['123 Main St', '456 Main St', '789 Oak St', '101 Pine St', '12 Cedar St'];
        const confidenceLevels = ['High', 'Medium', 'Low'];
        const data = [];
        
        for (let i = 1; i <= 9; i++) {
            data.push({
                id: `id-${i}`,
                date: `Jan ${i}`,
                time: `${i}:00 ${i % 2 === 0 ? 'PM' : 'AM'}`,
                location: locations[Math.floor(Math.random() * locations.length)],
                confidence: confidenceLevels[Math.floor(Math.random() * confidenceLevels.length)],
                packageTheft: Math.random() > 0.4,
            });
        }
        
        return data;
    };
    
    // Initialize chart
    const chartCanvas = document.getElementById('detectionChart');
    
    if (chartCanvas) {
        const labels = graphData.map(data => data.date); // X-axis labels (dates)
        const packageData = graphData.map(data => data.deliveries); // Y-axis data for deliveries
        const theftData = graphData.map(data => data.thefts); // Y-axis data for thefts

        chart = new Chart(chartCanvas, {
            type: 'line', // Change chart type to 'line'
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Package Deliveries',
                        data: packageData,
                        borderColor: 'rgba(96, 165, 250, 1)', // Line color for deliveries
                        backgroundColor: 'rgba(96, 165, 250, 0.2)', // Fill under the line
                        borderWidth: 2,
                        tension: 0.4, // Smooth curves
                        fill: true // Fill the area under the line
                    },
                    {
                        label: 'Theft Detections',
                        data: theftData,
                        borderColor: 'rgba(248, 113, 113, 1)', // Line color for thefts
                        backgroundColor: 'rgba(248, 113, 113, 0.2)', // Fill under the line
                        borderWidth: 2,
                        tension: 0.4, // Smooth curves
                        fill: true // Fill the area under the line
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }
    
    // Populate table with data
    const tableBody = document.getElementById('detectionTableBody');
    
    if (tableBody) {
        detectionData.forEach(record => {
            const row = document.createElement('tr');

            // Classify confidence levels
            let confidenceLevel = 'low'; // Default to 'low'
            let confidenceClass = 'bg-red-500/20 text-red-300';
            if (record.confidence > 0.75) {
                confidenceLevel = 'high';
                confidenceClass = 'bg-green-500/20 text-green-300';
            } else if (record.confidence > 0.5) {
                confidenceLevel = 'medium';
                confidenceClass = 'bg-yellow-500/20 text-yellow-300';
            }

            // Add row content
            row.innerHTML = `
                <td>${record.detection_id || 'N/A'}</td>
                <td>${record.date || 'N/A'}</td>
                <td>${record.time || 'N/A'}</td>
                <td>
                    <span class="inline-block px-2 py-1 rounded-full text-xs ${confidenceClass}">
                        ${confidenceLevel.charAt(0).toUpperCase() + confidenceLevel.slice(1)}
                    </span>
                </td>
                <td>${record.type_of_detection || 'Unknown'}</td>
                <td>${record.status || 'Unknown'}</td>
            `;

            // Add data attributes for filtering
            row.setAttribute('data-confidence-value', record.confidence); // Store numeric confidence value
            row.setAttribute('data-confidence', confidenceLevel); // Store confidence level for easier filtering

            tableBody.appendChild(row);
        });

        // Initialize the search functionality after populating the table
        const tableSearch = document.getElementById('tableSearch');
        if (tableSearch) {
            tableSearch.addEventListener('input', function () {
                const searchTerm = this.value.toLowerCase();
                const rows = tableBody.querySelectorAll('tr');

                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        }
    }
    
    // Filter pills functionality
    const pills = document.querySelectorAll('.pill');
    
    pills.forEach(pill => {
        pill.addEventListener('click', function() {
            pills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            
            // In a real app, this would filter the data
            window.showNotification(`Filter applied: ${this.textContent}`, 'info');
        });
    });

    // Initialize the chart with statistics data
    updateChartFromStatistics();
});



document.addEventListener('DOMContentLoaded', function () {
    const chartCanvas = document.getElementById('detectionChart');
    if (chartCanvas) {
        const labels = graphData.labels; // X-axis labels (dates)
        const datasets = [
            {
                label: 'Package Deliveries',
                data: graphData.datasets.deliveries,
                borderColor: 'rgba(96, 165, 250, 1)', // Line color for deliveries
                backgroundColor: 'rgba(96, 165, 250, 0.2)', // Fill under the line
                borderWidth: 2,
                tension: 0.4, // Smooth curves
                fill: true // Fill the area under the line
            },
            {
                label: 'Theft Detections',
                data: graphData.datasets.thefts,
                borderColor: 'rgba(248, 113, 113, 1)', // Line color for thefts
                backgroundColor: 'rgba(248, 113, 113, 0.2)', // Fill under the line
                borderWidth: 2,
                tension: 0.4, // Smooth curves
                fill: true // Fill the area under the line
            },
            {
                label: 'High Confidence',
                data: graphData.datasets.highConfidence,
                borderColor: 'rgba(34, 197, 94, 1)', // Line color for high confidence
                backgroundColor: 'rgba(34, 197, 94, 0.2)', // Fill under the line
                borderWidth: 2,
                tension: 0.4,
                fill: true
            },
            {
                label: 'Medium Confidence',
                data: graphData.datasets.mediumConfidence,
                borderColor: 'rgba(234, 179, 8, 1)', // Line color for medium confidence
                backgroundColor: 'rgba(234, 179, 8, 0.2)', // Fill under the line
                borderWidth: 2,
                tension: 0.4,
                fill: true
            },
            {
                label: 'Low Confidence',
                data: graphData.datasets.lowConfidence,
                borderColor: 'rgba(239, 68, 68, 1)', // Line color for low confidence
                backgroundColor: 'rgba(239, 68, 68, 0.2)', // Fill under the line
                borderWidth: 2,
                tension: 0.4,
                fill: true
            },
            {
                label: 'No Package Theft',
                data: graphData.datasets.noTheftRecords,
                borderColor: 'rgba(156, 163, 175, 1)', // Line color for package theft
                backgroundColor: 'rgba(156, 163, 175, 0.2)', // Fill under the line
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }
        ];

        // Initialize the chart
        new Chart(chartCanvas, {
            type: 'line', // Line chart for trends
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    }
});

function filterRecords(filter) {
    const rows = document.querySelectorAll('#detectionTableBody tr');
    const filteredGraphData = { high: 0, medium: 0, low: 0 }; // To store counts for the graph

    rows.forEach(row => {
        const confidenceLevel = row.getAttribute('data-confidence'); // Get confidence level from data attribute
        const verificationCell = row.querySelector('td:nth-child(7)').textContent.trim().toLowerCase(); // verification status cell cloumn

        // Show all rows if the filter is 'all'
        if (filter === 'all') {
            row.style.display = '';
            if (confidenceLevel) filteredGraphData[confidenceLevel]++;
            return;
        }

        // Filter by package theft
        if (filter === 'package-theft' && verificationCell === 'theft') {
            if (confidenceLevel) filteredGraphData[confidenceLevel]++;
            row.style.display = '';
        } else if (filter === 'no-package-theft' && verificationCell === 'safe') {
            if (confidenceLevel) filteredGraphData[confidenceLevel]++;
            row.style.display = '';
        }
        // Filter by confidence levels
        else if (filter === 'high-confidence' && confidenceLevel === 'high') {
            filteredGraphData.high++;
            row.style.display = '';
        } else if (filter === 'medium-confidence' && confidenceLevel === 'medium') {
            filteredGraphData.medium++;
            row.style.display = '';
        } else if (filter === 'low-confidence' && confidenceLevel === 'low') {
            filteredGraphData.low++;
            row.style.display = '';
        } else {
            // Hide rows that don't match the filter
            row.style.display = 'none';
        }
    });

    // Update the graph with the filtered data
    updateChartFromFilter(filteredGraphData);

    // Update active pill styling
    const pills = document.querySelectorAll('.pill');
    pills.forEach(pill => pill.classList.remove('active'));
    document.querySelector(`.pill[onclick="filterRecords('${filter}')"]`).classList.add('active');
}

function updateChart(filteredGraphData) {
    const labels = filteredGraphData.map(data => data.date); // X-axis labels (dates)
    const packageData = filteredGraphData.map(data => data.deliveries); // Y-axis data for deliveries
    const theftData = filteredGraphData.map(data => data.thefts); // Y-axis data for thefts

    // Update the chart data
    chart.data.labels = labels;
    chart.data.datasets[0].data = packageData; // Update deliveries dataset
    chart.data.datasets[1].data = theftData; // Update thefts dataset

    // Refresh the chart
    chart.update();
}

function updateChartFromStatistics() {
    const labels = ['High Confidence', 'Medium Confidence', 'Low Confidence']; // X-axis labels
    const confidenceData = [
        statisticsData.highConfidence,
        statisticsData.mediumConfidence,
        statisticsData.lowConfidence
    ]; // Y-axis data for confidence levels

    // Update the chart data
    chart.data.labels = labels;
    chart.data.datasets[0].data = confidenceData; // Update the dataset with confidence data

    // Refresh the chart
    chart.update();
}

function updateChartFromFilter(filteredGraphData) {
    const labels = ['High Confidence', 'Medium Confidence', 'Low Confidence']; // X-axis labels
    const confidenceData = [
        filteredGraphData.high || 0,
        filteredGraphData.medium || 0,
        filteredGraphData.low || 0
    ]; // Y-axis data for confidence levels

    // Update the chart data
    chart.data.labels = labels;
    chart.data.datasets[0].data = confidenceData; // Update the dataset with filtered confidence data

    // Refresh the chart
    chart.update();
}

function aggregateGraphData(filteredGraphData) {
    const aggregatedData = {
        labels: [], // Dates for the X-axis
        highConfidence: [],
        mediumConfidence: [],
        lowConfidence: []
    };

    // Group data by date
    const groupedData = {};
    filteredGraphData.forEach(data => {
        if (!groupedData[data.date]) {
            groupedData[data.date] = {
                highConfidence: 0,
                mediumConfidence: 0,
                lowConfidence: 0
            };
        }

        // Classify confidence levels dynamically
        if (data.confidence > 0.75) {
            groupedData[data.date].highConfidence += 1;
        } else if (data.confidence > 0.5) {
            groupedData[data.date].mediumConfidence += 1;
        } else {
            groupedData[data.date].lowConfidence += 1;
        }
    });

    // Populate aggregated data
    for (const date in groupedData) {
        aggregatedData.labels.push(date);
        aggregatedData.highConfidence.push(groupedData[date].highConfidence);
        aggregatedData.mediumConfidence.push(groupedData[date].mediumConfidence);
        aggregatedData.lowConfidence.push(groupedData[date].lowConfidence);
    }

    return aggregatedData;
}

document.addEventListener('DOMContentLoaded', function () {
    const tableSearch = document.getElementById('tableSearch');
    const tableBody = document.getElementById('detectionTableBody');

    if (tableSearch && tableBody) {
        tableSearch.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            const rows = tableBody.querySelectorAll('tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});

let sortAscending = true; // Flag to toggle sorting order

function sortTableById() {
    const tableBody = document.getElementById('detectionTableBody');
    const rows = Array.from(tableBody.querySelectorAll('tr')); // Get all rows as an array

    // Sort rows based on the Detection ID column
    rows.sort((a, b) => {
        const idA = a.querySelector('td:nth-child(1)').textContent.trim(); // Detection ID in first column
        const idB = b.querySelector('td:nth-child(1)').textContent.trim();

        // Compare IDs as strings for sorting
        if (sortAscending) {
            return idA.localeCompare(idB, undefined, { numeric: true });
        } else {
            return idB.localeCompare(idA, undefined, { numeric: true });
        }
    });

    // Toggle the sorting order for the next click
    sortAscending = !sortAscending;

    // Update the sort icon
    const sortIcon = document.getElementById('sortIcon');
    sortIcon.textContent = sortAscending ? '▲' : '▼';

    // Append sorted rows back to the table body
    rows.forEach(row => tableBody.appendChild(row));
}

let sortDateAscending = true; // Flag to toggle sorting order
function sortTableByDate() {
    const tableBody = document.getElementById('detectionTableBody');
    const rows = Array.from(tableBody.querySelectorAll('tr')); // Get all rows as an array

    // Sort rows based on the Date column
    rows.sort((a, b) => {
        const dateA = new Date(a.querySelector('td:nth-child(2)').textContent.trim()); // Date in second column
        const dateB = new Date(b.querySelector('td:nth-child(2)').textContent.trim());

        // Compare dates for sorting
        if (sortDateAscending) {
            return dateA - dateB; // Ascending order
        } else {
            return dateB - dateA; // Descending order
        }
    });

    // Toggle the sorting order for the next click
    sortDateAscending = !sortDateAscending;

    // Update the sort icon
    const sortIconDate = document.getElementById('sortIconDate');
    sortIconDate.textContent = sortDateAscending ? '▲' : '▼';

    // Append sorted rows back to the table body
    rows.forEach(row => tableBody.appendChild(row));
}