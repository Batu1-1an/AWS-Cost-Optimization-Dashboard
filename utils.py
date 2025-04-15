# utils.py
# Utility functions

def _check_missing_tags(resource_tags_list, required_tags_set):
    """Helper function to find missing tags from a list of tag dictionaries."""
    if not resource_tags_list: # Handle case where 'Tags' key might be missing entirely
        return list(required_tags_set) # All required tags are missing

    # Convert [{'Key': k, 'Value': v}, ...] to a set of keys {'k', ...}
    present_tags_set = {tag['Key'] for tag in resource_tags_list}
    missing = list(required_tags_set - present_tags_set)
    return missing