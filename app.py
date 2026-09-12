import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Fetch API keys safely from Render Environment Variables
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '').strip()
GIGFORLESS_API_KEY = os.environ.get('GIGFORLESS_API_KEY', '').strip()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/initiate-payment', methods=['POST'])
def initiate_payment():
    data = request.get_json() or {}
    
    network = data.get('network', '')
    phone = data.get('phone', '')
    bundle_gb = data.get('bundle_gb', 1)
    amount = data.get('amount', 0)
    
    # Generate hidden dummy email for Paystack
    dummy_email = f"customer_{phone}@isaiahgeniusherodatahub.com"
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": int(float(amount) * 100),
        "email": dummy_email,
        "metadata": {
            "network": str(network),
            "recipient_phone": str(phone),
            "bundle_gb": str(bundle_gb)
        },
        "callback_url": "https://isaiahgeniusherodatahub.onrender.com/webhook"
    }
    
    response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    return jsonify(response.json())


@app.route('/webhook', methods=['POST'])
def paystack_webhook():
    try:
        event_data = request.get_json() or {}
        
        if event_data.get('event') == 'charge.success':
            data = event_data.get('data', {})
            metadata = data.get('metadata', {})
            
            # Format network name safely (MTN -> mtn, AT -> at)
            raw_network = str(metadata.get('network', '')).lower().strip()
            network_map = {
                'mtn': 'mtn',
                'telecel': 'telecel',
                'at': 'at',
                'at (airteltigo)': 'at'
            }
            network = network_map.get(raw_network, raw_network)
            
            recipient = metadata.get('recipient_phone')
            bundle_gb = float(metadata.get('bundle_gb', 1))
            reference = data.get('reference')
            
            # Convert GB to MB for GigForLess
            bundle_mb = int(bundle_gb * 1024)
            
            gig_headers = {
                "Authorization": f"Bearer {GIGFORLESS_API_KEY}",
                "Content-Type": "application/json"
            }
            
            gig_payload = {
                "network": network,
                "recipient": recipient,
                "bundle_mb": bundle_mb,
                "ref": reference
            }
            
            gig_response = requests.post("https://gigforless.com/v1/data/buy", json=gig_payload, headers=gig_headers)
            print("GigForLess Response:", gig_response.text)
            
            return jsonify({"status": "success", "gigforless_response": gig_response.json()}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        print("Webhook error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)