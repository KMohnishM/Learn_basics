from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SimpleAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "success",
            "message": "Hello from the Dockerized Python API!"
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleAPI)
    print("Starting API server on port 8000...")
    httpd.serve_forever()
