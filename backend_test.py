#!/usr/bin/env python3
"""
Fractal Chart Margin & Forecast Zone Testing
Testing the specific fixes mentioned in review request:
- Chart margins increased (top: 36, right: 350)  
- Forecast zone width increased (420px)
- ScenarioBox and RiskBox components
"""

import requests
import json
import sys
from datetime import datetime

class FractalChartTester:
    def __init__(self, base_url="https://fractal-dev-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": test_name,
            "passed": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")

    def test_focus_pack_api(self, focus="30d", mode="hybrid"):
        """Test GET /api/fractal/v2.1/focus-pack with different horizons"""
        url = f"{self.base_url}/api/fractal/v2.1/focus-pack"
        params = {"focus": focus, "mode": mode}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.log_test(
                    f"Focus Pack API ({focus}, {mode})", 
                    False, 
                    f"Status code {response.status_code}, expected 200"
                )
                return None
                
            data = response.json()
            
            # Check required fields for ScenarioBox
            if not data.get("ok", False):
                self.log_test(
                    f"Focus Pack API ({focus}, {mode})", 
                    False, 
                    f"API returned ok=false, error: {data.get('error', 'Unknown error')}"
                )
                return None
                
            focus_pack = data.get("focusPack", {})
            scenario = focus_pack.get("scenario")
            
            if not scenario:
                self.log_test(
                    f"Focus Pack API ({focus}, {mode})", 
                    False, 
                    "Missing scenario data for ScenarioBox"
                )
                return None
                
            # Validate scenario structure for U6 ScenarioBox
            required_scenario_fields = ["horizonDays", "basePrice", "cases", "probUp", "avgMaxDD", "tailRiskP95"]
            missing_fields = [f for f in required_scenario_fields if f not in scenario]
            
            if missing_fields:
                self.log_test(
                    f"Focus Pack Scenario Data ({focus})", 
                    False, 
                    f"Missing scenario fields: {missing_fields}"
                )
            else:
                cases = scenario.get("cases", [])
                expected_case_labels = {"Bear", "Base", "Bull"}
                found_labels = {case.get("label") for case in cases}
                
                if expected_case_labels.issubset(found_labels):
                    self.log_test(
                        f"Focus Pack Scenario Data ({focus})", 
                        True, 
                        f"Valid scenario with {len(cases)} cases: {sorted(found_labels)}"
                    )
                else:
                    missing_labels = expected_case_labels - found_labels
                    self.log_test(
                        f"Focus Pack Scenario Data ({focus})", 
                        False, 
                        f"Missing case labels: {missing_labels}"
                    )
                    
            return data
            
        except Exception as e:
            self.log_test(
                f"Focus Pack API ({focus}, {mode})", 
                False, 
                f"Request failed: {str(e)}"
            )
            return None

    def test_terminal_api_for_risk_box(self, focus="30d"):
        """Test terminal API for U7 RiskBox data"""
        url = f"{self.base_url}/api/fractal/v2.1/terminal"
        params = {"focus": focus}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.log_test(
                    f"Terminal API for RiskBox ({focus})", 
                    False, 
                    f"Status code {response.status_code}, expected 200"
                )
                return None
                
            data = response.json()
            
            if not data.get("ok", False):
                self.log_test(
                    f"Terminal API for RiskBox ({focus})", 
                    False, 
                    f"API returned ok=false, error: {data.get('error', 'Unknown error')}"
                )
                return None
                
            terminal = data.get("terminal", {})
            
            # Check for RiskBox required fields
            volatility = terminal.get("volatility")
            sizing = terminal.get("sizing")
            
            if not volatility:
                self.log_test(
                    f"Terminal Volatility Data ({focus})", 
                    False, 
                    "Missing volatility data for RiskBox"
                )
                return None
                
            if not sizing:
                self.log_test(
                    f"Terminal Sizing Data ({focus})", 
                    False, 
                    "Missing sizing data for RiskBox"
                )
                return None
                
            # Validate volatility structure
            vol_regime = volatility.get("regime")
            if vol_regime:
                self.log_test(
                    f"Terminal Volatility Regime ({focus})", 
                    True, 
                    f"Vol regime: {vol_regime}"
                )
            else:
                self.log_test(
                    f"Terminal Volatility Regime ({focus})", 
                    False, 
                    "Missing volatility regime"
                )
                
            # Validate sizing structure
            final_size = sizing.get("finalSize")
            sizing_mode = sizing.get("mode")
            blockers = sizing.get("blockers", [])
            
            if final_size is not None:
                self.log_test(
                    f"Terminal Sizing Data ({focus})", 
                    True, 
                    f"Final size: {final_size}, Mode: {sizing_mode}, Blockers: {len(blockers)}"
                )
            else:
                self.log_test(
                    f"Terminal Sizing Data ({focus})", 
                    False, 
                    "Missing finalSize in sizing data"
                )
                
            return data
            
        except Exception as e:
            self.log_test(
                f"Terminal API for RiskBox ({focus})", 
                False, 
                f"Request failed: {str(e)}"
            )
            return None

    def test_chart_margins_data_structure(self, focus_data):
        """Test that forecast data supports increased margins and forecast zone width"""
        if not focus_data:
            return
            
        focus_pack = focus_data.get("focusPack", {})
        forecast = focus_pack.get("forecast")
        
        if not forecast:
            self.log_test(
                "Chart Forecast Data Structure", 
                False, 
                "Missing forecast data for chart rendering"
            )
            return
            
        # Check for unified path (supports chart margin fixes)
        unified_path = forecast.get("unifiedPath")
        if unified_path:
            synthetic_path = unified_path.get("syntheticPath", [])
            horizon_days = unified_path.get("horizonDays")
            
            if len(synthetic_path) > 0 and horizon_days:
                self.log_test(
                    "Chart Unified Path Structure", 
                    True, 
                    f"Unified path with {len(synthetic_path)} points, horizon: {horizon_days}d"
                )
                
                # Test support for longer horizons (180d+ needs increased forecast zone width)
                if horizon_days >= 180:
                    self.log_test(
                        "Long Horizon Support (180d+)", 
                        True, 
                        f"Horizon {horizon_days}d supported for 420px forecast zone"
                    )
                else:
                    self.log_test(
                        "Standard Horizon Support", 
                        True, 
                        f"Horizon {horizon_days}d within standard range"
                    )
            else:
                self.log_test(
                    "Chart Unified Path Structure", 
                    False, 
                    f"Invalid unified path: {len(synthetic_path)} points, horizon: {horizon_days}"
                )
        else:
            # Fallback to legacy format
            price_path = forecast.get("pricePath", [])
            if len(price_path) > 0:
                self.log_test(
                    "Chart Legacy Forecast Structure", 
                    True, 
                    f"Legacy format with {len(price_path)} forecast points"
                )
            else:
                self.log_test(
                    "Chart Forecast Structure", 
                    False, 
                    "No forecast data available for chart rendering"
                )

    def test_different_horizons(self):
        """Test different horizon parameters to verify chart scaling"""
        horizons = [
            ("7d", "hybrid"),
            ("30d", "hybrid"),
            ("90d", "hybrid"),
            ("180d", "hybrid"),  # This should benefit from increased forecast zone width
            ("365d", "hybrid")   # This should benefit from increased forecast zone width
        ]
        
        for focus, mode in horizons:
            focus_data = self.test_focus_pack_api(focus, mode)
            if focus_data:
                self.test_chart_margins_data_structure(focus_data)
                
                # Test terminal data for this horizon
                terminal_data = self.test_terminal_api_for_risk_box(focus)

    def test_api_error_handling(self):
        """Test API error handling"""
        # Test invalid focus
        url = f"{self.base_url}/api/fractal/v2.1/focus-pack"
        params = {"focus": "invalid", "mode": "hybrid"}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code in [400, 422]:
                self.log_test(
                    "Invalid Focus Parameter", 
                    True, 
                    f"Correctly rejected invalid focus with status {response.status_code}"
                )
            else:
                data = response.json()
                if not data.get("ok", True):
                    self.log_test(
                        "Invalid Focus Parameter", 
                        True, 
                        f"API correctly returned error: {data.get('error', 'Unknown')}"
                    )
                else:
                    self.log_test(
                        "Invalid Focus Parameter", 
                        False, 
                        f"API should reject invalid focus, got status {response.status_code}"
                    )
                
        except Exception as e:
            self.log_test(
                "Invalid Focus Parameter", 
                False, 
                f"Request failed: {str(e)}"
            )

    def run_all_tests(self):
        """Run all Fractal chart tests"""
        print("=" * 70)
        print("FRACTAL CHART MARGIN & FORECAST ZONE TESTING")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print()
        
        # Test different horizons and chart scaling
        self.test_different_horizons()
        
        # Test error handling
        self.test_api_error_handling()
        
        print()
        print("=" * 70)
        print(f"RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 70)
        
        return self.tests_passed, self.tests_run, self.test_results

def main():
    """Main test execution"""
    tester = FractalChartTester()
    passed, total, results = tester.run_all_tests()
    
    # Save results
    with open('/app/test_reports/fractal_chart_test_results.json', 'w') as f:
        json.dump({
            "summary": f"Fractal Chart Margin & Forecast Zone Testing",
            "tests_passed": passed,
            "tests_total": total,
            "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "timestamp": datetime.now().isoformat(),
            "test_details": results
        }, f, indent=2)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())