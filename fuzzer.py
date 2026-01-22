import requests
import time
from datetime import datetime

ENDPOINTS = {
    "login": {
        "url": "http://localhost:3000/api/auth/login",
        "fields": ["email", "password"]
    },
    "register": {
        "url": "http://localhost:3000/api/auth/register", 
        "fields": ["email", "password", "name"]
    }
}

def setup_logging():
    """Create log file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fuzz_results_{timestamp}.txt"
    return open(filename, "w")

def fuzzer():
    with open("payloads.txt", "r") as f:
        payloads = [line.strip() for line in f]
    
    # Setup log file
    log_file = setup_logging()
    log_file.write(f"Fuzzing started at {datetime.now()}\n")
    log_file.write(f"Loaded {len(payloads)} payloads\n")
    log_file.write("="*50 + "\n")
    
    print(f"[*] Loaded {len(payloads)} payloads")
    print(f"[*] Logging to: {log_file.name}")
    
    for endpoint_name, endpoint_info in ENDPOINTS.items():
        url = endpoint_info["url"]
        fields = endpoint_info["fields"]
        
        print(f"\n[*] Testing: {endpoint_name} ({url})")
        log_file.write(f"\nTesting: {endpoint_name} ({url})\n")
        
        for field in fields:
            print(f"  -> Fuzzing field: {field}")
            log_file.write(f"  Fuzzing field: {field}\n")
            
            for payload in payloads:
                try:
                    # Build data
                    data = {}
                    for fld in fields:
                        if fld == field:
                            data[fld] = payload
                        else:
                            if fld == "email":
                                data[fld] = "test@test.com"
                            elif fld == "password":
                                data[fld] = "TestPass123"
                            elif fld == "name":
                                data[fld] = "Test User"
                    
                    response = requests.post(url, json=data, timeout=3)
                    
                    # Check for interesting responses
                    if response.status_code >= 500:
                        log_entry = f"[!] {datetime.now()} - 500 Error in {endpoint_name}.{field}\n"
                        log_entry += f"    Payload: {payload}\n"
                        log_entry += f"    Response: {response.text[:200]}\n"
                        log_file.write(log_entry + "\n")
                        print(f"[!] 500 Error in {endpoint_name}.{field}")
                        
                    elif "error" in response.text.lower():
                        if "sql" in response.text.lower() or "syntax" in response.text.lower():
                            log_entry = f"[!] {datetime.now()} - SQL Error in {endpoint_name}.{field}\n"
                            log_entry += f"    Payload: {payload}\n"
                            log_entry += f"    Response: {response.text[:200]}\n"
                            log_file.write(log_entry + "\n")
                            print(f"[!] SQL Error in {endpoint_name}.{field}")
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    log_entry = f"[!] {datetime.now()} - Crash in {endpoint_name}.{field}\n"
                    log_entry += f"    Payload: {payload}\n"
                    log_entry += f"    Error: {str(e)}\n"
                    log_file.write(log_entry + "\n")
                    print(f"[!] Crash with {payload} in {field}")
    
    log_file.write(f"\nFuzzing completed at {datetime.now()}\n")
    log_file.close()
    print(f"\n[*] Fuzzing complete! Results saved to: {log_file.name}")

if __name__ == "__main__":
    fuzzer()