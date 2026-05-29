from urllib.parse import parse_qs

def wsgi_app(environ, start_response):
    query_string = environ.get('QUERY_STRING', '')
    get_params = parse_qs(query_string)

    post_params = {}
    if environ.get('REQUEST_METHOD') == 'POST':
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        if content_length > 0:
            body = environ['wsgi.input'].read(content_length).decode('utf-8')
            post_params = parse_qs(body)

    response_text = (
        f"Method: {environ.get('REQUEST_METHOD', 'UNKNOWN')}\n"
        f"GET Parameters: {dict(get_params)}\n"
        f"POST Parameters: {dict(post_params)}\n"
    )

    status = '200 OK'
    headers = [('Content-Type', 'text/plain; charset=utf-8')]
    start_response(status, headers)

    return [response_text.encode('utf-8')]
