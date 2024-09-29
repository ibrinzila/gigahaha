def troubleshoot_connectivity(issue):
    solutions = {
        "no_internet": [
            "Check if the router is powered on and all cables are properly connected.",
            "Restart your router by unplugging it for 30 seconds, then plugging it back in.",
            "Check if other devices can connect to the internet.",
            "Try connecting your device directly to the modem using an Ethernet cable."
        ],
        "slow_internet": [
            "Close unnecessary applications and browser tabs.",
            "Clear your browser cache and cookies.",
            "Try connecting your device directly to the modem using an Ethernet cable.",
            "Run a speed test at different times of the day to check for consistency."
        ],
        "wifi_not_working": [
            "Make sure Wi-Fi is enabled on your device.",
            "Forget the Wi-Fi network and reconnect to it.",
            "Restart your router by unplugging it for 30 seconds, then plugging it back in.",
            "Check if other devices can connect to the Wi-Fi network."
        ]
    }
    
    return solutions.get(issue, ["I'm sorry, I don't have specific troubleshooting steps for this issue. Please contact our technical support team for assistance."])
