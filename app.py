import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from analyzer import (
    analyze_cost_data, analyze_idle_instances, analyze_untagged_resources,
    analyze_ebs_optimization, analyze_cost_anomalies # Import new analyzer functions
)
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Removed dummy data definitions

@app.route('/')
def index():
    """Renders the main dashboard page."""
    # In the future, fetch real data here
    return render_template('index.html', title='AWS Cost Dashboard')

@app.route('/api/cost-by-service')
def get_cost_by_service():
    """API endpoint to provide cost data per service."""
    cost_data = analyze_cost_data()
    if cost_data is None:
        return jsonify({"error": "Failed to retrieve cost data"}), 500
    return jsonify(cost_data)

@app.route('/api/idle-instances')
def get_idle_instances():
    """API endpoint to provide list of idle instances."""
    idle_instances = analyze_idle_instances()
    if idle_instances is None:
        return jsonify({"error": "Failed to retrieve idle instance data"}), 500
    return jsonify(idle_instances)

@app.route('/api/untagged-resources')
def get_untagged_resources_api():
    """API endpoint to provide list of untagged instances and volumes."""
    # Note: Add ability to pass required_tags and region from request if needed later
    untagged_data = analyze_untagged_resources()
    if untagged_data is None:
        return jsonify({"error": "Failed to retrieve untagged resource data"}), 500
    return jsonify(untagged_data)

@app.route('/api/ebs-optimization')
def get_ebs_optimization_api():
    """API endpoint to provide EBS optimization candidates."""
    # Note: Add ability to pass region from request if needed later
    ebs_opts_data = analyze_ebs_optimization()
    if ebs_opts_data is None:
        return jsonify({"error": "Failed to retrieve EBS optimization data"}), 500
    return jsonify(ebs_opts_data)

@app.route('/api/cost-anomalies')
def get_cost_anomalies_api():
    """API endpoint to provide cost anomaly detection results."""
    # Note: Add ability to pass history_days, std_dev_threshold from request if needed later
    anomaly_data = analyze_cost_anomalies()
    if anomaly_data is None:
        return jsonify({"error": "Failed to retrieve cost anomaly data"}), 500
    return jsonify(anomaly_data)

if __name__ == '__main__':
    # Use debug=True for development, but disable in production
    app.run(debug=True)