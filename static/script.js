document.addEventListener('DOMContentLoaded', function() {
    fetchCostData();
    fetchIdleInstances();
    fetchUntaggedResources();
    fetchEbsOptimizationData();
    fetchCostAnomalyData(); // Add call for cost anomaly data
    fetchS3OptimizationData(); // Add call for S3 optimization data
});

function fetchCostData() {
    fetch('/api/cost-by-service')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderCostChart(data);
        })
        .catch(error => {
            console.error('Error fetching cost data:', error);
            const chartDiv = document.getElementById('costChart');
            chartDiv.innerHTML = '<p style="color: red;">Could not load cost data.</p>';
        });
}

function renderCostChart(data) {
    const labels = Object.keys(data);
    const values = Object.values(data);

    const plotData = [{
        values: values,
        labels: labels,
        type: 'pie',
        hole: .4, // Optional: makes it a donut chart
        textinfo: "label+percent",
        insidetextorientation: "radial"
    }];

    const layout = {
        title: 'Cost Breakdown by Service',
        height: 400,
        width: 500,
        showlegend: true
        // Add more layout options as needed
    };

    Plotly.newPlot('costChart', plotData, layout);
}

function fetchIdleInstances() {
    fetch('/api/idle-instances')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderIdleInstancesTable(data);
        })
        .catch(error => {
            console.error('Error fetching idle instances:', error);
            const tableBody = document.getElementById('idleInstancesTable').querySelector('tbody');
            tableBody.innerHTML = '<tr><td colspan="4" style="color: red;">Could not load idle instance data.</td></tr>';
        });
}

function renderIdleInstancesTable(data) {
    const tableBody = document.getElementById('idleInstancesTable').querySelector('tbody');
    tableBody.innerHTML = ''; // Clear previous data

    if (data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4">No potentially idle instances found.</td></tr>';
        return;
    }

    data.forEach(instance => {
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = instance.InstanceId;
        row.insertCell(1).textContent = instance.Region;
        row.insertCell(2).textContent = instance.AvgCPU.toFixed(2); // Format CPU usage
        row.insertCell(3).textContent = instance.Reason;
    });
}

function fetchUntaggedResources() {
    fetch('/api/untagged-resources')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderUntaggedResourcesTable(data);
        })
        .catch(error => {
            console.error('Error fetching untagged resources:', error);
            const tableBody = document.getElementById('untaggedResourcesTable').querySelector('tbody');
            tableBody.innerHTML = '<tr><td colspan="4" style="color: red;">Could not load untagged resource data.</td></tr>';
        });
}

function renderUntaggedResourcesTable(data) {
    const tableBody = document.getElementById('untaggedResourcesTable').querySelector('tbody');
    tableBody.innerHTML = ''; // Clear previous data

    const instances = data.Instances || [];
    const volumes = data.Volumes || [];

    if (instances.length === 0 && volumes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4">No untagged instances or volumes found (based on required tags).</td></tr>';
        return;
    }

    // Combine instances and volumes for easier iteration
    const allUntagged = [...instances, ...volumes];

    allUntagged.forEach(resource => {
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = resource.ResourceId;
        row.insertCell(1).textContent = resource.ResourceType;
        row.insertCell(2).textContent = resource.Region;
        // Join the list of missing tags into a string
        row.insertCell(3).textContent = resource.MissingTags.join(', ');
    });
}

function fetchEbsOptimizationData() {
    fetch('/api/ebs-optimization')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderEbsOptimizationTable(data);
        })
        .catch(error => {
            console.error('Error fetching EBS optimization data:', error);
            const tableBody = document.getElementById('ebsOptimizationTable').querySelector('tbody');
            tableBody.innerHTML = '<tr><td colspan="5" style="color: red;">Could not load EBS optimization data.</td></tr>';
        });
}

function renderEbsOptimizationTable(data) {
    const tableBody = document.getElementById('ebsOptimizationTable').querySelector('tbody');
    tableBody.innerHTML = ''; // Clear previous data

    const unattached = data.UnattachedVolumes || [];
    const gp2Volumes = data.Gp2Volumes || [];

    if (unattached.length === 0 && gp2Volumes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No EBS optimization candidates found.</td></tr>';
        return;
    }

    // Combine both types of candidates for rendering
    const allCandidates = [...unattached, ...gp2Volumes];

    allCandidates.forEach(volume => {
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = volume.ResourceId;
        row.insertCell(1).textContent = volume.Region;
        row.insertCell(2).textContent = volume.SizeGiB;
        row.insertCell(3).textContent = volume.CurrentType || 'N/A'; // Display type if available (gp2)
        row.insertCell(4).textContent = volume.Reason;
    });
}

