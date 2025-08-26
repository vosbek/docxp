"""
AWS Configuration Debugging Tool
Run this while your backend is running to diagnose the issue
"""
import requests
import json
import time

def test_endpoint(url, description):
    print(f"\n🔍 Testing {description}")
    print(f"   URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"   ✅ Status: {response.status_code} (took {elapsed:.2f}s)")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   📊 Response: {json.dumps(data, indent=6)}")
                return True, data
            except:
                print(f"   📝 Raw Response: {response.text[:200]}...")
        else:
            print(f"   ❌ Error Response: {response.text[:200]}...")
            
    except requests.exceptions.ConnectRefused:
        print(f"   ❌ Connection refused - backend not running?")
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout after 30 seconds")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return False, None

def main():
    print("🚀 DocXP AWS Configuration Diagnostic Tool")
    print("=" * 50)
    
    # Test basic backend health
    success, _ = test_endpoint(
        "http://localhost:8001/health", 
        "Backend Health Check"
    )
    
    if not success:
        print("\n❌ Backend not responding - start your backend first!")
        return
    
    # Test AWS configuration status endpoint
    success, data = test_endpoint(
        "http://localhost:8001/api/configuration/aws/status",
        "AWS Configuration Status"
    )
    
    if success and data:
        if data.get('connected'):
            print(f"\n🎉 AWS Connection is working!")
            print(f"   Account: {data.get('account_id')}")
            print(f"   Region: {data.get('region')}")
            print(f"   Auth Method: {data.get('auth_method')}")
            print(f"   Models: {data.get('available_models_count')}")
        else:
            print(f"\n❌ AWS Connection failed:")
            print(f"   Error: {data.get('error')}")
            print(f"   Auth Method: {data.get('auth_method')}")
    
    # Test CORS preflight
    print(f"\n🔍 Testing CORS preflight...")
    try:
        response = requests.options(
            "http://localhost:8001/api/configuration/aws/status",
            headers={
                'Origin': 'http://localhost:4200',
                'Access-Control-Request-Method': 'GET'
            }
        )
        print(f"   ✅ CORS preflight: {response.status_code}")
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        if cors_headers:
            print(f"   📝 CORS headers: {json.dumps(cors_headers, indent=6)}")
    except Exception as e:
        print(f"   ❌ CORS test failed: {e}")
    
    print(f"\n📋 Summary:")
    print(f"   - Backend should be running on http://localhost:8001")
    print(f"   - Frontend should be running on http://localhost:4200")
    print(f"   - Check browser Developer Tools > Network tab for more details")
    print(f"   - Look for any CORS errors in browser console")

if __name__ == "__main__":
    main()
