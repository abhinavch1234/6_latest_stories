import json
import http.server
import urllib.request
import socketserver

def fetch_time_html():
    url = "https://time.com"
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching HTML: {e}")
        return ""

def parse_stories(html_content):
    stories = []
    
    start_anchor = '<ul class="grid grid-cols-4 lg:grid-cols-12 my-10 gap-x-4">'
    start_index = html_content.find(start_anchor)
    
    if start_index == -1:
        print("Error: Could not find the story list anchor in the HTML.")
        return []
    
    search_area = html_content[start_index:]
    
    story_start_marker = '<li class="col-span-full inline-grid size-full lg:col-span-3">'
    
    for _ in range(6):
        
        story_start = search_area.find(story_start_marker)
        if story_start == -1:
            break
        
        search_area = search_area[story_start:]
        
        story_end = search_area.find('</li>')
        if story_end == -1:
            break
            
        story_html = search_area[:story_end]
        
        link_tag = 'href="'
        
        link_start_index_1 = story_html.find(link_tag)
        if link_start_index_1 == -1: continue
        
        link_start_index_2 = story_html.find(link_tag, link_start_index_1 + len(link_tag))
        if link_start_index_2 == -1: continue

        link_start_pos = link_start_index_2 + len(link_tag)
        link_end_index = story_html.find('"', link_start_pos)
        
        full_link = story_html[link_start_pos:link_end_index]
        
        title_tag_start = '<span>'
        title_start_index = story_html.find(title_tag_start, link_end_index)
        if title_start_index == -1: continue
            
        title_start_pos = title_start_index + len(title_tag_start)
        title_end_index = story_html.find('</span>', title_start_pos)
        if title_end_index == -1: continue
            
        title = story_html[title_start_pos:title_end_index]
        
        stories.append({"title": title, "link": full_link})
        
        search_area = search_area[story_end:]

    return stories

class MyAPIHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        
        if self.path == '/getTimeStories':
            try:
                print("Request received... fetching live data from Time.com...")
                html = fetch_time_html()
                
                if not html:
                    raise Exception("Failed to fetch HTML from Time.com")
                
                stories = parse_stories(html)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response_json = json.dumps(stories, separators=(',', ':'))
                self.wfile.write(response_json.encode('utf-8'))
                print(f"Success! Sent {len(stories)} stories.")
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found. Please use the /getTimeStories endpoint.")

if __name__ == "__main__":
    PORT = 8000
    
    with socketserver.TCPServer(("", PORT), MyAPIHandler) as httpd:
        print(f"Server started successfully!")
        print(f"Your API is running. Open this URL in your browser:")
        print(f"  http://localhost:{PORT}/getTimeStories")
        print("\nPress Ctrl+C to stop the server.")
        
        httpd.serve_forever()