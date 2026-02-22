#!/usr/bin/env python3
"""
L4.1 Daily Run Orchestrator Backend Testing
Tests for daily pipeline with lifecycle integration
"""

import requests
import json
import sys
import time
from datetime import datetime

class DailyRunTester:
    def __init__(self, base_url="https://fractal-module-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = []
        
    def log_result(self, test_name, passed, response=None, error=None, details=""):
        """Log test result with detailed information"""
        self.tests_run += 1
        result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error": error
        }
        
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name}")
            if error:
                print(f"   Error: {error}")
            if response:
                print(f"   Status: {response.status_code}")
                try:
                    print(f"   Response: {response.text[:300]}...")
                except:
                    pass
            self.failed_tests.append(test_name)
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                result["response_data"] = response_data
            except:
                pass
                
        self.test_results.append(result)

    def test_daily_run_pipeline(self, asset="BTC"):
        """Test POST /api/ops/daily-run/run-now"""
        try:
            url = f"{self.base_url}/api/ops/daily-run/run-now"
            params = {"asset": asset}
            
            print(f"\n🔍 Testing Daily Run Pipeline for {asset}...")
            start_time = time.time()
            
            response = requests.post(url, params=params, timeout=60)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get('ok', False):
                    self.log_result(
                        f"Daily Run Pipeline ({asset})", 
                        False, 
                        response, 
                        f"API returned ok=false: {data.get('error', 'Unknown error')}"
                    )
                    return None
                
                result = data.get('data', {})
                
                # Validate required fields
                required_fields = ['runId', 'asset', 'mode', 'durationMs', 'steps', 'lifecycle']
                missing_fields = [f for f in required_fields if f not in result]
                
                if missing_fields:
                    self.log_result(
                        f"Daily Run Pipeline ({asset})", 
                        False, 
                        response, 
                        f"Missing required fields: {missing_fields}"
                    )
                    return None
                
                # Validate steps - should be exactly 11 (L4.2: added AUTO_WARMUP)
                steps = result.get('steps', [])
                if len(steps) != 11:
                    self.log_result(
                        f"Daily Run Pipeline ({asset})", 
                        False, 
                        response, 
                        f"Expected 11 steps, got {len(steps)}"
                    )
                    return None
                
                # Validate step order and names (L4.2: AUTO_WARMUP is step 5)
                expected_steps = [
                    'SNAPSHOT_WRITE', 'OUTCOME_RESOLVE', 'LIVE_SAMPLE_UPDATE',
                    'DRIFT_CHECK', 'AUTO_WARMUP', 'LIFECYCLE_HOOKS', 'WARMUP_PROGRESS_WRITE',
                    'AUTO_PROMOTE', 'INTEL_TIMELINE_WRITE', 'ALERTS_DISPATCH',
                    'INTEGRITY_GUARD'
                ]
                
                step_names = [step.get('name') for step in steps]
                if step_names != expected_steps:
                    self.log_result(
                        f"Daily Run Pipeline ({asset})", 
                        False, 
                        response, 
                        f"Step order mismatch. Expected: {expected_steps}, Got: {step_names}"
                    )
                    return None
                
                # Validate lifecycle fields
                lifecycle = result.get('lifecycle', {})
                if 'before' not in lifecycle or 'after' not in lifecycle:
                    self.log_result(
                        f"Daily Run Pipeline ({asset})", 
                        False, 
                        response, 
                        "Missing lifecycle.before or lifecycle.after"
                    )
                    return None
                
                # Count successful steps
                successful_steps = sum(1 for step in steps if step.get('ok', False))
                total_duration = result.get('durationMs', 0)
                
                # L4.2: Check AUTO_WARMUP step specifically
                auto_warmup_step = next((s for s in steps if s.get('name') == 'AUTO_WARMUP'), None)
                auto_warmup_details = ""
                if auto_warmup_step and auto_warmup_step.get('details'):
                    if auto_warmup_step['details'].get('started'):
                        auto_warmup_details = f", AUTO_WARMUP: Started ({auto_warmup_step['details'].get('reason', 'Unknown reason')})"
                    else:
                        auto_warmup_details = f", AUTO_WARMUP: Skipped ({auto_warmup_step['details'].get('reason', 'Unknown reason')})"
                
                details = f"RunId: {result.get('runId')}, Steps: {successful_steps}/11, Duration: {total_duration}ms{auto_warmup_details}"
                if lifecycle.get('transition'):
                    details += f", Transition: {lifecycle.get('transition')}"
                
                self.log_result(
                    f"Daily Run Pipeline ({asset})", 
                    True, 
                    response, 
                    details=details
                )
                
                return result
                
            else:
                self.log_result(
                    f"Daily Run Pipeline ({asset})", 
                    False, 
                    response, 
                    f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            self.log_result(
                f"Daily Run Pipeline ({asset})", 
                False, 
                error="Request timeout (>60s)"
            )
        except Exception as e:
            self.log_result(
                f"Daily Run Pipeline ({asset})", 
                False, 
                error=str(e)
            )
        
        return None

    def test_pipeline_step_timing(self, run_result):
        """Validate that all steps have timing information"""
        if not run_result:
            return
            
        steps = run_result.get('steps', [])
        
        for step in steps:
            step_name = step.get('name', 'Unknown')
            has_timing = 'ms' in step and isinstance(step.get('ms'), (int, float))
            
            if has_timing:
                timing = step.get('ms')
                self.log_result(
                    f"Step Timing - {step_name}", 
                    True, 
                    details=f"{timing}ms"
                )
            else:
                self.log_result(
                    f"Step Timing - {step_name}", 
                    False, 
                    error="Missing or invalid timing data"
                )

    def test_lifecycle_transition_capture(self, run_result):
        """Validate lifecycle before/after capture"""
        if not run_result:
            return
            
        lifecycle = run_result.get('lifecycle', {})
        before = lifecycle.get('before')
        after = lifecycle.get('after')
        transition = lifecycle.get('transition')
        
        # Test before state capture
        if before and isinstance(before, dict):
            required_before_fields = ['status', 'systemMode', 'liveSamples']
            missing_before = [f for f in required_before_fields if f not in before]
            
            if missing_before:
                self.log_result(
                    "Lifecycle Before Capture", 
                    False, 
                    error=f"Missing fields: {missing_before}"
                )
            else:
                self.log_result(
                    "Lifecycle Before Capture", 
                    True, 
                    details=f"Status: {before.get('status')}, Samples: {before.get('liveSamples')}"
                )
        else:
            self.log_result("Lifecycle Before Capture", False, error="Invalid or missing before state")
        
        # Test after state capture
        if after and isinstance(after, dict):
            required_after_fields = ['status', 'systemMode', 'liveSamples']
            missing_after = [f for f in required_after_fields if f not in after]
            
            if missing_after:
                self.log_result(
                    "Lifecycle After Capture", 
                    False, 
                    error=f"Missing fields: {missing_after}"
                )
            else:
                self.log_result(
                    "Lifecycle After Capture", 
                    True, 
                    details=f"Status: {after.get('status')}, Samples: {after.get('liveSamples')}"
                )
        else:
            self.log_result("Lifecycle After Capture", False, error="Invalid or missing after state")
        
        # Test transition detection
        if before and after:
            status_changed = before.get('status') != after.get('status')
            has_transition = bool(transition)
            
            if status_changed and has_transition:
                self.log_result(
                    "Lifecycle Transition Detection", 
                    True, 
                    details=f"Detected: {transition}"
                )
            elif not status_changed and not has_transition:
                self.log_result(
                    "Lifecycle Transition Detection", 
                    True, 
                    details="No status change, no transition (correct)"
                )
            else:
                self.log_result(
                    "Lifecycle Transition Detection", 
                    False, 
                    error=f"Status changed: {status_changed}, Transition: {has_transition}"
                )

    def test_daily_run_status(self, asset="BTC"):
        """Test GET /api/ops/daily-run/status"""
        try:
            url = f"{self.base_url}/api/ops/daily-run/status"
            params = {"asset": asset}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok', False):
                    result = data.get('data', {})
                    last_run = result.get('lastRun')
                    
                    if last_run:
                        details = f"Found last run: {last_run.get('type', 'Unknown')} at {last_run.get('ts', 'Unknown')}"
                        meta = last_run.get('meta', {})
                        if 'runId' in meta:
                            details += f", RunId: {meta.get('runId')}"
                    else:
                        details = "No previous runs found"
                    
                    self.log_result(
                        f"Daily Run Status ({asset})", 
                        True, 
                        response, 
                        details=details
                    )
                    return result
                else:
                    self.log_result(
                        f"Daily Run Status ({asset})", 
                        False, 
                        response, 
                        f"API returned ok=false: {data.get('error', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    f"Daily Run Status ({asset})", 
                    False, 
                    response, 
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                f"Daily Run Status ({asset})", 
                False, 
                error=str(e)
            )
        
        return None

    def test_daily_run_history(self, asset="BTC", limit=5):
        """Test GET /api/ops/daily-run/history"""
        try:
            url = f"{self.base_url}/api/ops/daily-run/history"
            params = {"asset": asset, "limit": str(limit)}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok', False):
                    events = data.get('data', [])
                    
                    if isinstance(events, list):
                        details = f"Found {len(events)} historical runs"
                        if events:
                            latest = events[0]
                            details += f", Latest: {latest.get('ts', 'Unknown time')}"
                        
                        self.log_result(
                            f"Daily Run History ({asset})", 
                            True, 
                            response, 
                            details=details
                        )
                        return events
                    else:
                        self.log_result(
                            f"Daily Run History ({asset})", 
                            False, 
                            response, 
                            "Invalid response format: data is not a list"
                        )
                else:
                    self.log_result(
                        f"Daily Run History ({asset})", 
                        False, 
                        response, 
                        f"API returned ok=false: {data.get('error', 'Unknown error')}"
                    )
            else:
                self.log_result(
                    f"Daily Run History ({asset})", 
                    False, 
                    response, 
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                f"Daily Run History ({asset})", 
                False, 
                error=str(e)
            )
        
        return None

    def test_invalid_asset(self):
        """Test API with invalid asset parameter"""
        try:
            url = f"{self.base_url}/api/ops/daily-run/run-now"
            params = {"asset": "INVALID"}
            
            response = requests.post(url, params=params, timeout=30)
            
            if response.status_code == 400:
                data = response.json()
                if not data.get("ok", True) and "must be BTC or SPX" in data.get("error", ""):
                    self.log_result(
                        "Invalid Asset Validation", 
                        True, 
                        response,
                        details="Correctly rejected invalid asset"
                    )
                else:
                    self.log_result(
                        "Invalid Asset Validation", 
                        False, 
                        response,
                        "Wrong error response format"
                    )
            else:
                self.log_result(
                    "Invalid Asset Validation", 
                    False, 
                    response,
                    f"Expected 400, got {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "Invalid Asset Validation", 
                False, 
                error=str(e)
            )

    def run_comprehensive_tests(self):
        """Run comprehensive test suite for Daily Run Orchestrator"""
        print("=" * 70)
        print("🚀 L4.1 DAILY RUN ORCHESTRATOR TESTING")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print()
        
        # Test pipeline for both assets
        print("🔄 Testing Pipeline Execution...")
        btc_result = self.test_daily_run_pipeline("BTC")
        spx_result = self.test_daily_run_pipeline("SPX")
        
        # Test step timing validation
        print("\n⏱️  Testing Step Timing...")
        if btc_result:
            self.test_pipeline_step_timing(btc_result)
        if spx_result:
            self.test_pipeline_step_timing(spx_result)
        
        # Test lifecycle integration
        print("\n🔄 Testing Lifecycle Integration...")
        if btc_result:
            self.test_lifecycle_transition_capture(btc_result)
        
        # Test status and history endpoints
        print("\n📊 Testing Status & History Endpoints...")
        self.test_daily_run_status("BTC")
        self.test_daily_run_status("SPX")
        self.test_daily_run_history("BTC", 3)
        self.test_daily_run_history("SPX", 3)
        
        # Test error handling
        print("\n❌ Testing Error Handling...")
        self.test_invalid_asset()
        
        # Final results
        print("\n" + "=" * 70)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print(f"❌ Failed tests: {', '.join(self.failed_tests)}")
        else:
            print("✅ All tests passed!")
        
        return self.tests_passed, self.tests_run, self.test_results

def main():
    """Main test execution"""
    tester = DailyRunTester()
    passed, total, results = tester.run_comprehensive_tests()
    
    # Save detailed results
    with open('/app/backend/daily_run_test_results.json', 'w') as f:
        json.dump({
            "summary": "L4.1 Daily Run Orchestrator Backend Testing",
            "tests_passed": passed,
            "tests_total": total,
            "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "timestamp": datetime.now().isoformat(),
            "test_details": results,
            "failed_tests": tester.failed_tests
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to /app/backend/daily_run_test_results.json")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())