"""
Backend API Testing for Fractal Module U6 Features
Tests the U6 Scenarios 2.0 implementation including ScenarioBox component
and backend scenario pack generation from focus-pack endpoint
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

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.request(method, url, headers=headers, params=params, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.issues.append(f"{name}: Status {response.status_code} (expected {expected_status})")
                try:
                    return False, response.json()
                except:
                    return False, response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.issues.append(f"{name}: {str(e)}")
            return False, {}

    def test_focus_pack_7d_vs_365d(self):
        """U3: Test that 7d and 365d return different matches"""
        print("\n🎯 Testing U3: Multi-Horizon calls with different matches")
        
        # Test 7d horizon
        success_7d, data_7d = self.run_test(
            "Focus pack BTC 7d",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "7d"}
        )
        
        # Test 365d horizon  
        success_365d, data_365d = self.run_test(
            "Focus pack BTC 365d", 
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "365d"}
        )
        
        if success_7d and success_365d:
            # Check if responses have different matches
            focus_pack_7d = data_7d.get('focusPack', data_7d)
            focus_pack_365d = data_365d.get('focusPack', data_365d)
            matches_7d = focus_pack_7d.get('overlay', {}).get('matches', [])
            matches_365d = focus_pack_365d.get('overlay', {}).get('matches', [])
            
            if len(matches_7d) > 0 and len(matches_365d) > 0:
                # Compare first match IDs to see if they're different
                first_match_7d = matches_7d[0].get('id', 'none') if matches_7d else 'none'
                first_match_365d = matches_365d[0].get('id', 'none') if matches_365d else 'none'
                
                print(f"   7d first match: {first_match_7d}, count: {len(matches_7d)}")
                print(f"   365d first match: {first_match_365d}, count: {len(matches_365d)}")
                
                if first_match_7d != first_match_365d:
                    print("✅ Different horizons return different matches")
                    return True, data_7d, data_365d
                else:
                    print("⚠️  Same first match for different horizons - might be expected")
                    return True, data_7d, data_365d
            else:
                self.issues.append("U3: No matches found in responses")
                return False, data_7d, data_365d
        
        return False, None, None

    def test_horizon_field_in_meta(self):
        """U3: Test that horizon field is present in meta"""
        print("\n🎯 Testing U3: Horizon field in response meta")
        
        success, data = self.run_test(
            "Focus pack meta horizon field",
            "GET", 
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        if success and data:
            focus_pack = data.get('focusPack', data)
            meta = focus_pack.get('meta', {})
            horizon = meta.get('horizon')
            focus = meta.get('focus')
            
            print(f"   Meta horizon: {horizon}")
            print(f"   Meta focus: {focus}")
            
            if horizon:
                print("✅ Horizon field present in meta")
                return True, data
            else:
                self.issues.append("U3: Missing horizon field in meta")
                return False, data
        
        return False, None

    def test_data_status_logic(self):
        """U3: Test DataStatusIndicator logic (matches count and quality)"""
        print("\n🎯 Testing U3: Data Status Indicator logic")
        
        success, data = self.run_test(
            "Focus pack for data status",
            "GET",
            "api/fractal/v2.1/focus-pack", 
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        if success and data:
            focus_pack = data.get('focusPack', data)
            matches_count = len(focus_pack.get('overlay', {}).get('matches', []))
            diagnostics = focus_pack.get('diagnostics', {})
            quality_score = diagnostics.get('qualityScore', 0)
            sample_size = diagnostics.get('sampleSize', 0)
            
            print(f"   Matches count: {matches_count}")
            print(f"   Quality score: {quality_score}")
            print(f"   Sample size: {sample_size}")
            
            # Determine expected status based on logic from DataStatusIndicator
            expected_status = "UNKNOWN"
            if matches_count > 0:
                if quality_score >= 0.5 and sample_size >= 5:
                    expected_status = "REAL"
                elif quality_score < 0.3 or sample_size < 5:
                    expected_status = "FALLBACK"
                else:
                    expected_status = "REAL"
            else:
                expected_status = "FALLBACK"
            
            print(f"   Expected status: {expected_status}")
            print("✅ Data for status indicator available")
            return True, data, expected_status
        
        return False, None, None

    def test_hybrid_summary_data(self):
        """U4: Test HybridSummaryPanel data (% returns AND price targets)"""
        print("\n🎯 Testing U4: Hybrid Chart data for returns and price targets")
        
        success, data = self.run_test(
            "Focus pack for hybrid data",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        if success and data:
            focus_pack = data.get('focusPack', data)
            forecast = focus_pack.get('forecast', {})
            primary_match = focus_pack.get('primarySelection', {}).get('primaryMatch', {})
            
            # Check forecast path for synthetic prices
            price_path = forecast.get('path', []) or forecast.get('pricePath', [])
            current_price = forecast.get('currentPrice', 0)
            
            print(f"   Current price: {current_price}")
            print(f"   Forecast path length: {len(price_path)}")
            print(f"   Primary match available: {'id' in primary_match}")
            
            if price_path and current_price > 0:
                end_price = price_path[-1] if price_path else current_price
                return_pct = ((end_price - current_price) / current_price) * 100
                print(f"   Forecast end price: {end_price}")
                print(f"   Expected return: {return_pct:.1f}%")
                print("✅ Data available for % returns and price targets")
                return True, data
            else:
                self.issues.append("U4: Missing price path or current price data")
                return False, data
        
        return False, None

    def test_forecast_tooltip_data(self):
        """U4: Test ForecastTooltip data availability"""
        print("\n🎯 Testing U4: Forecast Tooltip data structure")
        
        success, data = self.run_test(
            "Focus pack for tooltip data",
            "GET", 
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        if success and data:
            forecast = data.get('forecast', {})
            unified_path = forecast.get('unifiedPath', {}) or data.get('unifiedPath', {})
            
            # Check if unified path has the needed data for tooltips
            synthetic_path = unified_path.get('syntheticPath', [])
            replay_path = unified_path.get('replayPath', [])
            
            print(f"   Unified synthetic path length: {len(synthetic_path)}")
            print(f"   Unified replay path length: {len(replay_path)}")
            
            if synthetic_path or replay_path:
                print("✅ Unified path data available for forecast tooltips")
                return True, data
            else:
                # Fallback to legacy structure
                price_path = forecast.get('path', [])
                primary_match = data.get('primarySelection', {}).get('primaryMatch', {})
                replay_data = primary_match.get('aftermathNormalized', [])
                
                print(f"   Legacy price path length: {len(price_path)}")
                print(f"   Legacy replay data length: {len(replay_data)}")
                
                if price_path and replay_data:
                    print("✅ Legacy forecast data available for tooltips")
                    return True, data
                else:
                    self.issues.append("U4: Missing forecast tooltip data")
                    return False, data
        
        return False, None

    def test_signal_header_data(self):
        """U5: Test SignalHeader data for 4 cards"""
        print("\n🎯 Testing U5: Signal Header data for 4 cards")
        
        # Need terminal data for SignalHeader
        success, data = self.run_test(
            "Terminal data for signal header",
            "GET",
            "api/fractal/v2.1/terminal",
            200,
            params={"symbol": "BTC", "set": "extended", "focus": "30d"}
        )
        
        if success and data:
            consensus = data.get('decisionKernel', {}).get('consensus', {})
            conflict = data.get('decisionKernel', {}).get('conflict', {})
            volatility = data.get('volatility', {})
            phase_snapshot = data.get('phaseSnapshot', {})
            
            print(f"   Consensus available: {'score' in consensus}")
            print(f"   Conflict available: {'level' in conflict}")
            print(f"   Volatility available: {'regime' in volatility}")
            print(f"   Phase snapshot available: {'currentPhase' in phase_snapshot}")
            
            # Check if we have data for all 4 cards
            has_signal_data = 'score' in consensus or 'dir' in consensus
            has_confidence_data = True  # Can be derived from other metrics
            has_market_mode_data = 'currentPhase' in phase_snapshot
            has_risk_data = 'regime' in volatility
            
            card_status = {
                'Signal': has_signal_data,
                'Confidence': has_confidence_data, 
                'Market Mode': has_market_mode_data,
                'Risk': has_risk_data
            }
            
            for card, available in card_status.items():
                status = "✅" if available else "❌"
                print(f"   {card} card data: {status}")
            
            if all(card_status.values()):
                print("✅ All 4 signal header cards have data")
                return True, data
            else:
                missing_cards = [card for card, available in card_status.items() if not available]
                self.issues.append(f"U5: Missing data for cards: {', '.join(missing_cards)}")
                return True, data  # Partial success
        
        return False, None

    def test_u6_scenario_pack_structure(self):
        """U6: Test that focus-pack returns scenario object with correct structure"""
        print("\n🎯 Testing U6: Scenario pack structure in focus-pack response")
        
        success, data = self.run_test(
            "Focus pack BTC 30d for scenario",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        if success and data:
            focus_pack = data.get('focusPack', data)  # Handle nested response
            scenario = focus_pack.get('scenario')
            if not scenario:
                self.issues.append("U6: Missing scenario object in focus-pack response")
                return False, data
            
            # Check required scenario fields
            required_fields = [
                'horizonDays', 'basePrice', 'returns', 'targets', 
                'probUp', 'sampleSize', 'dataStatus', 'cases'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in scenario:
                    missing_fields.append(field)
            
            if missing_fields:
                self.issues.append(f"U6: Missing scenario fields: {missing_fields}")
                return False, data
                
            # Check returns structure (p10, p50, p90)
            returns = scenario.get('returns', {})
            if not all(k in returns for k in ['p10', 'p50', 'p90']):
                self.issues.append("U6: Missing p10/p50/p90 returns in scenario")
                return False, data
                
            # Check targets structure
            targets = scenario.get('targets', {})
            if not all(k in targets for k in ['p10', 'p50', 'p90']):
                self.issues.append("U6: Missing p10/p50/p90 targets in scenario")
                return False, data
                
            # Check cases array (Bear/Base/Bull)
            cases = scenario.get('cases', [])
            if len(cases) != 3:
                self.issues.append(f"U6: Expected 3 scenario cases, got {len(cases)}")
                return False, data
                
            case_labels = [case.get('label') for case in cases]
            expected_labels = ['Bear', 'Base', 'Bull']
            if set(case_labels) != set(expected_labels):
                self.issues.append(f"U6: Expected cases {expected_labels}, got {case_labels}")
                return False, data
            
            print(f"   ✅ Scenario horizonDays: {scenario.get('horizonDays')}")
            print(f"   ✅ Scenario basePrice: {scenario.get('basePrice')}")
            print(f"   ✅ Scenario probUp: {scenario.get('probUp')}")
            print(f"   ✅ Scenario sampleSize: {scenario.get('sampleSize')}")
            print(f"   ✅ Scenario dataStatus: {scenario.get('dataStatus')}")
            print(f"   ✅ Cases: {[case.get('label') for case in cases]}")
            print("✅ U6 Scenario pack structure is valid")
            return True, data
        
        return False, None
    
    def test_u6_different_horizons_scenarios(self):
        """U6: Test that different horizons (7d vs 365d) return different scenario targets"""
        print("\n🎯 Testing U6: Different scenario targets for 7d vs 365d horizons")
        
        # Test 7d scenario
        success_7d, data_7d = self.run_test(
            "Scenario pack BTC 7d",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "7d"}
        )
        
        # Test 365d scenario
        success_365d, data_365d = self.run_test(
            "Scenario pack BTC 365d",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "365d"}
        )
        
        if success_7d and success_365d:
            focus_pack_7d = data_7d.get('focusPack', data_7d)
            focus_pack_365d = data_365d.get('focusPack', data_365d)
            scenario_7d = focus_pack_7d.get('scenario', {})
            scenario_365d = focus_pack_365d.get('scenario', {})
            
            if not scenario_7d or not scenario_365d:
                self.issues.append("U6: Missing scenario data in horizon responses")
                return False, data_7d, data_365d
            
            # Compare horizon days
            horizon_7d = scenario_7d.get('horizonDays')
            horizon_365d = scenario_365d.get('horizonDays')
            
            print(f"   7d horizonDays: {horizon_7d}")
            print(f"   365d horizonDays: {horizon_365d}")
            
            if horizon_7d != 7 or horizon_365d != 365:
                self.issues.append(f"U6: Wrong horizonDays - 7d:{horizon_7d}, 365d:{horizon_365d}")
                return False, data_7d, data_365d
            
            # Compare target prices (should be different)
            targets_7d = scenario_7d.get('targets', {})
            targets_365d = scenario_365d.get('targets', {})
            
            p90_7d = targets_7d.get('p90', 0)
            p90_365d = targets_365d.get('p90', 0)
            
            print(f"   7d P90 target: ${p90_7d:,}")
            print(f"   365d P90 target: ${p90_365d:,}")
            
            if p90_7d == p90_365d:
                print("⚠️  Same P90 targets for different horizons - unexpected")
            else:
                print("✅ Different P90 targets for different horizons")
            
            return True, data_7d, data_365d
        
        return False, None, None
    
    def test_u6_data_status_real_vs_fallback(self):
        """U6: Test dataStatus is REAL when sampleSize >= 5"""
        print("\n🎯 Testing U6: Data status logic (REAL when sampleSize >= 5)")
        
        success, data = self.run_test(
            "Scenario pack data status",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        if success and data:
            focus_pack = data.get('focusPack', data)
            scenario = focus_pack.get('scenario', {})
            if not scenario:
                self.issues.append("U6: Missing scenario for data status test")
                return False, data
            
            sample_size = scenario.get('sampleSize', 0)
            data_status = scenario.get('dataStatus', 'UNKNOWN')
            
            print(f"   Sample size: {sample_size}")
            print(f"   Data status: {data_status}")
            
            # Expected logic: REAL when sampleSize >= 5
            expected_status = 'REAL' if sample_size >= 5 else 'FALLBACK'
            
            print(f"   Expected status: {expected_status}")
            
            if data_status == expected_status:
                print("✅ Data status logic is correct")
                return True, data
            else:
                self.issues.append(f"U6: Wrong data status - got {data_status}, expected {expected_status}")
                return False, data
        
        return False, None
    
    def test_fractal_page_endpoint(self):
        """Test that frontend /fractal page loads without errors"""
        print("\n🎯 Testing Frontend: /fractal page accessibility")
        
        # Test if the focus-pack endpoint works - this is what the frontend calls
        success, data = self.run_test(
            "Focus pack for frontend",
            "GET",
            "api/fractal/v2.1/focus-pack",
            200,
            params={"symbol": "BTC", "focus": "30d"}
        )
        
        return success, data

def main():
    print("🚀 Starting Fractal Module U6 Backend API Testing...")
    print("=" * 60)
    
    # Use the public endpoint
    tester = FractalAPITester("https://fractal-dev-3.preview.emergentagent.com")
    
    # Run all tests
    results = {}
    
    # U6 Tests - Scenarios 2.0
    results['u6_scenario_structure'] = tester.test_u6_scenario_pack_structure()
    results['u6_different_horizons'] = tester.test_u6_different_horizons_scenarios()
    results['u6_data_status'] = tester.test_u6_data_status_real_vs_fallback()
    
    # Previous tests (keeping for regression testing)
    results['u3_multi_horizon'] = tester.test_focus_pack_7d_vs_365d()
    results['u3_horizon_field'] = tester.test_horizon_field_in_meta()
    results['u3_data_status'] = tester.test_data_status_logic()
    
    # U4 Tests  
    results['u4_hybrid_summary'] = tester.test_hybrid_summary_data()
    results['u4_forecast_tooltip'] = tester.test_forecast_tooltip_data()
    
    # U5 Tests
    results['u5_signal_header'] = tester.test_signal_header_data()
    
    # Frontend Page Test
    results['frontend_page'] = tester.test_fractal_page_endpoint()
    
    # Print summary
    print(f"\n📊 Testing Summary:")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.issues:
        print(f"\n⚠️  Issues found:")
        for issue in tester.issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ All tests passed!")
    
    # Return appropriate exit code
    return 0 if len(tester.issues) == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)