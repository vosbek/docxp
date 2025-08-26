#!/usr/bin/env python3
"""
Test AWS Configuration Endpoint Directly
"""
import requests
import json
import sys

def test_aws_endpoint():
    """Test the AWS configuration endpoint"""
    base_url = "http://localhost:8001"
    endpoint = "/api/configuration/aws/status"
    url = f"{base_url}{endpoint}"
    
    print(f"🔍 Testing AWS Configuration Endpoint")
    print(f"📡 URL: {url}")
    print(f"🕐 Making request...")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response Data:")
            print(json.dumps(data, indent=2))
            
            if data.get('connected'):
                print(f"🎉 AWS Connection: SUCCESS")
                print(f"   Account: {data.get('account_id')}")
                print(f"   Region: {data.get('region')}")
                print(f"   Auth Method: {data.get('auth_method')}")
                print(f"   Models Available: {data.get('available_models_count')}")
            else:
                print(f"❌ AWS Connection: FAILED")
                print(f"   Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectRefused:
        print(f"❌ Connection refused - is the backend running on {base_url}?")
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_aws_endpoint()