function fetchCostAnomalyData() {
    fetch('/api/cost-anomalies')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderCostAnomalyInfo(data);
        })
        .catch(error => {
            console.error('Error fetching cost anomaly data:', error);
            const infoDiv = document.getElementById('costAnomalyInfo');
            infoDiv.innerHTML = '<p style="color: red;">Could not load cost anomaly data.</p>';
        });
}

function renderCostAnomalyInfo(data) {
    const infoDiv = document.getElementById('costAnomalyInfo');
    infoDiv.innerHTML = ''; // Clear previous data

    if (!data) {
        infoDiv.innerHTML = '<p>Could not retrieve anomaly data.</p>';
        return;
    }

    const isAnomaly = data.is_anomaly;
    const anomalyClass = isAnomaly ? 'anomaly-detected' : 'no-anomaly';
    const anomalyText = isAnomaly ? 'Anomaly Detected!' : 'No Anomaly Detected';

    // Add specific class for styling
    infoDiv.classList.add(anomalyClass);

    // Create elements to display the info
    const statusP = document.createElement('p');
    statusP.innerHTML = `<strong>Status:</strong> ${anomalyText}`;
    infoDiv.appendChild(statusP);

    const latestP = document.createElement('p');
    latestP.innerHTML = `<strong>Latest Cost (${data.latest_date}):</strong> $${data.latest_cost.toFixed(2)}`;
    infoDiv.appendChild(latestP);

    const avgP = document.createElement('p');
    avgP.innerHTML = `<strong>Avg. Cost (prev. ${data.history_days - 1} days):</strong> $${data.average_cost.toFixed(2)}`;
    infoDiv.appendChild(avgP);

    const thresholdP = document.createElement('p');
    thresholdP.innerHTML = `<strong>Anomaly Threshold:</strong> $${data.threshold.toFixed(2)} (Avg + ${data.std_dev_threshold} * StdDev)`;
    infoDiv.appendChild(thresholdP);

    if (isAnomaly) {
        const explanationP = document.createElement('p');
        explanationP.textContent = `The latest cost is significantly higher than the recent average based on the defined threshold.`;
        infoDiv.appendChild(explanationP);
    }
}

function fetchS3OptimizationData() {
    fetch('/api/s3-optimization')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderS3OptimizationData(data);
        })
        .catch(error => {
            console.error('Error fetching S3 optimization data:', error);
            const summaryDiv = document.getElementById('s3SummaryInfo');
            summaryDiv.innerHTML = '<p style="color: red;">Could not load S3 optimization data.</p>';
        });
}

function renderS3OptimizationData(data) {
    renderS3Summary(data);
    renderS3StorageClassChart(data);
    renderS3SavingsChart(data);
    renderS3RecommendationsTable(data);
}

function renderS3Summary(data) {
    const summaryDiv = document.getElementById('s3SummaryInfo');
    const summary = data.summary;
    const costAnalysis = data.cost_analysis;
    
    summaryDiv.innerHTML = `
        <h3>S3 Storage Analysis Summary</h3>
        <div class="s3-stats">
            <div class="s3-stat-item">
                <span class="s3-stat-number">${summary.total_buckets}</span>
                <span class="s3-stat-label">Total Buckets</span>
            </div>
            <div class="s3-stat-item">
                <span class="s3-stat-number">${summary.total_size_gb.toFixed(1)}</span>
                <span class="s3-stat-label">Total Size (GB)</span>
            </div>
            <div class="s3-stat-item">
                <span class="s3-stat-number">${summary.optimization_opportunities_count}</span>
                <span class="s3-stat-label">Opportunities</span>
            </div>
            <div class="s3-stat-item">
                <span class="s3-stat-number">${summary.buckets_analyzed}</span>
                <span class="s3-stat-label">Analyzed Buckets</span>
            </div>
        </div>
        <div class="savings-highlight">
            <div>Potential Monthly Savings: <span class="amount">$${costAnalysis.total_monthly_savings_usd}</span></div>
            <div>Potential Annual Savings: <span class="amount">$${costAnalysis.annual_savings_usd}</span></div>
        </div>
    `;
}

