import os
import sys
import json
import urllib.request
import urllib.error

def main():
    # 1. Read and sanitize the base URL
    base_url = os.environ.get("AGENTSWARM_BASE_URL", "https://agentswarm.space").rstrip("/")
    api_url = f"{base_url}/api/bounties"

    try:
        # 2. Perform the HTTP GET request
        # No API key required as per instructions
        with urllib.request.urlopen(api_url) as response:
            if response.status != 200:
                print(f"Error: Received HTTP {response.status}", file=sys.stderr)
                sys.exit(1)
            
            raw_data = response.read().decode('utf-8')
            
            # 3. Parse JSON
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError as e:
                print(f"JSON Error: {str(e)}", file=sys.stderr)
                sys.exit(1)

            # 4. Process and Print Bounties
            bounties = data.get("bounties", [])
            if not isinstance(bounties, list):
                # Handle unexpected JSON structure
                sys.exit(1)

            for item in bounties:
                if item.get("status") == "open":
                    b_id = item.get("id")
                    title = item.get("title")
                    # Preserve reward string verbatim
                    reward = item.get("bounty", {}).get("reward", "")
                    
                    # Format: <id>\t<title>\t<bounty.reward>\t<base>/p/<id>
                    # Using literal tabs as requested
                    output = f"{b_id}\t{title}\t{reward}\t{base_url}/p/{b_id}"
                    print(output)

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch-all for other potential issues (e.g. encoding)
        print(f"Unexpected Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
