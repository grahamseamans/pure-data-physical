#!/usr/bin/env python3
"""Test script for Pure Data Physical brain patch."""

import subprocess
import time
import sys
from pythonosc import udp_client

PD_PATH = "/Applications/Pd-0.56-2.app/Contents/Resources/bin/pd"
PATCH_PATH = "brain.pd"
PORT = 8000

def main():
    # Start Pd headlessly
    print("Starting Pd...")
    pd = subprocess.Popen(
        [PD_PATH, "-nogui", "-stderr", PATCH_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for Pd to start
    time.sleep(2)

    # Check if Pd is still running
    if pd.poll() is not None:
        print("Pd failed to start!")
        print(pd.stderr.read())
        sys.exit(1)

    print("Pd started, sending OSC messages...\n")

    # Create OSC client
    client = udp_client.SimpleUDPClient("127.0.0.1", PORT)

    # Test 1: hello message
    print("Sending /hello module-1 oscillator")
    client.send_message("/hello", ["module-1", "oscillator"])
    time.sleep(0.5)

    # Test 2: param message
    print("Sending /param module-1 freq 440")
    client.send_message("/param", ["module-1", "freq", 440])
    time.sleep(0.5)

    # Test 3: another param
    print("Sending /param module-1 freq 880")
    client.send_message("/param", ["module-1", "freq", 880])
    time.sleep(0.5)

    # Test 4: goodbye
    print("Sending /goodbye module-1")
    client.send_message("/goodbye", ["module-1"])
    time.sleep(0.5)

    # Let it record for a bit
    print("\nRecording for 2 seconds...")
    time.sleep(2)

    # Kill Pd
    print("\nStopping Pd...")
    pd.terminate()
    pd.wait(timeout=5)

    # Print output
    stdout, stderr = pd.communicate(timeout=5)

    print("\n=== Pd Output ===")
    if stderr:
        for line in stderr.strip().split('\n'):
            if line and not line.startswith('expr:'):  # filter noise
                print(line)

    print("\nDone!")

if __name__ == "__main__":
    main()
