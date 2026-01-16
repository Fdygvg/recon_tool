#!/usr/bin/env python3
"""
Combined Subdomain Enumerator & Port Scanner
Author: Your Name
"""

import sys
import os
import argparse
from datetime import datetime
import requests
import socket  
import concurrent.futures 
import json
import csv


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Basic reconnaissance tool')
    parser.add_argument('-d', '--domain', help='Target domain (e.g., example.com)')
    parser.add_argument('-t', '--target', help='Target IP or hostname for port scan')
    parser.add_argument('-o', '--output', help='Save results to file')
    parser.add_argument('--subdomains-only', action='store_true', help='Only run subdomain enumeration')
    parser.add_argument('--ports-only', action='store_true', help='Only run port scanning')
    parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json',
                    help='Output format (default: json)')
    parser.add_argument('-w', '--wordlist', help='Path to subdomain wordlist file')
    return parser.parse_args()


def enumerate_subdomains(domain, wordlist_file=None):
    """
    Discover subdomains using a wordlist or common patterns
    Returns: list of discovered subdomains
    """
    print(f"[*] Starting subdomain enumeration for: {domain}")
    
    wordlist = []
    
    # Auto-detect wordlist.txt if no file specified
    if not wordlist_file and os.path.exists('wordlist.txt'):
         wordlist_file = 'wordlist.txt'
         print(f"[*] Auto-detected local wordlist: {wordlist_file}")

    if wordlist_file:
        try:
            with open(wordlist_file, 'r', encoding='utf-8') as f:
                wordlist = [line.strip() for line in f if line.strip()]
            print(f"[*] Loaded {len(wordlist)} subdomains from: {wordlist_file}")
        except FileNotFoundError:
            print(f"[!] Wordlist file not found: {wordlist_file}")
            return []
    
    else:
        wordlist = ['mail', 'ftp', 'blog', 'api']
        print(f"[*] Using built-in list of {len(wordlist)} subdomains")
    
    discovered = []
    timeouts = []
    
    for sub in wordlist:
        subdomain = f"{sub}.{domain}"
        url = f"http://{subdomain}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                discovered.append(subdomain)
                print(f"[+] Found: {subdomain} (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            print(f"[-] Timeout: {subdomain}")
            timeouts.append(subdomain)
        except Exception as e:
            print(f"[!] Error checking {subdomain}: {e}")
    
    return discovered, timeouts




def scan_ports(target, ports=None, max_workers=50):
    """
    Scan for open ports on a target
    Returns: dict of port:service pairs
    """
    print(f"[*] Starting port scan for: {target}")
    
    # Default ports if none provided
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 3389, 8080]
    
    open_ports = {}
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3 second timeout per port
            
            result = sock.connect_ex((target, port))  # Returns 0 if success
            
            if result == 0:
                # Try to get service name
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                
                open_ports[port] = service
                print(f"[+] Port {port} open ({service})")
            
            sock.close()
            
        except socket.error as e:
            print(f"[!] Socket error on port {port}: {e}")
        except Exception as e:
            print(f"[!] General error on port {port}: {e}")
    
    return open_ports











import concurrent.futures  # Add this to imports at top

def run_recon(args):
    """
    Main function that runs subdomain and port scanning
    based on command-line arguments
    """
    results = {'subdomains': [], 'ports': {}}
    
    # Start timestamp
    start_time = datetime.now()
    print(f"[*] Recon started at {start_time.strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # SUBDOMAIN ENUMERATION
    if args.domain and not args.ports_only:
        print(f"\n[ PHASE 1 ] Subdomain Enumeration")
        print("-" * 30)
        
        discovered = enumerate_subdomains(args.domain, args.wordlist)
        results['subdomains'] = discovered
        
        if discovered:
            print(f"\n[*] Found {len(discovered)} subdomains:")
            for sub in discovered:
                print(f"    {sub}")
        else:
            print("[-] No subdomains found")
    
    # PORT SCANNING
    if args.target and not args.subdomains_only:
        print(f"\n\n[ PHASE 2 ] Port Scanning")
        print("-" * 30)
        
        # If we found subdomains, scan them too
        targets_to_scan = [args.target]
        if 'discovered' in locals() and discovered:
            targets_to_scan.extend(discovered)
        
        for target in targets_to_scan:
            print(f"\n[*] Scanning: {target}")
            open_ports = scan_ports_fast(target)  # Using faster version
            results['ports'][target] = open_ports
            
            if open_ports:
                print(f"    Open ports on {target}:")
                for port, service in open_ports.items():
                    print(f"      Port {port}: {service}")
            else:
                print(f"    No open ports found on {target}")
    
    # End timestamp
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"[*] Recon completed in {duration.total_seconds():.2f} seconds")
    print(f"[*] Started: {start_time.strftime('%H:%M:%S')}")
    print(f"[*] Ended:   {end_time.strftime('%H:%M:%S')}")
    
    return results

