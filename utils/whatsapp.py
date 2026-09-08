import urllib.parse
import webbrowser


# Your WhatsApp number for project testing
WHATSAPP_NUMBER = "919010467476"


def create_whatsapp_link(
    vehicle_number,
    owner_name,
    violation,
    fine,
    challan_id,
    timestamp,
):
    """
    Creates a WhatsApp Click-to-Chat link
    with the challan message pre-filled.
    """

    message = f"""🚦 TrafficSense AI - Traffic Challan

Dear {owner_name},

A traffic violation has been detected for your vehicle.

🧾 Challan ID: {challan_id}
🚗 Vehicle Number: {vehicle_number}
🚨 Violation: {violation}
💰 Fine Amount: ₹{fine}
📅 Date / Time: {timestamp}

Please pay the challan within the specified time to avoid additional penalties.

Thank you.
TrafficSense AI
"""

    encoded_message = urllib.parse.quote(message)

    whatsapp_url = (
        f"https://wa.me/{WHATSAPP_NUMBER}"
        f"?text={encoded_message}"
    )

    return whatsapp_url


def send_whatsapp_message(
    vehicle_number,
    owner_name,
    violation,
    fine,
    challan_id,
    timestamp,
):
    """
    Opens WhatsApp with the challan message pre-filled.
    """

    whatsapp_url = create_whatsapp_link(
        vehicle_number=vehicle_number,
        owner_name=owner_name,
        violation=violation,
        fine=fine,
        challan_id=challan_id,
        timestamp=timestamp,
    )

    webbrowser.open(whatsapp_url)

    return whatsapp_url