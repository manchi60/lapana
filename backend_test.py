#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Panadería Management System
Tests all CRUD operations for clientes, productos, pedidos, and dashboard statistics
"""

import requests
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

class PanaderiaAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'clientes': [],
            'productos': [],
            'pedidos': []
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"

            if response.status_code in [200, 201]:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, f"Status {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"

    def test_clientes_crud(self):
        """Test all cliente CRUD operations"""
        print("\n🧪 Testing CLIENTES CRUD Operations...")
        
        # Test 1: Create cliente
        cliente_data = {
            "nombre": "Juan Pérez",
            "telefono": "123456789",
            "email": "juan@example.com",
            "direccion": "Calle Principal 123"
        }
        
        success, response = self.make_request('POST', 'clientes', cliente_data)
        if success and 'id' in response:
            cliente_id = response['id']
            self.created_resources['clientes'].append(cliente_id)
            self.log_test("Create Cliente", True, f"ID: {cliente_id}")
        else:
            self.log_test("Create Cliente", False, str(response))
            return False

        # Test 2: Get all clientes
        success, response = self.make_request('GET', 'clientes')
        if success and isinstance(response, list):
            self.log_test("Get All Clientes", True, f"Found {len(response)} clientes")
        else:
            self.log_test("Get All Clientes", False, str(response))

        # Test 3: Get specific cliente
        success, response = self.make_request('GET', f'clientes/{cliente_id}')
        if success and response.get('id') == cliente_id:
            self.log_test("Get Specific Cliente", True, f"Retrieved cliente: {response.get('nombre')}")
        else:
            self.log_test("Get Specific Cliente", False, str(response))

        # Test 4: Update cliente
        update_data = {
            "nombre": "Juan Pérez Actualizado",
            "telefono": "987654321",
            "email": "juan.updated@example.com",
            "direccion": "Nueva Dirección 456"
        }
        success, response = self.make_request('PUT', f'clientes/{cliente_id}', update_data)
        if success and response.get('nombre') == update_data['nombre']:
            self.log_test("Update Cliente", True, "Cliente updated successfully")
        else:
            self.log_test("Update Cliente", False, str(response))

        return True

    def test_productos_crud(self):
        """Test all producto CRUD operations"""
        print("\n🥖 Testing PRODUCTOS CRUD Operations...")
        
        # Test categories
        categorias = ["Pan", "Pastelería", "Bollería", "Repostería", "Otros"]
        
        for i, categoria in enumerate(categorias):
            producto_data = {
                "nombre": f"Producto {categoria} {i+1}",
                "precio": round(2.50 + i * 0.75, 2),
                "categoria": categoria,
                "descripcion": f"Delicioso {categoria.lower()} artesanal",
                "disponible": True
            }
            
            success, response = self.make_request('POST', 'productos', producto_data)
            if success and 'id' in response:
                producto_id = response['id']
                self.created_resources['productos'].append(producto_id)
                self.log_test(f"Create Producto ({categoria})", True, f"ID: {producto_id}, Precio: €{producto_data['precio']}")
            else:
                self.log_test(f"Create Producto ({categoria})", False, str(response))

        # Test get all productos
        success, response = self.make_request('GET', 'productos')
        if success and isinstance(response, list) and len(response) >= len(categorias):
            self.log_test("Get All Productos", True, f"Found {len(response)} productos")
        else:
            self.log_test("Get All Productos", False, str(response))

        # Test get specific producto
        if self.created_resources['productos']:
            producto_id = self.created_resources['productos'][0]
            success, response = self.make_request('GET', f'productos/{producto_id}')
            if success and response.get('id') == producto_id:
                self.log_test("Get Specific Producto", True, f"Retrieved: {response.get('nombre')}")
            else:
                self.log_test("Get Specific Producto", False, str(response))

        return True

    def test_pedidos_crud(self):
        """Test all pedido CRUD operations"""
        print("\n📦 Testing PEDIDOS CRUD Operations...")
        
        if not self.created_resources['clientes'] or not self.created_resources['productos']:
            self.log_test("Pedidos Prerequisites", False, "Need clientes and productos first")
            return False

        # Create pedido
        cliente_id = self.created_resources['clientes'][0]
        productos_ids = self.created_resources['productos'][:3]  # Use first 3 products
        
        pedido_data = {
            "cliente_id": cliente_id,
            "fecha_entrega_estimada": (date.today() + timedelta(days=2)).isoformat(),
            "productos": [
                {"producto_id": productos_ids[0], "cantidad": 2},
                {"producto_id": productos_ids[1], "cantidad": 1},
                {"producto_id": productos_ids[2], "cantidad": 3}
            ]
        }
        
        success, response = self.make_request('POST', 'pedidos', pedido_data)
        if success and 'id' in response:
            pedido_id = response['id']
            self.created_resources['pedidos'].append(pedido_id)
            total = response.get('total', 0)
            self.log_test("Create Pedido", True, f"ID: {pedido_id}, Total: €{total}")
        else:
            self.log_test("Create Pedido", False, str(response))
            return False

        # Test get all pedidos
        success, response = self.make_request('GET', 'pedidos')
        if success and isinstance(response, list):
            self.log_test("Get All Pedidos", True, f"Found {len(response)} pedidos")
        else:
            self.log_test("Get All Pedidos", False, str(response))

        # Test get specific pedido
        success, response = self.make_request('GET', f'pedidos/{pedido_id}')
        if success and response.get('id') == pedido_id:
            self.log_test("Get Specific Pedido", True, f"Estado: {response.get('estado')}")
        else:
            self.log_test("Get Specific Pedido", False, str(response))

        # Test update pedido status
        estados = ["en_proceso", "completado"]
        for estado in estados:
            success, response = self.make_request('PUT', f'pedidos/{pedido_id}/estado', {"estado": estado})
            if success:
                self.log_test(f"Update Pedido Status to {estado}", True, "Status updated")
            else:
                self.log_test(f"Update Pedido Status to {estado}", False, str(response))

        return True

    def test_dashboard_statistics(self):
        """Test dashboard statistics endpoint"""
        print("\n📊 Testing DASHBOARD Statistics...")
        
        success, response = self.make_request('GET', 'dashboard/estadisticas')
        if success and isinstance(response, dict):
            required_fields = [
                'total_clientes', 'total_productos', 'total_pedidos',
                'pedidos_pendientes', 'pedidos_en_proceso', 'pedidos_completados',
                'ingresos_totales'
            ]
            
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                stats = {
                    'Clientes': response['total_clientes'],
                    'Productos': response['total_productos'],
                    'Pedidos': response['total_pedidos'],
                    'Pendientes': response['pedidos_pendientes'],
                    'En Proceso': response['pedidos_en_proceso'],
                    'Completados': response['pedidos_completados'],
                    'Ingresos': f"€{response['ingresos_totales']}"
                }
                stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items()])
                self.log_test("Dashboard Statistics", True, stats_str)
            else:
                self.log_test("Dashboard Statistics", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Dashboard Statistics", False, str(response))

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n🚫 Testing ERROR Handling...")
        
        # Test invalid cliente ID
        success, response = self.make_request('GET', 'clientes/invalid-id')
        if not success and "404" in str(response):
            self.log_test("Invalid Cliente ID", True, "Correctly returned 404")
        else:
            self.log_test("Invalid Cliente ID", False, "Should return 404")

        # Test invalid producto ID
        success, response = self.make_request('GET', 'productos/invalid-id')
        if not success and "404" in str(response):
            self.log_test("Invalid Producto ID", True, "Correctly returned 404")
        else:
            self.log_test("Invalid Producto ID", False, "Should return 404")

        # Test invalid pedido status
        if self.created_resources['pedidos']:
            pedido_id = self.created_resources['pedidos'][0]
            success, response = self.make_request('PUT', f'pedidos/{pedido_id}/estado', {"estado": "invalid_status"})
            if not success and "400" in str(response):
                self.log_test("Invalid Pedido Status", True, "Correctly returned 400")
            else:
                self.log_test("Invalid Pedido Status", False, "Should return 400")

    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete pedidos first (they reference clientes and productos)
        for pedido_id in self.created_resources['pedidos']:
            success, _ = self.make_request('DELETE', f'pedidos/{pedido_id}')
            if success:
                print(f"  ✅ Deleted pedido {pedido_id}")
            else:
                print(f"  ❌ Failed to delete pedido {pedido_id}")

        # Delete productos
        for producto_id in self.created_resources['productos']:
            success, _ = self.make_request('DELETE', f'productos/{producto_id}')
            if success:
                print(f"  ✅ Deleted producto {producto_id}")
            else:
                print(f"  ❌ Failed to delete producto {producto_id}")

        # Delete clientes
        for cliente_id in self.created_resources['clientes']:
            success, _ = self.make_request('DELETE', f'clientes/{cliente_id}')
            if success:
                print(f"  ✅ Deleted cliente {cliente_id}")
            else:
                print(f"  ❌ Failed to delete cliente {cliente_id}")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Panadería API Testing...")
        print(f"📍 Testing against: {self.base_url}")
        
        try:
            # Test basic connectivity
            success, response = self.make_request('GET', 'dashboard/estadisticas')
            if not success:
                print(f"❌ Cannot connect to API at {self.api_url}")
                print(f"Error: {response}")
                return False

            print("✅ API connectivity confirmed")
            
            # Run all test suites
            self.test_clientes_crud()
            self.test_productos_crud()
            self.test_pedidos_crud()
            self.test_dashboard_statistics()
            self.test_error_handling()
            
            return True
            
        except Exception as e:
            print(f"❌ Unexpected error during testing: {str(e)}")
            return False
        
        finally:
            # Always try to cleanup
            self.cleanup_resources()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        print("="*60)

def main():
    """Main test execution"""
    # Use the public URL from frontend/.env
    base_url = "https://1c13e083-113d-41e4-a418-c490820e2cff.preview.emergentagent.com"
    
    tester = PanaderiaAPITester(base_url)
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        return 0 if success and tester.tests_passed == tester.tests_run else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())