#!/usr/bin/env python
"""
Enhanced server runner for QR Attendance System with auto-restart capabilities
"""
import subprocess
import time
import os
import signal
import sys
import socket
import requests
from urllib.error import URLError
import threading

# Configuration
HOST = '0.0.0.0'  # Bind to all interfaces
PORT = 8000
CHECK_INTERVAL = 30  # Seconds between health checks
MAX_RESTART_ATTEMPTS = 5
HEALTH_CHECK_TIMEOUT = 5  # Seconds
SERVER_START_TIMEOUT = 10  # Seconds

def get_local_ip():
    """Get the machine's local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "127.0.0.1"

def is_server_running(url, timeout=HEALTH_CHECK_TIMEOUT):
    """Check if the server is responding to requests"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500  # Any non-server error status is considered "running"
    except requests.exceptions.RequestException:
        return False

def print_server_info():
    """Print information about the server"""
    local_ip = get_local_ip()
    print("\n" + "="*50)
    print(f"Server running at:")
    print(f"- Local:   http://127.0.0.1:{PORT}/")
    print(f"- Network: http://{local_ip}:{PORT}/")
    print(f"QR Code URL: http://{local_ip}:{PORT}/student/attendance")
    print("="*50 + "\n")

def setup_firewall():
    """Ensure the port is open in Windows Firewall"""
    if sys.platform != "win32":
        return  # Only run on Windows
    
    try:
        # Check if rule already exists
        check_cmd = f'netsh advfirewall firewall show rule name="Django QR Attendance System" | findstr "Rule Name:"'
        rule_exists = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if rule_exists.returncode != 0:
            print("Setting up firewall rule for port 8000...")
            # Create inbound rule for port 8000
            cmd = (
                f'netsh advfirewall firewall add rule name="Django QR Attendance System" '
                f'dir=in action=allow protocol=TCP localport={PORT}'
            )
            subprocess.run(cmd, shell=True, check=True)
            print("Firewall rule added successfully.")
        else:
            print("Firewall rule already exists.")
    except Exception as e:
        print(f"Warning: Could not set up firewall rule. {str(e)}")
        print("You may need to manually allow port 8000 in your firewall settings.")

def health_check_worker(process, url):
    """Worker thread to perform periodic health checks"""
    restart_attempts = 0
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        # Skip check if process has terminated on its own
        if process.poll() is not None:
            print("Server process has terminated. Stopping health checks.")
            break
        
        # Check server health
        if not is_server_running(url):
            print(f"Server not responding at {url}! Attempting restart...")
            
            # Restart logic
            restart_attempts += 1
            if restart_attempts > MAX_RESTART_ATTEMPTS:
                print(f"Exceeded maximum restart attempts ({MAX_RESTART_ATTEMPTS}). Please check server logs.")
                # Terminate the process forcefully
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    if sys.platform == "win32":
                        subprocess.run(f"taskkill /F /PID {process.pid}", shell=True)
                    else:
                        os.kill(process.pid, signal.SIGKILL)
                break
            
            # Try to gracefully stop the server
            try:
                print("Attempting to stop the server gracefully...")
                if sys.platform == "win32":
                    subprocess.run(f"taskkill /PID {process.pid}", shell=True)
                else:
                    os.kill(process.pid, signal.SIGTERM)
                # Wait for process to end
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't respond
                    if sys.platform == "win32":
                        subprocess.run(f"taskkill /F /PID {process.pid}", shell=True)
                    else:
                        os.kill(process.pid, signal.SIGKILL)
            except Exception as e:
                print(f"Error stopping server: {str(e)}")
            
            # Start a new process
            print("Starting a new server process...")
            process = start_server()
            
            # Wait for server to start
            server_started = False
            for _ in range(SERVER_START_TIMEOUT):
                if is_server_running(url):
                    server_started = True
                    break
                time.sleep(1)
            
            if server_started:
                print("Server restarted successfully.")
                restart_attempts = 0  # Reset counter on successful restart
            else:
                print("Server failed to restart properly.")
        else:
            # Reset attempts if server is healthy
            restart_attempts = 0

def start_server():
    """Start the Django development server"""
    cmd = [sys.executable, "manage.py", "runserver", f"{HOST}:{PORT}"]
    
    # Use different creation flags for Windows
    if sys.platform == "win32":
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    return process

def main():
    """Main function to run the server with monitoring"""
    print("Starting QR Attendance System Server with auto-restart capabilities...")
    
    # Check and setup firewall if needed
    setup_firewall()
    
    # Start the server
    process = start_server()
    
    # Wait for the server to start
    time.sleep(2)
    
    # Display server information
    print_server_info()
    
    # Health check URL
    local_ip = get_local_ip()
    health_check_url = f"http://{local_ip}:{PORT}/"
    
    # Start health check in a separate thread
    health_check_thread = threading.Thread(
        target=health_check_worker,
        args=(process, health_check_url),
        daemon=True
    )
    health_check_thread.start()
    
    # Create a reader thread for server output
    def reader_thread(stream, prefix):
        for line in iter(stream.readline, ''):
            if line:
                print(f"{prefix}: {line.rstrip()}")
    
    stdout_thread = threading.Thread(
        target=reader_thread,
        args=(process.stdout, "SERVER"),
        daemon=True
    )
    stderr_thread = threading.Thread(
        target=reader_thread,
        args=(process.stderr, "SERVER ERROR"),
        daemon=True
    )
    
    stdout_thread.start()
    stderr_thread.start()
    
    try:
        # Wait for the process to finish
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        try:
            if sys.platform == "win32":
                subprocess.run(f"taskkill /PID {process.pid}", shell=True)
            else:
                process.terminate()
            process.wait(timeout=5)
        except:
            if sys.platform == "win32":
                subprocess.run(f"taskkill /F /PID {process.pid}", shell=True)
            else:
                os.kill(process.pid, signal.SIGKILL)
        print("Server shutdown complete.")

if __name__ == "__main__":
    main() 