document.addEventListener('DOMContentLoaded', function() {
    fetchCostData();
    fetchIdleInstances();
    fetchUntaggedResources(); // Add call for untagged resources
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