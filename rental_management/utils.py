"""
Utility functions for Django Unfold configuration
"""

def environment_callback(request):
    """
    Callback to show environment information in the admin
    """
    return ["Development", "success"]  # [label, color]


def dashboard_callback(request, context):
    """
    Callback to customize the admin dashboard
    """
    return [
        {
            "title": "Quick Stats",
            "metric": "Properties",
            "value": "0",
            "chart": [],
        },
        {
            "title": "Recent Activity",
            "metric": "Payments",
            "value": "0",
            "chart": [],
        },
    ]