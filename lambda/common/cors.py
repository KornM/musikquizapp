"""
CORS utility module for adding Cross-Origin Resource Sharing headers to Lambda responses.
"""


def add_cors_headers(response):
    """
    Add CORS headers to a Lambda response.
    
    This function adds the necessary CORS headers to enable cross-origin requests
    from the CloudFront-hosted frontend.
    
    Args:
        response (dict): Lambda response dictionary with statusCode and body
        
    Returns:
        dict: Response dictionary with CORS headers added
    """
    if 'headers' not in response:
        response['headers'] = {}
    
    response['headers'].update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    })
    
    return response
