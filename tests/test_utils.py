import pytest
from utils import _check_missing_tags # Assuming utils.py is in the root

# Test cases for _check_missing_tags
# Parameters: (resource_tags_list, required_tags_set, expected_missing_list)
check_tags_test_cases = [
    # Case 1: All required tags present
    ([{'Key': 'Project', 'Value': 'A'}, {'Key': 'Owner', 'Value': 'B'}], {'Project', 'Owner'}, []),
    # Case 2: One required tag missing
    ([{'Key': 'Project', 'Value': 'A'}], {'Project', 'Owner'}, ['Owner']),
    # Case 3: Other tags present, one required missing
    ([{'Key': 'Project', 'Value': 'A'}, {'Key': 'Name', 'Value': 'Test'}], {'Project', 'Owner'}, ['Owner']),
    # Case 4: All required tags missing (other tags present)
    ([{'Key': 'Name', 'Value': 'Test'}], {'Project', 'Owner'}, ['Project', 'Owner']),
    # Case 5: Resource has no tags at all
    ([], {'Project', 'Owner'}, ['Project', 'Owner']),
    # Case 6: Resource tags list is None
    (None, {'Project', 'Owner'}, ['Project', 'Owner']),
    # Case 7: Required tags set is empty
    ([{'Key': 'Project', 'Value': 'A'}], set(), []),
    # Case 8: Both resource tags and required tags are empty
    ([], set(), []),
    # Case 9: Case sensitivity check (should be case-sensitive)
    ([{'Key': 'project', 'Value': 'A'}], {'Project', 'Owner'}, ['Project', 'Owner']),
]

@pytest.mark.parametrize("resource_tags, required_tags, expected_missing", check_tags_test_cases)
def test_check_missing_tags(resource_tags, required_tags, expected_missing):
    """Tests the _check_missing_tags helper function with various inputs."""
    missing = _check_missing_tags(resource_tags, required_tags)
    # Sort lists before comparing to handle potential order differences
    assert sorted(missing) == sorted(expected_missing)