def scan_ports_fast(target, ports=None):
    """
    Faster port scanner using multiple threads
    """
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 3389, 8080]
    
    open_ports = {}
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target, port))
            sock.close()
            
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                return port, service
        except:
            pass
        return None
    
    # Use thread pool to scan multiple ports at once
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_port = {executor.submit(check_port, port): port for port in ports}
        
        for future in concurrent.futures.as_completed(future_to_port):
            result = future.result()
            if result:
                port, service = result
                open_ports[port] = service
    
    return open_ports





def run_recon(args):
    """
    Main function that runs subdomain and port scanning
    based on command-line arguments
    """
    results = {'subdomains': [], 'ports': {}}
    
    # Start timestamp
    start_time = datetime.now()
    print(f"[*] Recon started at {start_time.strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # SUBDOMAIN ENUMERATION
    if args.domain and not args.ports_only:
        print(f"\n[ PHASE 1 ] Subdomain Enumeration")
        print("-" * 30)
        
        discovered = enumerate_subdomains(args.domain)
        results['subdomains'] = discovered
        
        if discovered:
            print(f"\n[*] Found {len(discovered)} subdomains:")
            for sub in discovered:
                print(f"    {sub}")
        else:
            print("[-] No subdomains found")
    
    # PORT SCANNING
    if args.target and not args.subdomains_only:
        print(f"\n\n[ PHASE 2 ] Port Scanning")
        print("-" * 30)
        
        # If we found subdomains, scan them too
        targets_to_scan = [args.target]
        if 'discovered' in locals() and discovered:
            targets_to_scan.extend(discovered)
        
        for target in targets_to_scan:
            print(f"\n[*] Scanning: {target}")
            open_ports = scan_ports_fast(target)  # Using faster version
            results['ports'][target] = open_ports
            
            if open_ports:
                print(f"    Open ports on {target}:")
                for port, service in open_ports.items():
                    print(f"      Port {port}: {service}")
            else:
                print(f"    No open ports found on {target}")
    
    # End timestamp
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"[*] Recon completed in {duration.total_seconds():.2f} seconds")
    print(f"[*] Started: {start_time.strftime('%H:%M:%S')}")
    print(f"[*] Ended:   {end_time.strftime('%H:%M:%S')}")
    
    return results

def scan_ports_fast(target, ports=None):
    """
    Faster port scanner using multiple threads
    """
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 3389, 8080]
    
    open_ports = {}
    
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target, port))
            sock.close()
            
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                return port, service
        except:
            pass
        return None
    
    # Use thread pool to scan multiple ports at once
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_port = {executor.submit(check_port, port): port for port in ports}
        
        for future in concurrent.futures.as_completed(future_to_port):
            result = future.result()
            if result:
                port, service = result
                open_ports[port] = service
    
    return open_ports





