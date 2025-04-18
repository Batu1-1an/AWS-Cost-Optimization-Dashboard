document.addEventListener('DOMContentLoaded', function() {
    fetchCostData();
    fetchIdleInstances();
    fetchUntaggedResources();
    fetchEbsOptimizationData();
    fetchCostAnomalyData(); // Add call for cost anomaly data
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