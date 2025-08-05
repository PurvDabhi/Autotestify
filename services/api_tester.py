import requests
import time
import json
import jsonschema # Now used for schema validation
from urllib.parse import urljoin
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed # ADDED: For concurrency

class APITester:
    def __init__(self, max_workers: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AutoTestify-API-Tester/2.0'
        })
        # ADDED: ThreadPoolExecutor for running tests in parallel
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

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
        """Aggregates individual endpoint results into a final report."""
        successful_tests = sum(1 for r in results if r['success'])
        failed_tests = len(results) - successful_tests
        
        status_code_dist = {}
        content_type_dist = {}
        response_times = []

        for r in results:
            response_times.append(r['response_time'])
            # Update status code distribution
            status_code = r['status_code'] if r['status_code'] else 'N/A'
            status_code_dist[status_code] = status_code_dist.get(status_code, 0) + 1
            # Update content type analysis
            content_type = r.get('content_type', 'unknown').split(';')[0]
            content_type_dist[content_type] = content_type_dist.get(content_type, 0) + 1

        # Calculate performance metrics
        perf_metrics = {}
        if response_times:
            fastest_res = min(results, key=lambda r: r['response_time'])
            slowest_res = max(results, key=lambda r: r['response_time'])
            perf_metrics = {
                'average_response_time': round(sum(response_times) / len(response_times), 2),
                'fastest_endpoint': {'endpoint': fastest_res['endpoint'], 'time_ms': fastest_res['response_time']},
                'slowest_endpoint': {'endpoint': slowest_res['endpoint'], 'time_ms': slowest_res['response_time']}
            }
        
        final_report = {
            'base_url': base_url,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration_seconds': round(duration, 2),
            'total_endpoints_tested': len(results),
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'performance_metrics': perf_metrics,
            'status_code_distribution': status_code_dist,
            'content_type_analysis': content_type_dist,
            'security_analysis': self._analyze_security(results),
            'endpoint_results': results,
        }
        return final_report

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
        """Test a single API endpoint."""
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
            'schema_valid': 'N/A', # ADDED
            'error': None,
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
            
            # Main success criteria: 2xx status code
            result['success'] = 200 <= response.status_code < 300
            
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

    def _analyze_security(self, endpoint_results: List[Dict]) -> Dict:
        """Analyze overall security based on endpoint results."""
        # This method's logic is mostly fine, no major changes needed.
        # It's a good-faith effort at a basic security check.
        https_usage = any(r['url'].startswith('https://') for r in endpoint_results)
        recommendations = []
        if not https_usage:
            recommendations.append("Critical: API is not served over HTTPS. All traffic is insecure.")
        
        return {
            'https_enabled': https_usage,
            'recommendations': recommendations
        }

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