def save_results(results, filename=None, format='json'):
    """
    Save scan results to file in various formats
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recon_results_{timestamp}"
    
    try:
        if format.lower() == 'json':
            filename = f"{filename}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"[*] Results saved to {filename} (JSON format)")
            
        elif format.lower() == 'csv':
            filename = f"{filename}.csv"
            save_csv(results, filename)
            print(f"[*] Results saved to {filename} (CSV format)")
            
        elif format.lower() == 'txt':
            filename = f"{filename}.txt"
            save_text(results, filename)
            print(f"[*] Results saved to {filename} (Text format)")
            
        else:
            print(f"[!] Unknown format: {format}. Using JSON.")
            save_results(results, filename, 'json')
            
        return filename
        
    except Exception as e:
        print(f"[!] Failed to save results: {e}")
        return None

def save_csv(results, filename):
    """Save results as CSV spreadsheet"""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write subdomains section
        writer.writerow(["SUBDOMAINS FOUND"])
        writer.writerow(["Domain", "URL"])
        
        for subdomain in results.get('subdomains', []):
            writer.writerow([subdomain, f"http://{subdomain}"])
        
        writer.writerow([])  # Empty row
        
        # Write ports section
        writer.writerow(["OPEN PORTS"])
        writer.writerow(["Target", "Port", "Service"])
        
        for target, ports in results.get('ports', {}).items():
            for port, service in ports.items():
                writer.writerow([target, port, service])
        
        # Summary row
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Subdomains found:", len(results.get('subdomains', []))])
        writer.writerow(["Targets scanned:", len(results.get('ports', {}))])

def save_text(results, filename):
    """Save results as readable text report"""
    with open(filename, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("RECONNAISSANCE REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        # Subdomains section
        f.write("SUBDOMAINS:\n")
        f.write("-" * 40 + "\n")
        if results.get('subdomains'):
            for i, subdomain in enumerate(results['subdomains'], 1):
                f.write(f"{i:3}. {subdomain}\n")
        else:
            f.write("No subdomains found\n")
        
        f.write("\n\n")
        
        # Ports section
        f.write("OPEN PORTS:\n")
        f.write("-" * 40 + "\n")
        for target, ports in results.get('ports', {}).items():
            f.write(f"\nTarget: {target}\n")
            if ports:
                for port, service in ports.items():
                    f.write(f"  Port {port:5} : {service}\n")
            else:
                f.write("  No open ports found\n")
        
        # Summary
        f.write("\n" + "=" * 60 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"Subdomains found: {len(results.get('subdomains', []))}\n")
        total_ports = sum(len(p) for p in results.get('ports', {}).values())
        f.write(f"Open ports found: {total_ports}\n")
        f.write("=" * 60 + "\n")

def display_results(results):
    """Pretty print results to console"""
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    # Subdomains
    print(f"\n📁 SUBDOMAINS: {len(results.get('subdomains', []))} found")
    if results.get('subdomains'):
        for sub in results['subdomains'][:10]:  # Show first 10
            print(f"   • {sub}")
        if len(results['subdomains']) > 10:
            print(f"   ... and {len(results['subdomains']) - 10} more")
    
    # Ports
    print(f"\n🔓 OPEN PORTS:")
    for target, ports in results.get('ports', {}).items():
        print(f"\n   Target: {target}")
        if ports:
            for port, service in ports.items():
                print(f"     Port {port:5} → {service}")
        else:
            print("     No open ports")
    
    print("\n" + "=" * 60)





    
def validate_arguments(args):
    """
    Check if arguments make sense before running
    """
    errors = []
    
    # Check at least one operation is requested
    if not args.domain and not args.target:
        errors.append("Must specify either --domain or --target (or both)")
    
    # Validate domain format
    if args.domain:
        if len(args.domain) < 4:
            errors.append(f"Domain '{args.domain}' seems too short")
        if ' ' in args.domain:
            errors.append(f"Domain '{args.domain}' contains spaces (invalid)")
    
    # Validate target format (basic check)
    if args.target:
        if args.target.startswith('http://') or args.target.startswith('https://'):
            errors.append(f"Target '{args.target}' should not include http://, just hostname or IP")
    
    # Check conflicting flags
    if args.subdomains_only and args.ports_only:
        errors.append("Cannot use both --subdomains-only and --ports-only")
    
    # Check domain for port scanning
    if args.ports_only and not args.target:
        errors.append("--ports-only requires --target")
    
    return errors

def check_dependencies():
    """
    Verify required modules are installed
    """
    missing = []
    
    try:
        import requests
    except ImportError:
        missing.append("requests - Install with: pip install requests")
    
    try:
        import socket
    except ImportError:
        missing.append("socket - Should be built-in to Python")
    
    try:
        import concurrent.futures
    except ImportError:
        missing.append("concurrent.futures - Should be built-in to Python 3.2+")
    
    return missing

def safe_run(args):
    """
    Main wrapper with error handling
    """
    print("[*] Starting security reconnaissance tool")
    print("[*] Note: Only scan targets you own or have permission to test\n")
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print("[!] Missing dependencies:")
        for dep in missing_deps:
            print(f"    {dep}")
        print("\n[*] Install missing packages and try again")
        return 1
    
    # Validate arguments
    errors = validate_arguments(args)
    if errors:
        print("[!] Argument errors:")
        for error in errors:
            print(f"    • {error}")
        print("\n[*] Use --help for usage information")
        return 1
    
    try:
        # Run the actual reconnaissance
        results = run_recon(args)
        
        # Display results
        display_results(results)
        
        # Save if output requested
        if args.output:
            saved_file = save_results(results, args.output)
            if saved_file:
                print(f"[*] Results also saved to: {saved_file}")
        
        return 0  # Success
        
    except KeyboardInterrupt:
        print("\n\n[!] Scan interrupted by user (Ctrl+C)")
        print("[*] Partial results may be available")
        return 130  # Standard Unix interrupt code
        
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        print("[*] Please report this issue")
        import traceback
        traceback.print_exc()  # Detailed debug info
        return 1  # Error code

# FINAL PART: Main entry point
if __name__ == "__main__":
    """
    This runs when you execute: python recon_tool.py
    """
    # Parse arguments
    args = parse_arguments()
    
    # Run with error handling
    exit_code = safe_run(args)
    
    # Exit with proper code
    sys.exit(exit_code)