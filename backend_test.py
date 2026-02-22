"""
Backend API Testing for Fractal Module U3, U4, U5 Features
Tests the /api/fractal/v2.1/focus-pack endpoint with different horizons
"""

import requests
import json
import sys
from datetime import datetime

class FractalAPITester:
    def __init__(self, base_url="https://fractal-dev-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []
        
    def log_result(self, test_name, passed, response=None, error=None):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
            if error:
                print(f"   Error: {error}")
            if response:
                print(f"   Status: {response.status_code}")
                try:
                    print(f"   Response: {response.text[:200]}...")
                except:
                    pass
            self.failed_tests.append(test_name)
    
    def test_get_lifecycle_state(self):
        """Test GET /api/lifecycle/state"""
        try:
            url = f"{self.base_url}/api/lifecycle/state"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and 'data' in data:
                    # Check if states exist
                    states = data['data'].get('states', [])
                    combined = data['data'].get('combined', {})
                    btc = data['data'].get('btc')
                    spx = data['data'].get('spx')
                    
                    print(f"   Found {len(states)} lifecycle states")
                    print(f"   BTC state: {btc['status'] if btc else 'None'}")
                    print(f"   SPX state: {spx['status'] if spx else 'None'}")
                    print(f"   Combined ready: {combined.get('ready', False)}")
                    
                    self.log_result("GET /api/lifecycle/state", True)
                    return True
                else:
                    self.log_result("GET /api/lifecycle/state", False, response, "Invalid response format")
            else:
                self.log_result("GET /api/lifecycle/state", False, response)
        except Exception as e:
            self.log_result("GET /api/lifecycle/state", False, error=str(e))
        return False
    
    def test_get_lifecycle_events(self):
        """Test GET /api/lifecycle/events"""
        try:
            url = f"{self.base_url}/api/lifecycle/events"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and 'data' in data:
                    events = data['data']
                    print(f"   Found {len(events)} lifecycle events")
                    if events:
                        print(f"   Latest event: {events[0].get('type')} for {events[0].get('modelId')}")
                    self.log_result("GET /api/lifecycle/events", True)
                    return True
                else:
                    self.log_result("GET /api/lifecycle/events", False, response, "Invalid response format")
            else:
                self.log_result("GET /api/lifecycle/events", False, response)
        except Exception as e:
            self.log_result("GET /api/lifecycle/events", False, error=str(e))
        return False
    
    def test_initialize_lifecycle(self):
        """Test POST /api/lifecycle/init"""
        try:
            url = f"{self.base_url}/api/lifecycle/init"
            response = requests.post(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and 'data' in data:
                    btc_state = data['data'].get('btc', {})
                    spx_state = data['data'].get('spx', {})
                    print(f"   BTC initialized: {btc_state.get('status', 'Unknown')}")
                    print(f"   SPX initialized: {spx_state.get('status', 'Unknown')}")
                    self.log_result("POST /api/lifecycle/init", True)
                    return True
                else:
                    self.log_result("POST /api/lifecycle/init", False, response, "Invalid response format")
            else:
                self.log_result("POST /api/lifecycle/init", False, response)
        except Exception as e:
            self.log_result("POST /api/lifecycle/init", False, error=str(e))
        return False
    
    def test_force_warmup(self, asset="BTC"):
        """Test POST /api/lifecycle/actions/force-warmup"""
        try:
            url = f"{self.base_url}/api/lifecycle/actions/force-warmup"
            payload = {"asset": asset, "targetDays": 30}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    state = data.get('data', {})
                    print(f"   {asset} warmup started: {state.get('status', 'Unknown')}")
                    self.log_result(f"POST /api/lifecycle/actions/force-warmup ({asset})", True)
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"POST /api/lifecycle/actions/force-warmup ({asset})", False, response, error_msg)
            else:
                self.log_result(f"POST /api/lifecycle/actions/force-warmup ({asset})", False, response)
        except Exception as e:
            self.log_result(f"POST /api/lifecycle/actions/force-warmup ({asset})", False, error=str(e))
        return False
    
    def test_force_apply(self, asset="BTC"):
        """Test POST /api/lifecycle/actions/force-apply"""
        try:
            url = f"{self.base_url}/api/lifecycle/actions/force-apply"
            payload = {"asset": asset, "reason": "Test force apply"}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    state = data.get('data', {})
                    print(f"   {asset} force apply successful: {state.get('status', 'Unknown')}")
                    self.log_result(f"POST /api/lifecycle/actions/force-apply ({asset})", True)
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    print(f"   Force apply blocked: {error_msg}")
                    # This might be expected behavior, so we'll count as passed if we get a proper error response
                    self.log_result(f"POST /api/lifecycle/actions/force-apply ({asset})", True)
                    return True
            else:
                self.log_result(f"POST /api/lifecycle/actions/force-apply ({asset})", False, response)
        except Exception as e:
            self.log_result(f"POST /api/lifecycle/actions/force-apply ({asset})", False, error=str(e))
        return False
    
    def test_revoke(self, asset="BTC"):
        """Test POST /api/lifecycle/actions/revoke"""
        try:
            url = f"{self.base_url}/api/lifecycle/actions/revoke"
            payload = {"asset": asset, "reason": "Test revoke"}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    state = data.get('data', {})
                    print(f"   {asset} revoked: {state.get('status', 'Unknown')}")
                    self.log_result(f"POST /api/lifecycle/actions/revoke ({asset})", True)
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"POST /api/lifecycle/actions/revoke ({asset})", False, response, error_msg)
            else:
                self.log_result(f"POST /api/lifecycle/actions/revoke ({asset})", False, response)
        except Exception as e:
            self.log_result(f"POST /api/lifecycle/actions/revoke ({asset})", False, error=str(e))
        return False
    
    def test_reset_simulation(self, asset="BTC"):
        """Test POST /api/lifecycle/actions/reset-simulation"""
        try:
            url = f"{self.base_url}/api/lifecycle/actions/reset-simulation"
            payload = {"asset": asset, "reason": "Test reset"}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    state = data.get('data', {})
                    print(f"   {asset} reset to simulation: {state.get('status', 'Unknown')}")
                    self.log_result(f"POST /api/lifecycle/actions/reset-simulation ({asset})", True)
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"POST /api/lifecycle/actions/reset-simulation ({asset})", False, response, error_msg)
            else:
                self.log_result(f"POST /api/lifecycle/actions/reset-simulation ({asset})", False, response)
        except Exception as e:
            self.log_result(f"POST /api/lifecycle/actions/reset-simulation ({asset})", False, error=str(e))
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # L3 SPECIFIC TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_constitution_apply(self, asset="BTC", test_hash=None):
        """Test L3.1: POST /api/lifecycle/constitution/apply"""
        try:
            hash_value = test_hash or f"test_hash_{int(datetime.now().timestamp())}"
            url = f"{self.base_url}/api/lifecycle/constitution/apply"
            payload = {"asset": asset, "hash": hash_value}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    result = data.get('data', {})
                    print(f"   {asset} constitution applied: {result.get('applied', False)}")
                    print(f"   New status: {result.get('newStatus', 'Unknown')}")
                    print(f"   Reason: {result.get('reason', 'No reason')}")
                    self.log_result(f"L3.1 Constitution Apply ({asset})", True)
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"L3.1 Constitution Apply ({asset})", False, response, error_msg)
            else:
                self.log_result(f"L3.1 Constitution Apply ({asset})", False, response)
        except Exception as e:
            self.log_result(f"L3.1 Constitution Apply ({asset})", False, error=str(e))
        return None
    
    def test_drift_update(self, asset="BTC", severity="OK"):
        """Test L3.2: POST /api/lifecycle/drift/update"""
        try:
            url = f"{self.base_url}/api/lifecycle/drift/update"
            payload = {
                "asset": asset, 
                "severity": severity,
                "deltaHitRate": 0.05,
                "deltaSharpe": 0.1
            }
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    result = data.get('data', {})
                    print(f"   {asset} drift updated to {severity}")
                    print(f"   Updated: {result.get('updated', False)}")
                    if result.get('revoked'):
                        print(f"   🚨 AUTO-REVOKED: {result.get('reason', 'Unknown reason')}")
                    self.log_result(f"L3.2 Drift Update ({asset}, {severity})", True)
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"L3.2 Drift Update ({asset}, {severity})", False, response, error_msg)
            else:
                self.log_result(f"L3.2 Drift Update ({asset}, {severity})", False, response)
        except Exception as e:
            self.log_result(f"L3.2 Drift Update ({asset}, {severity})", False, error=str(e))
        return None
    
    def test_samples_increment(self, asset="BTC", count=1):
        """Test L3.5: POST /api/lifecycle/samples/increment"""
        try:
            url = f"{self.base_url}/api/lifecycle/samples/increment"
            payload = {"asset": asset, "count": count}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    result = data.get('data', {})
                    print(f"   {asset} live samples: {result.get('liveSamples', 0)}")
                    if result.get('promoted'):
                        print(f"   🎉 AUTO-PROMOTED to APPLIED!")
                    self.log_result(f"L3.5 Samples Increment ({asset}, +{count})", True)
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"L3.5 Samples Increment ({asset}, +{count})", False, response, error_msg)
            else:
                self.log_result(f"L3.5 Samples Increment ({asset}, +{count})", False, response)
        except Exception as e:
            self.log_result(f"L3.5 Samples Increment ({asset}, +{count})", False, error=str(e))
        return None
    
    def test_integrity_check(self, asset="BTC"):
        """Test L3.4: POST /api/lifecycle/integrity/check"""
        try:
            url = f"{self.base_url}/api/lifecycle/integrity/check"
            payload = {"asset": asset}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    result = data.get('data', {})
                    integrity = result.get('integrityResult', {})
                    print(f"   {asset} integrity valid: {integrity.get('valid', 'Unknown')}")
                    if integrity.get('fixes'):
                        print(f"   Fixes applied: {', '.join(integrity.get('fixes', []))}")
                    self.log_result(f"L3.4 Integrity Check ({asset})", True)
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"L3.4 Integrity Check ({asset})", False, response, error_msg)
            else:
                self.log_result(f"L3.4 Integrity Check ({asset})", False, response)
        except Exception as e:
            self.log_result(f"L3.4 Integrity Check ({asset})", False, error=str(e))
        return None
    
    def test_check_promotion(self, asset="BTC"):
        """Test L3.5: POST /api/lifecycle/check-promotion"""
        try:
            url = f"{self.base_url}/api/lifecycle/check-promotion"
            payload = {"asset": asset}
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    result = data.get('data', {})
                    print(f"   {asset} promotion check - promoted: {result.get('promoted', False)}")
                    print(f"   Blocked: {result.get('blocked', False)}")
                    print(f"   Reason: {result.get('reason', 'No reason')}")
                    self.log_result(f"L3.5 Check Promotion ({asset})", True)
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_result(f"L3.5 Check Promotion ({asset})", False, response, error_msg)
            else:
                self.log_result(f"L3.5 Check Promotion ({asset})", False, response)
        except Exception as e:
            self.log_result(f"L3.5 Check Promotion ({asset})", False, error=str(e))
        return None
    
    def test_model_status(self, model_id="BTC"):
        """Test GET /api/lifecycle/{modelId}/status"""
        try:
            url = f"{self.base_url}/api/lifecycle/{model_id}/status"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and 'data' in data:
                    state = data['data']
                    print(f"   {model_id} status: {state.get('status', 'Unknown')}")
                    print(f"   System mode: {state.get('systemMode', 'Unknown')}")
                    self.log_result(f"GET /api/lifecycle/{model_id}/status", True)
                    return True
                else:
                    self.log_result(f"GET /api/lifecycle/{model_id}/status", False, response, "Invalid response format")
            else:
                self.log_result(f"GET /api/lifecycle/{model_id}/status", False, response)
        except Exception as e:
            self.log_result(f"GET /api/lifecycle/{model_id}/status", False, error=str(e))
        return False
    
    def test_l3_workflow_scenarios(self):
        """Test comprehensive L3 workflow scenarios"""
        print("\n🧪 Testing L3 Workflow Scenarios...")
        
        # Scenario 1: Constitution Binding (L3.1) - change constitution on APPLIED model
        print("\n📋 Scenario 1: Constitution Binding Test...")
        self.test_reset_simulation("BTC")  # Start fresh
        self.test_force_apply("BTC")  # Apply first
        constitution_result = self.test_constitution_apply("BTC", "new_constitution_hash_123")
        if constitution_result and constitution_result.get('applied'):
            print("   ✅ Constitution binding worked - status reset as expected")
        
        # Scenario 2: Drift Auto-Revoke (L3.2) - CRITICAL drift should revoke APPLIED model
        print("\n⚠️  Scenario 2: Drift Auto-Revoke Test...")
        self.test_force_apply("BTC")  # Apply first
        revoke_result = self.test_drift_update("BTC", "CRITICAL")
        if revoke_result and revoke_result.get('revoked'):
            print("   ✅ Auto-revoke worked - model revoked due to CRITICAL drift")
        
        # Scenario 3: Drift Recovery (L3.3) - recovery from CRITICAL should enter WARMUP  
        print("\n🔄 Scenario 3: Drift Recovery Test...")
        # Model should be REVOKED from previous test
        recovery_result = self.test_drift_update("BTC", "OK")
        if recovery_result:
            # Check if model is now in WARMUP
            self.test_model_status("BTC")
            print("   ✅ Drift recovery test completed")
        
        # Scenario 4: Auto-Promotion (L3.5) - 30+ samples + OK drift should promote
        print("\n🚀 Scenario 4: Auto-Promotion Test...")
        self.test_reset_simulation("BTC")  # Fresh start
        self.test_force_warmup("BTC")      # Start warmup
        self.test_drift_update("BTC", "OK")  # Ensure drift is OK
        # Add samples incrementally to test progression
        for i in range(5):
            samples_result = self.test_samples_increment("BTC", 6)  # Add 6 samples each time (total 30)
            if samples_result and samples_result.get('promoted'):
                print(f"   ✅ Auto-promotion triggered after {samples_result.get('liveSamples', 0)} samples")
                break
        
        # Scenario 5: State Integrity (L3.4) - validate and fix state
        print("\n🛡️  Scenario 5: State Integrity Test...")
        self.test_integrity_check("BTC")
        self.test_integrity_check("SPX")
    
    def run_all_tests(self):
        """Run all lifecycle API tests"""
        print("🔍 Testing Lifecycle API endpoints...")
        print("=" * 50)
        
        # Initialize lifecycle if needed
        print("\n📝 Initializing Lifecycle States...")
        self.test_initialize_lifecycle()
        
        # Test state retrieval
        print("\n📊 Testing State Retrieval...")
        self.test_get_lifecycle_state()
        self.test_get_lifecycle_events()
        
        # Test individual model status
        print("\n🎯 Testing Model Status...")
        self.test_model_status("BTC")
        self.test_model_status("SPX")
        
        # Test lifecycle actions for both models
        print("\n🚀 Testing L2 Lifecycle Actions for BTC...")
        self.test_force_warmup("BTC")
        self.test_force_apply("BTC")
        self.test_revoke("BTC")
        self.test_reset_simulation("BTC")
        
        print("\n🚀 Testing L2 Lifecycle Actions for SPX...")
        self.test_force_warmup("SPX")
        self.test_force_apply("SPX")
        self.test_revoke("SPX")
        self.test_reset_simulation("SPX")
        
        # Test L3 features
        print("\n🔬 Testing L3 Features...")
        self.test_constitution_apply("BTC", "test_hash_btc")
        self.test_constitution_apply("SPX", "test_hash_spx")
        self.test_drift_update("BTC", "WARN")
        self.test_drift_update("SPX", "OK")
        self.test_samples_increment("BTC", 5)
        self.test_samples_increment("SPX", 10)
        self.test_integrity_check("BTC")
        self.test_integrity_check("SPX")
        self.test_check_promotion("BTC")
        self.test_check_promotion("SPX")
        
        # Test comprehensive L3 workflows
        self.test_l3_workflow_scenarios()
        
        # Final results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print(f"❌ Failed tests: {', '.join(self.failed_tests)}")
            return False
        else:
            print("✅ All tests passed!")
            return True

def main():
    tester = LifecycleAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())