import psutil
import time
from datetime import datetime
import socket


REVERSE_SHELL_PORTS = {
    4444: "Metasploit default",
    5555: "Android ADB / Common malware",
    6666: "Common backdoor port",
    1337: "Leet speak port (elite)",
    31337: "Back orifice / Elite port",
    12345: "NetBus Trojan",
    54321: "Common malware port",
    9999: "Common pentesting port",
    4443: "Alternate Metasploit",
    8080: "Sometimes used for C2"
}


NORMAL_PROCESSES = {
    'chrome.exe', 'firefox.exe', 'msedge.exe',
    'discord.exe', 'spotify.exe', 'steam.exe',
    'code.exe', 'postman.exe', 'slack.exe'
}

def get_ip_info(ip):
    try:

        if ip.startswith(('10.', '172.', '192.168.', '127.')):
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                return f"Local: {hostname}"
            except:
                return "Local network"
        return "External IP"
    except:
        return "Unknown"

def detect_suspicious_connections():
    print("🔍 Reverse Shell Detector Started")
    print("Monitoring network connections...\n")
    
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        alerts = []
        
        try:

            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    remote_ip, remote_port = conn.raddr
                    

                    if remote_ip.startswith('127.'):
                        continue
                    

                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                        proc_cmdline = ' '.join(proc.cmdline())[:50]
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_name = "Unknown"
                        proc_cmdline = "N/A"
                    

                    if remote_port in REVERSE_SHELL_PORTS:
                        reason = REVERSE_SHELL_PORTS[remote_port]
                        alerts.append({
                            'level': 'HIGH',
                            'message': f"Process '{proc_name}' connecting to known reverse shell port {remote_port} ({reason})",
                            'details': f"IP: {remote_ip} | CMD: {proc_cmdline}"
                        })
                    

                    elif (remote_port > 40000 and 
                          proc_name.lower() not in [p.lower() for p in NORMAL_PROCESSES]):
                        alerts.append({
                            'level': 'MEDIUM',
                            'message': f"Unusual process '{proc_name}' connecting to high port {remote_port}",
                            'details': f"IP: {remote_ip} | Port >40000 is unusual for this process"
                        })
                    

                    elif any(keyword in proc_cmdline.lower() for keyword in ['/dev/tcp', 'nc ', 'netcat', 'ncat', 'socat']):
                        alerts.append({
                            'level': 'CRITICAL',
                            'message': f"Process with reverse shell indicators: '{proc_name}'",
                            'details': f"Command contains suspicious keywords: {proc_cmdline}"
                        })
            

            if alerts:
                print(f"\n⏰ [{current_time}] DETECTIONS:")
                for alert in alerts:
                    color = {'CRITICAL': '🟥', 'HIGH': '🟧', 'MEDIUM': '🟨'}[alert['level']]
                    print(f"{color} {alert['level']}: {alert['message']}")
                    print(f"   📋 {alert['details']}")
                    print()
            else:
                print(f"[{current_time}] ✅ No suspicious connections detected")
            
        except Exception as e:
            print(f"[{current_time}] ⚠️ Error: {e}")
        

        time.sleep(5)

    
def educational_info():
    print("="*60)
    print("🎓 EDUCATIONAL REVERSE SHELL DETECTOR")
    print("="*60)
    print("\nThis tool monitors for signs of reverse shells:")
    print("1. Connections to known malicious ports")
    print("2. Unusual processes making network calls")
    print("3. Suspicious command line arguments")
    print("\n⚠️  This is for EDUCATION only!")
    print("   Never run on systems you don't own.")
    print("   Only detects basic patterns.")
    print("\nCommon reverse shell ports being monitored:")
    for port, desc in sorted(REVERSE_SHELL_PORTS.items())[:5]:
        print(f"   Port {port}: {desc}")
    print("="*60)
    print()

if __name__ == "__main__":
    educational_info()
    try:
        detect_suspicious_connections()
    except KeyboardInterrupt:
        print("\n\n🛑 Detector stopped. Stay secure!")