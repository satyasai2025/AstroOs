"""Sample plugin for testing sandbox behavior"""
import sys

def main():
    # Test CPU usage
    if len(sys.argv) > 1 and sys.argv[1] == "--heavy":
        # Simulate heavy computation
        result = 0
        for i in range(10**7):
            result += i
        print(f"Heavy computation result: {result}")

    # Test memory usage
    if len(sys.argv) > 1 and sys.argv[1] == "--memory":
        # Allocate memory
        data = [0] * (10**6)
        print(f"Allocated {len(data)} integers")

    # Test network access
    if len(sys.argv) > 1 and sys.argv[1] == "--network":
        import socket
        try:
            socket.create_connection(("google.com", 80), timeout=5)
            print("Network access successful")
        except Exception as e:
            print(f"Network access failed: {e}")

    # Default behavior
    print("Plugin executed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())