import requests
import time
import json
import logging
import jsonschema # Now used for schema validation
from urllib.parse import urljoin
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed # ADDED: For concurrency
try:
    from utils.connection_pool import connection_pool, cache_manager, rate_limiter, get_cached_or_fetch
except ImportError:
    # Fallback if connection pool utilities are not available
    connection_pool = None
    cache_manager = None
    rate_limiter = None
    get_cached_or_fetch = None

class APITester:
    def __init__(self, max_workers: int = 10):
        self.logger = logging.getLogger(__name__)
        
        # Use connection pool if available, otherwise create regular session
        if connection_pool:
            self.session = connection_pool.get_session('api_tester')
        else:
            self.session = requests.Session()
            
        self.session.headers.update({
            'User-Agent': 'AutoTestify-API-Tester/2.0'
        })
        # ADDED: ThreadPoolExecutor for running tests in parallel
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers

    def test_endpoints(self, base_url: str, endpoints: List[Dict] = None) -> Dict:
        """Test API endpoints concurrently and return comprehensive results."""
        if not self._is_valid_url(base_url):
            raise ValueError(f"Invalid base_url provided: {base_url}")

        if not endpoints:
            print("No endpoints provided, attempting to discover them...")
            endpoints = self._discover_endpoints(base_url)
            if not endpoints:
                print("Could not discover any endpoints. Aborting.")
                return {}
        
        print(f"Testing {len(endpoints)} endpoints...")
        
        start_time = time.time()
        future_to_endpoint = {
            self.executor.submit(self._test_single_endpoint, base_url, ep): ep 
            for ep in endpoints
        }

        # Collect results as they complete
        endpoint_results = []
        for future in as_completed(future_to_endpoint):
            try:
                result = future.result()
                endpoint_results.append(result)
            except Exception as exc:
                endpoint = future_to_endpoint[future]
                print(f"Endpoint {endpoint.get('path')} generated an exception: {exc}")

        total_duration = time.time() - start_time
        
        # ADDED: Aggregation logic is moved to its own method for clarity
        return self._aggregate_results(base_url, endpoint_results, total_duration)

    def _aggregate_results(self, base_url: str, results: List[Dict], duration: float) -> Dict:
        """Enhanced aggregation with detailed performance and reliability metrics."""
        successful_tests = sum(1 for r in results if r['success'])
        failed_tests = len(results) - successful_tests
        
        status_code_dist = {}
        content_type_dist = {}
        response_times = [r['response_time'] for r in results if r['response_time'] > 0]
        method_performance = {}
        endpoint_grades = []

        for r in results:
            # Status code distribution
            status_code = str(r['status_code']) if r['status_code'] else 'Error'
            status_code_dist[status_code] = status_code_dist.get(status_code, 0) + 1
            
            # Content type analysis
            content_type = r.get('content_type', 'unknown').split(';')[0]
            content_type_dist[content_type] = content_type_dist.get(content_type, 0) + 1
            
            # Method-based performance tracking
            method = r['method']
            if method not in method_performance:
                method_performance[method] = {'times': [], 'success_rate': 0, 'total': 0}
            method_performance[method]['times'].append(r['response_time'])
            method_performance[method]['total'] += 1
            if r['success']:
                method_performance[method]['success_rate'] += 1
            
            # Calculate endpoint grade
            grade = self._calculate_endpoint_grade(r)
            endpoint_grades.append(grade)
            r['performance_grade'] = grade

        # Enhanced performance metrics
        perf_metrics = self._calculate_performance_metrics(results, response_times, method_performance)
        
        # Calculate overall API grade
        overall_grade = self._calculate_overall_grade(endpoint_grades, successful_tests, len(results))
        
        # Calculate additional insights
        avg_response_size = sum(r.get('response_size', 0) for r in results) / len(results) if results else 0
        total_data_transferred = sum(r.get('response_size', 0) for r in results)
        
        # Calculate API health score
        health_score = self._calculate_api_health_score(results, perf_metrics)
        
        final_report = {
            'base_url': base_url,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration_seconds': round(duration, 2),
            'total_endpoints_tested': len(results),
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': round((successful_tests / len(results)) * 100, 1) if results else 0,
            'overall_grade': overall_grade,
            'performance_metrics': perf_metrics,
            'status_code_distribution': status_code_dist,
            'content_type_analysis': content_type_dist,
            'method_performance': method_performance,
            'reliability_score': self._calculate_reliability_score(results),
            'health_score': health_score,
            'security_analysis': self._analyze_security(results),
            'data_transfer_analysis': {
                'total_bytes_transferred': total_data_transferred,
                'average_response_size': round(avg_response_size, 2),
                'largest_response': max((r.get('response_size', 0) for r in results), default=0),
                'smallest_response': min((r.get('response_size', 0) for r in results if r.get('response_size', 0) > 0), default=0)
            },
            'endpoint_results': results,
            'test_summary': {
                'fastest_response': perf_metrics.get('min_response_time', 0),
                'slowest_response': perf_metrics.get('max_response_time', 0),
                'response_time_range': perf_metrics.get('range', 0),
                'consistency_rating': perf_metrics.get('performance_consistency', 'N/A'),
                'outliers_detected': perf_metrics.get('outlier_count', 0)
            }
        }
        return final_report
    
    def _calculate_api_health_score(self, results, perf_metrics):
        """Calculate overall API health score combining multiple factors."""
        if not results:
            return 0
        
        # Success rate component (30%)
        success_rate = sum(1 for r in results if r['success']) / len(results)
        success_component = success_rate * 30
        
        # Performance component (25%)
        avg_time = perf_metrics.get('average_response_time', 0)
        if avg_time < 100:
            perf_component = 25
        elif avg_time < 300:
            perf_component = 22
        elif avg_time < 500:
            perf_component = 18
        elif avg_time < 1000:
            perf_component = 14
        elif avg_time < 2000:
            perf_component = 10
        else:
            perf_component = 5
        
        # Consistency component (20%)
        cv = perf_metrics.get('coefficient_of_variation', 100)
        if cv < 10:
            consistency_component = 20
        elif cv < 25:
            consistency_component = 16
        elif cv < 50:
            consistency_component = 12
        elif cv < 100:
            consistency_component = 8
        else:
            consistency_component = 4
        
        # Error handling component (15%)
        status_codes = [r.get('status_code', 0) for r in results if r.get('status_code')]
        if status_codes:
            error_rate = sum(1 for code in status_codes if code >= 400) / len(status_codes)
            error_component = max(0, 15 - (error_rate * 15))
        else:
            error_component = 7.5
        
        # Security component (10%)
        security_headers = sum(1 for r in results if r.get('has_security_headers', False))
        security_component = (security_headers / len(results)) * 10
        
        total_health = success_component + perf_component + consistency_component + error_component + security_component
        return round(min(100, max(0, total_health)), 1)

    def _discover_endpoints(self, base_url: str) -> List[Dict]:
        """Discover common API endpoints and try to find an OpenAPI/Swagger spec."""
        # CHANGED: Prioritize discovering from Swagger/OpenAPI spec first
        try:
            swagger_endpoints = self._discover_from_swagger(base_url)
            if swagger_endpoints:
                print(f"Discovered {len(swagger_endpoints)} endpoints from OpenAPI/Swagger spec.")
                return swagger_endpoints
        # CHANGED: Catch specific exceptions, not a bare `except`
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Could not automatically discover from spec: {e}")

        print("Falling back to common endpoint probing.")
        common_endpoints = [
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/status', 'method': 'GET', 'description': 'Status endpoint'},
            {'path': '/api/v1/ping', 'method': 'GET', 'description': 'Ping endpoint'},
            {'path': '/api/v1/health', 'method': 'GET', 'description': 'API health check'},
            {'path': '/api/status', 'method': 'GET', 'description': 'API status endpoint'},
            {'path': '/ping', 'method': 'GET', 'description': 'Simple ping endpoint'},
            {'path': '/api/v1/status', 'method': 'GET', 'description': 'API v1 status'},
            {'path': '/healthcheck', 'method': 'GET', 'description': 'Health check endpoint'},
            {'path': '/api/healthcheck', 'method': 'GET', 'description': 'API health check'},
            {'path': '/metrics', 'method': 'GET', 'description': 'Metrics endpoint'}
        ]
        return common_endpoints

    def _discover_from_swagger(self, base_url: str) -> List[Dict]:
        """Try to discover endpoints from Swagger/OpenAPI specification."""
        swagger_paths = ['/openapi.json', '/swagger.json', '/api/docs/json']
        for path in swagger_paths:
            spec_url = urljoin(base_url, path)
            try:
                response = self.session.get(spec_url, timeout=5)
                response.raise_for_status() # Will raise HTTPError for bad responses
                spec = response.json()
                return self._parse_openapi_spec(spec)
            # CHANGED: More specific exception handling
            except (requests.exceptions.RequestException, json.JSONDecodeError):
                continue
        return []

    def _parse_openapi_spec(self, spec: Dict) -> List[Dict]:
        """Parse OpenAPI specification to extract endpoints."""
        endpoints = []
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'description': details.get('summary', 'No description'),
                        # ADDED: Extract response schema for validation
                        'expected_schema': details.get('responses', {}).get('200', {}).get('content', {}).get('application/json', {}).get('schema')
                    })
        # CHANGED: Removed arbitrary limit of 20 endpoints
        return endpoints

    def _test_single_endpoint(self, base_url: str, endpoint_config: Dict) -> Dict:
        """Enhanced single endpoint testing with detailed metrics."""
        full_url = urljoin(base_url, endpoint_config['path'])
        method = endpoint_config.get('method', 'GET')
        
        result = {
            'endpoint': endpoint_config['path'],
            'method': method,
            'url': full_url,
            'success': False,
            'status_code': None,
            'response_time': -1,
            'response_size': 0,
            'content_type': None,
            'schema_valid': 'N/A',
            'headers_count': 0,
            'has_cache_headers': False,
            'has_security_headers': False,
            'error': None,
            'performance_grade': 'F'
        }
        
        try:
            start_time = time.time()
            
            kwargs = {'timeout': 15}
            # ADDED: Allow passing test data in the endpoint config
            if method in ['POST', 'PUT', 'PATCH'] and 'data' in endpoint_config:
                kwargs['json'] = endpoint_config['data']
            
            response = self.session.request(method, full_url, **kwargs)
            
            result['response_time'] = round((time.time() - start_time) * 1000, 2)
            result['status_code'] = response.status_code
            result['response_size'] = len(response.content)
            result['content_type'] = response.headers.get('content-type', '')
            result['headers_count'] = len(response.headers)
            
            # Analyze response headers
            result['has_cache_headers'] = any(h in response.headers for h in ['cache-control', 'etag', 'expires'])
            security_headers = ['x-frame-options', 'x-content-type-options', 'x-xss-protection', 'strict-transport-security']
            result['has_security_headers'] = any(h in response.headers for h in security_headers)
            
            # Enhanced success criteria
            result['success'] = 200 <= response.status_code < 300 and result['response_time'] < 10000
            
            # ADDED: Schema validation logic
            if 'application/json' in result['content_type'] and endpoint_config.get('expected_schema'):
                try:
                    is_valid, error = self._validate_response_schema(response.json(), endpoint_config['expected_schema'])
                    result['schema_valid'] = is_valid
                    if not is_valid:
                        result['success'] = False # If schema is invalid, the test fails
                        result['error'] = f"Schema validation failed: {error}"
                except json.JSONDecodeError:
                    result['schema_valid'] = False
                    result['error'] = "Response is not valid JSON."

        # CHANGED: More specific exception handling
        except requests.exceptions.Timeout:
            result['error'] = 'Request timed out'
        except requests.exceptions.RequestException as e:
            result['error'] = f'Request failed: {e}'
        except Exception as e:
            result['error'] = f'An unexpected error occurred: {e}'
            
        return result

    def _validate_response_schema(self, response_data: Dict, schema: Dict) -> (bool, str):
        """Validates response data against a JSON schema."""
        try:
            jsonschema.validate(instance=response_data, schema=schema)
            return True, ""
        except jsonschema.exceptions.ValidationError as e:
            # Return a simplified error message
            return False, f"At path `/{'/'.join(map(str, e.path))}`: {e.message}"
        except Exception as e:
            return False, f"An unexpected schema validation error occurred: {e}"

    def _calculate_performance_metrics(self, results, response_times, method_performance):
        """Calculate comprehensive and accurate performance metrics."""
        if not response_times:
            return {
                'average_response_time': 0,
                'median_response_time': 0,
                'std_deviation': 0,
                'coefficient_of_variation': 0,
                'p50_response_time': 0,
                'p75_response_time': 0,
                'p90_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'fastest_endpoint': None,
                'slowest_endpoint': None,
                'throughput_estimate': 0,
                'performance_consistency': 'N/A',
                'outlier_count': 0,
                'response_time_distribution': {}
            }
            
        # Enhanced percentile calculation with better accuracy
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        def accurate_percentile(p):
            """Calculate percentile using linear interpolation method"""
            if n == 1:
                return sorted_times[0]
            
            # Use the R-6 quantile method (used by Excel and many statistical packages)
            h = (n + 1) * p / 100
            h_floor = int(h)
            h_ceil = h_floor + 1
            
            if h_floor <= 0:
                return sorted_times[0]
            elif h_ceil >= n:
                return sorted_times[n - 1]
            else:
                # Linear interpolation
                return sorted_times[h_floor - 1] + (h - h_floor) * (sorted_times[h_ceil - 1] - sorted_times[h_floor - 1])
        
        # Calculate basic statistics
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        # Calculate standard deviation
        variance = sum((x - avg_time) ** 2 for x in response_times) / len(response_times)
        std_dev = variance ** 0.5
        
        # Calculate coefficient of variation (relative variability)
        cv = (std_dev / avg_time * 100) if avg_time > 0 else 0
        
        # Determine performance consistency
        if cv < 10:
            consistency = "Excellent (Very Consistent)"
        elif cv < 25:
            consistency = "Good (Consistent)"
        elif cv < 50:
            consistency = "Fair (Moderately Variable)"
        elif cv < 100:
            consistency = "Poor (Highly Variable)"
        else:
            consistency = "Critical (Extremely Variable)"
        
        # Detect outliers using IQR method
        q1 = accurate_percentile(25)
        q3 = accurate_percentile(75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = [t for t in response_times if t < lower_bound or t > upper_bound]
        
        # Find fastest and slowest endpoints with more details
        fastest_res = min(results, key=lambda r: r['response_time'] if r['response_time'] > 0 else float('inf'))
        slowest_res = max(results, key=lambda r: r['response_time'])
        
        # Enhanced method performance calculation
        for method, data in method_performance.items():
            if data['times']:
                method_times = data['times']
                data['avg_response_time'] = round(sum(method_times) / len(method_times), 2)
                data['median_response_time'] = round(sorted(method_times)[len(method_times)//2], 2)
                data['min_response_time'] = round(min(method_times), 2)
                data['max_response_time'] = round(max(method_times), 2)
                data['std_deviation'] = round((sum((x - data['avg_response_time']) ** 2 for x in method_times) / len(method_times)) ** 0.5, 2)
                data['success_rate'] = round((data['success_rate'] / data['total']) * 100, 1)
                data['throughput'] = round(1000 / data['avg_response_time'], 2) if data['avg_response_time'] > 0 else 0
        
        # Calculate response time distribution
        distribution = {
            'excellent_under_100ms': len([t for t in response_times if t < 100]),
            'very_good_100_200ms': len([t for t in response_times if 100 <= t < 200]),
            'good_200_500ms': len([t for t in response_times if 200 <= t < 500]),
            'fair_500ms_1s': len([t for t in response_times if 500 <= t < 1000]),
            'slow_1s_2s': len([t for t in response_times if 1000 <= t < 2000]),
            'very_slow_2s_5s': len([t for t in response_times if 2000 <= t < 5000]),
            'critical_over_5s': len([t for t in response_times if t >= 5000])
        }
        
        # Calculate more accurate throughput estimate
        # Consider concurrent requests and actual test duration
        total_test_time = sum(response_times) / 1000  # Convert to seconds
        concurrent_throughput = len(results) / max(total_test_time, 0.001)  # Requests per second if run sequentially
        
        # Estimate potential concurrent throughput (assuming 10 concurrent connections)
        estimated_concurrent_throughput = min(concurrent_throughput * 10, 1000 / avg_time * 1000) if avg_time > 0 else 0
        
        return {
            'average_response_time': round(avg_time, 2),
            'median_response_time': round(accurate_percentile(50), 2),
            'std_deviation': round(std_dev, 2),
            'coefficient_of_variation': round(cv, 2),
            'p50_response_time': round(accurate_percentile(50), 2),
            'p75_response_time': round(accurate_percentile(75), 2),
            'p90_response_time': round(accurate_percentile(90), 2),
            'p95_response_time': round(accurate_percentile(95), 2),
            'p99_response_time': round(accurate_percentile(99), 2),
            'min_response_time': round(min_time, 2),
            'max_response_time': round(max_time, 2),
            'fastest_endpoint': {
                'endpoint': fastest_res['endpoint'], 
                'method': fastest_res['method'],
                'time_ms': fastest_res['response_time'],
                'status_code': fastest_res['status_code']
            },
            'slowest_endpoint': {
                'endpoint': slowest_res['endpoint'], 
                'method': slowest_res['method'],
                'time_ms': slowest_res['response_time'],
                'status_code': slowest_res['status_code']
            },
            'throughput_estimate': round(concurrent_throughput, 2),
            'concurrent_throughput_estimate': round(estimated_concurrent_throughput, 2),
            'performance_consistency': consistency,
            'outlier_count': len(outliers),
            'outlier_percentage': round(len(outliers) / len(response_times) * 100, 1),
            'response_time_distribution': distribution,
            'iqr': round(iqr, 2),
            'range': round(max_time - min_time, 2)
        }
    
    def _calculate_endpoint_grade(self, result):
        """Calculate enhanced performance grade for individual endpoint with more granular scoring."""
        if not result['success']:
            return 'F'
        
        response_time = result['response_time']
        status_code = result.get('status_code', 0)
        has_security_headers = result.get('has_security_headers', False)
        has_cache_headers = result.get('has_cache_headers', False)
        
        # Base grade from response time with more granular thresholds
        if response_time < 50:
            base_grade = 'A+'
        elif response_time < 100:
            base_grade = 'A'
        elif response_time < 200:
            base_grade = 'A-'
        elif response_time < 300:
            base_grade = 'B+'
        elif response_time < 500:
            base_grade = 'B'
        elif response_time < 750:
            base_grade = 'B-'
        elif response_time < 1000:
            base_grade = 'C+'
        elif response_time < 1500:
            base_grade = 'C'
        elif response_time < 2000:
            base_grade = 'C-'
        elif response_time < 3000:
            base_grade = 'D'
        else:
            base_grade = 'F'
        
        # Grade adjustments based on other factors
        grade_values = {
            'A+': 97, 'A': 93, 'A-': 90,
            'B+': 87, 'B': 83, 'B-': 80,
            'C+': 77, 'C': 73, 'C-': 70,
            'D': 65, 'F': 50
        }
        
        current_score = grade_values.get(base_grade, 50)
        
        # Adjust for HTTP status codes
        if 200 <= status_code < 300:
            pass  # No adjustment for success codes
        elif 300 <= status_code < 400:
            current_score -= 5  # Minor penalty for redirects
        elif 400 <= status_code < 500:
            current_score -= 15  # Penalty for client errors
        elif status_code >= 500:
            current_score -= 25  # Heavy penalty for server errors
        
        # Bonus for security headers
        if has_security_headers:
            current_score += 2
        
        # Bonus for cache headers
        if has_cache_headers:
            current_score += 1
        
        # Convert back to letter grade
        if current_score >= 95:
            return 'A+'
        elif current_score >= 90:
            return 'A'
        elif current_score >= 87:
            return 'A-'
        elif current_score >= 83:
            return 'B+'
        elif current_score >= 80:
            return 'B'
        elif current_score >= 77:
            return 'B-'
        elif current_score >= 73:
            return 'C+'
        elif current_score >= 70:
            return 'C'
        elif current_score >= 67:
            return 'C-'
        elif current_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _calculate_overall_grade(self, grades, successful, total):
        """Calculate overall API performance grade."""
        if total == 0:
            return 'F'
        
        success_rate = successful / total
        grade_scores = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
        avg_grade_score = sum(grade_scores.get(g, 1) for g in grades) / len(grades) if grades else 1
        
        # Weight by success rate
        final_score = avg_grade_score * success_rate
        
        if final_score >= 4.5:
            return 'A'
        elif final_score >= 3.5:
            return 'B'
        elif final_score >= 2.5:
            return 'C'
        elif final_score >= 1.5:
            return 'D'
        else:
            return 'F'
    
    def _calculate_reliability_score(self, results):
        """Calculate comprehensive API reliability score based on multiple factors."""
        if not results:
            return 0
        
        # Basic success rate (40% weight)
        success_rate = sum(1 for r in results if r['success']) / len(results)
        success_score = success_rate * 40
        
        # Response time consistency (25% weight)
        response_times = [r['response_time'] for r in results if r['response_time'] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            std_dev = (sum((x - avg_time) ** 2 for x in response_times) / len(response_times)) ** 0.5
            cv = (std_dev / avg_time) if avg_time > 0 else 1
            
            # Lower coefficient of variation = higher consistency score
            consistency_score = max(0, 25 - (cv * 25))
        else:
            consistency_score = 0
        
        # Performance score (20% weight)
        if response_times:
            # Score based on average response time
            if avg_time < 100:
                perf_score = 20
            elif avg_time < 300:
                perf_score = 18
            elif avg_time < 500:
                perf_score = 15
            elif avg_time < 1000:
                perf_score = 12
            elif avg_time < 2000:
                perf_score = 8
            elif avg_time < 5000:
                perf_score = 4
            else:
                perf_score = 1
        else:
            perf_score = 0
        
        # Error distribution score (10% weight)
        status_codes = [r.get('status_code', 0) for r in results if r.get('status_code')]
        if status_codes:
            server_errors = sum(1 for code in status_codes if code >= 500)
            client_errors = sum(1 for code in status_codes if 400 <= code < 500)
            
            error_penalty = (server_errors * 2 + client_errors) / len(status_codes) * 10
            error_score = max(0, 10 - error_penalty)
        else:
            error_score = 5  # Neutral score if no status codes available
        
        # Security and best practices score (5% weight)
        security_features = sum(1 for r in results if r.get('has_security_headers', False))
        cache_features = sum(1 for r in results if r.get('has_cache_headers', False))
        
        security_score = (security_features + cache_features) / (len(results) * 2) * 5
        
        # Calculate total reliability score
        total_score = success_score + consistency_score + perf_score + error_score + security_score
        
        return max(0, min(100, round(total_score, 1)))
    
    def _analyze_security(self, endpoint_results: List[Dict]) -> Dict:
        """Enhanced security analysis."""
        https_usage = any(r['url'].startswith('https://') for r in endpoint_results)
        status_codes = [r['status_code'] for r in endpoint_results if r['status_code']]
        
        security_issues = []
        security_score = 100
        
        if not https_usage:
            security_issues.append("Critical: API not served over HTTPS")
            security_score -= 50
        
        # Check for information disclosure
        if any(code in [500, 502, 503] for code in status_codes):
            security_issues.append("Warning: Server errors detected - may expose internal information")
            security_score -= 10
        
        # Check for proper error handling
        if 404 not in status_codes and len(endpoint_results) > 5:
            security_issues.append("Info: No 404 responses - endpoint enumeration might be possible")
            security_score -= 5
        
        return {
            'https_enabled': https_usage,
            'security_score': max(0, security_score),
            'security_issues': security_issues,
            'recommendations': self._get_security_recommendations(security_issues)
        }
    
    def _get_security_recommendations(self, issues):
        """Generate security recommendations based on identified issues."""
        recommendations = []
        for issue in issues:
            if "HTTPS" in issue:
                recommendations.append("Enable HTTPS/TLS encryption for all API endpoints")
            elif "Server errors" in issue:
                recommendations.append("Implement proper error handling to avoid information disclosure")
            elif "404" in issue:
                recommendations.append("Implement consistent error responses for non-existent endpoints")
        return recommendations

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Simple check to validate a URL."""
        return url.startswith("http://") or url.startswith("https://")


# --- Example Usage ---
if __name__ == '__main__':
    # Using a public test API
    BASE_URL = "https://jsonplaceholder.typicode.com"
    
    # ADDED: You can define specific endpoints with test data and schemas
    custom_endpoints = [
        {
            "path": "/todos/1",
            "method": "GET",
            "description": "Get a single todo item",
            "expected_schema": {
                "type": "object",
                "properties": {
                    "userId": {"type": "number"},
                    "id": {"type": "number"},
                    "title": {"type": "string"},
                    "completed": {"type": "boolean"}
                },
                "required": ["userId", "id", "title", "completed"]
            }
        },
        {
            "path": "/posts",
            "method": "POST",
            "description": "Create a new post",
            # ADDED: Providing realistic test data for the POST request
            "data": {
                "title": "foo",
                "body": "bar",
                "userId": 1
            }
        },
        {
            "path": "/invalid-endpoint",
            "method": "GET",
            "description": "A test for a 404 Not Found"
        }
    ]

    tester = APITester(max_workers=10)
    
    # Option 1: Let the tester discover endpoints automatically
    print("--- RUN 1: Automatic Discovery ---")
    auto_results = tester.test_endpoints(base_url=BASE_URL)
    # Use json.dumps for pretty printing the final report
    if auto_results:
        print(json.dumps(auto_results, indent=2))
    
    print("\n" + "="*50 + "\n")

    # Option 2: Provide a custom list of endpoints to test
    print("--- RUN 2: Custom Endpoints Test ---")
    custom_results = tester.test_endpoints(base_url=BASE_URL, endpoints=custom_endpoints)
    if custom_results:
        print(json.dumps(custom_results, indent=2))
