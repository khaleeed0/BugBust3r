#!/usr/bin/env python3
"""
Simple HTTP server for testing ZAP scans on localhost
Run this script and then test ZAP with: http://localhost:5000
"""
import http.server
import socketserver
import sys

PORT = 5000

class TestHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for testing"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Server for ZAP Scanning</title>
        </head>
        <body>
            <h1>Test Server for ZAP Scanning</h1>
            <p>This is a test server running on port 5000.</p>
            <p>If you can see this, the server is working correctly.</p>
            <h2>Test Forms (for ZAP to scan):</h2>
            <form method="POST" action="/submit">
                <label>Username:</label>
                <input type="text" name="username" />
                <br><br>
                <label>Password:</label>
                <input type="password" name="password" />
                <br><br>
                <input type="submit" value="Submit" />
            </form>
            <h2>Test Links:</h2>
            <a href="/page1">Page 1</a> | 
            <a href="/page2">Page 2</a> | 
            <a href="/admin">Admin Page</a>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Form Submitted</title>
        </head>
        <body>
            <h1>Form Submitted</h1>
            <p>Data received: {post_data.decode()}</p>
            <a href="/">Back to home</a>
        </body>
        </html>
        """
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{self.address_string()}] {format % args}")

def main():
    """Start the test server"""
    try:
        with socketserver.TCPServer(("", PORT), TestHTTPRequestHandler) as httpd:
            print(f"=" * 60)
            print(f"Test HTTP Server for ZAP Scanning")
            print(f"=" * 60)
            print(f"Server running on http://localhost:{PORT}")
            print(f"Press Ctrl+C to stop the server")
            print(f"=" * 60)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Error: Port {PORT} is already in use.")
            print("Please stop the service using that port or use a different port.")
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