function renderS3StorageClassChart(data) {
    // Aggregate storage class data across all buckets
    const storageClassAgg = {};
    
    data.buckets.forEach(bucket => {
        Object.entries(bucket.storage_classes).forEach(([storageClass, count]) => {
            storageClassAgg[storageClass] = (storageClassAgg[storageClass] || 0) + count;
        });
    });
    
    const labels = Object.keys(storageClassAgg);
    const values = Object.values(storageClassAgg);
    
    if (labels.length === 0) {
        document.getElementById('s3StorageClassChart').innerHTML = '<p>No storage class data available.</p>';
        return;
    }
    
    const plotData = [{
        values: values,
        labels: labels,
        type: 'pie',
        hole: .3,
        textinfo: "label+percent",
        textposition: "inside"
    }];
    
    const layout = {
        title: {
            text: 'Storage Classes Across All Buckets',
            font: { size: 14 }
        },
        height: 250,
        margin: { t: 40, b: 10, l: 10, r: 10 },
        showlegend: true,
        legend: {
            orientation: "h",
            y: -0.1
        }
    };
    
    Plotly.newPlot('s3StorageClassChart', plotData, layout, {responsive: true});
}

function renderS3SavingsChart(data) {
    const savingsBreakdown = data.cost_analysis.savings_breakdown;
    
    const typeLabels = {
        'storage_class_optimization': 'Storage Class Optimization',
        'deprecated_storage_class': 'Deprecated Storage Classes',
        'missing_lifecycle_policy': 'Missing Lifecycle Policies'
    };
    
    const labels = Object.keys(savingsBreakdown).map(key => typeLabels[key] || key);
    const values = Object.values(savingsBreakdown).map(item => item.potential_savings);
    
    if (labels.length === 0) {
        document.getElementById('s3SavingsChart').innerHTML = '<p>No savings opportunities identified.</p>';
        return;
    }
    
    const plotData = [{
        x: labels,
        y: values,
        type: 'bar',
        marker: {
            color: ['#007bff', '#dc3545', '#ffc107']
        }
    }];
    
    const layout = {
        title: {
            text: 'Potential Monthly Savings by Type',
            font: { size: 14 }
        },
        height: 250,
        margin: { t: 40, b: 60, l: 40, r: 20 },
        xaxis: {
            title: 'Optimization Type'
        },
        yaxis: {
            title: 'Potential Savings ($)'
        }
    };
    
    Plotly.newPlot('s3SavingsChart', plotData, layout, {responsive: true});
}

function renderS3RecommendationsTable(data) {
    const tableBody = document.querySelector('#s3RecommendationsTable tbody');
    const recommendations = data.priority_recommendations;
    
    // Clear existing data
    tableBody.innerHTML = '';
    
    if (!recommendations || recommendations.length === 0) {
        const row = tableBody.insertRow();
        const cell = row.insertCell(0);
        cell.colSpan = 6;
        cell.textContent = 'No optimization recommendations available.';
        cell.style.textAlign = 'center';
        cell.style.fontStyle = 'italic';
        return;
    }
    
    recommendations.forEach(rec => {
        const row = tableBody.insertRow();
        
        // Priority column with badge
        const priorityCell = row.insertCell(0);
        const priorityBadge = document.createElement('span');
        priorityBadge.className = `priority-badge priority-${rec.priority_level.toLowerCase()}`;
        priorityBadge.textContent = rec.priority_level;
        priorityCell.appendChild(priorityBadge);
        
        // Bucket name
        row.insertCell(1).textContent = rec.bucket_name;
        
        // Size (GB)
        row.insertCell(2).textContent = rec.bucket_size_gb.toFixed(2);
        
        // Optimization type
        const typeCell = row.insertCell(3);
        const typeFormatted = rec.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        typeCell.textContent = typeFormatted;
        
        // Potential savings
        row.insertCell(4).textContent = `${rec.potential_savings_percent}%`;
        
        // Recommended action
        row.insertCell(5).textContent = rec.recommended_action;
    });
}