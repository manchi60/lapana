from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ===== MODELS =====

class Cliente(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    telefono: str
    email: Optional[str] = None
    direccion: Optional[str] = None
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)

class ClienteCreate(BaseModel):
    nombre: str
    telefono: str
    email: Optional[str] = None
    direccion: Optional[str] = None

class Producto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    precio: float
    categoria: str
    descripcion: Optional[str] = None
    disponible: bool = True

class ProductoCreate(BaseModel):
    nombre: str
    precio: float
    categoria: str
    descripcion: Optional[str] = None
    disponible: bool = True

class DetalleProducto(BaseModel):
    producto_id: str
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float

class Pedido(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cliente_id: str
    nombre_cliente: str
    fecha_pedido: datetime = Field(default_factory=datetime.utcnow)
    fecha_entrega_estimada: datetime
    estado: str = "pendiente"  # pendiente, en_proceso, completado, cancelado
    productos: List[DetalleProducto]
    total: float

class PedidoCreate(BaseModel):
    cliente_id: str
    fecha_entrega_estimada: str  # Cambiar a string para recibir desde frontend
    productos: List[dict]  # {producto_id: str, cantidad: int}

# ===== ENDPOINTS CLIENTES =====

@api_router.post("/clientes", response_model=Cliente)
async def crear_cliente(cliente: ClienteCreate):
    cliente_dict = cliente.dict()
    cliente_obj = Cliente(**cliente_dict)
    await db.clientes.insert_one(cliente_obj.dict())
    return cliente_obj

@api_router.get("/clientes", response_model=List[Cliente])
async def obtener_clientes():
    clientes = await db.clientes.find().to_list(1000)
    return [Cliente(**cliente) for cliente in clientes]

@api_router.get("/clientes/{cliente_id}", response_model=Cliente)
async def obtener_cliente(cliente_id: str):
    cliente = await db.clientes.find_one({"id": cliente_id})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return Cliente(**cliente)

@api_router.put("/clientes/{cliente_id}", response_model=Cliente)
async def actualizar_cliente(cliente_id: str, cliente: ClienteCreate):
    cliente_existente = await db.clientes.find_one({"id": cliente_id})
    if not cliente_existente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    cliente_dict = cliente.dict()
    await db.clientes.update_one({"id": cliente_id}, {"$set": cliente_dict})
    
    cliente_actualizado = await db.clientes.find_one({"id": cliente_id})
    return Cliente(**cliente_actualizado)

@api_router.delete("/clientes/{cliente_id}")
async def eliminar_cliente(cliente_id: str):
    resultado = await db.clientes.delete_one({"id": cliente_id})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado exitosamente"}

# ===== ENDPOINTS PRODUCTOS =====

@api_router.post("/productos", response_model=Producto)
async def crear_producto(producto: ProductoCreate):
    producto_dict = producto.dict()
    producto_obj = Producto(**producto_dict)
    await db.productos.insert_one(producto_obj.dict())
    return producto_obj

@api_router.get("/productos", response_model=List[Producto])
async def obtener_productos():
    productos = await db.productos.find().to_list(1000)
    return [Producto(**producto) for producto in productos]

@api_router.get("/productos/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: str):
    producto = await db.productos.find_one({"id": producto_id})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return Producto(**producto)

@api_router.put("/productos/{producto_id}", response_model=Producto)
async def actualizar_producto(producto_id: str, producto: ProductoCreate):
    producto_existente = await db.productos.find_one({"id": producto_id})
    if not producto_existente:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    producto_dict = producto.dict()
    await db.productos.update_one({"id": producto_id}, {"$set": producto_dict})
    
    producto_actualizado = await db.productos.find_one({"id": producto_id})
    return Producto(**producto_actualizado)

@api_router.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: str):
    resultado = await db.productos.delete_one({"id": producto_id})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"mensaje": "Producto eliminado exitosamente"}

# ===== ENDPOINTS PEDIDOS =====

@api_router.post("/pedidos", response_model=Pedido)
async def crear_pedido(pedido: PedidoCreate):
    # Obtener información del cliente
    cliente = await db.clientes.find_one({"id": pedido.cliente_id})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Convertir fecha string a datetime
    try:
        fecha_entrega = datetime.strptime(pedido.fecha_entrega_estimada, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Procesar productos del pedido
    productos_detalle = []
    total = 0
    
    for item in pedido.productos:
        producto = await db.productos.find_one({"id": item["producto_id"]})
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {item['producto_id']} no encontrado")
        
        subtotal = producto["precio"] * item["cantidad"]
        detalle = DetalleProducto(
            producto_id=item["producto_id"],
            nombre_producto=producto["nombre"],
            cantidad=item["cantidad"],
            precio_unitario=producto["precio"],
            subtotal=subtotal
        )
        productos_detalle.append(detalle)
        total += subtotal
    
    # Crear el pedido
    pedido_obj = Pedido(
        cliente_id=pedido.cliente_id,
        nombre_cliente=cliente["nombre"],
        fecha_entrega_estimada=fecha_entrega,
        productos=productos_detalle,
        total=total
    )
    
    await db.pedidos.insert_one(pedido_obj.dict())
    return pedido_obj

@api_router.get("/pedidos", response_model=List[Pedido])
async def obtener_pedidos():
    pedidos = await db.pedidos.find().sort("fecha_pedido", -1).to_list(1000)
    return [Pedido(**pedido) for pedido in pedidos]

@api_router.get("/pedidos/{pedido_id}", response_model=Pedido)
async def obtener_pedido(pedido_id: str):
    pedido = await db.pedidos.find_one({"id": pedido_id})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return Pedido(**pedido)

@api_router.put("/pedidos/{pedido_id}/estado")
async def actualizar_estado_pedido(pedido_id: str, estado: dict):
    pedido = await db.pedidos.find_one({"id": pedido_id})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    estados_validos = ["pendiente", "en_proceso", "completado", "cancelado"]
    if estado["estado"] not in estados_validos:
        raise HTTPException(status_code=400, detail="Estado no válido")
    
    await db.pedidos.update_one({"id": pedido_id}, {"$set": {"estado": estado["estado"]}})
    return {"mensaje": "Estado actualizado exitosamente"}

@api_router.delete("/pedidos/{pedido_id}")
async def eliminar_pedido(pedido_id: str):
    resultado = await db.pedidos.delete_one({"id": pedido_id})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"mensaje": "Pedido eliminado exitosamente"}

# ===== ENDPOINTS DASHBOARD =====

@api_router.get("/dashboard/estadisticas")
async def obtener_estadisticas():
    total_clientes = await db.clientes.count_documents({})
    total_productos = await db.productos.count_documents({})
    total_pedidos = await db.pedidos.count_documents({})
    
    # Pedidos por estado
    pedidos_pendientes = await db.pedidos.count_documents({"estado": "pendiente"})
    pedidos_en_proceso = await db.pedidos.count_documents({"estado": "en_proceso"})
    pedidos_completados = await db.pedidos.count_documents({"estado": "completado"})
    
    # Calcular ingresos totales
    pedidos_completados_datos = await db.pedidos.find({"estado": "completado"}).to_list(1000)
    ingresos_totales = sum(pedido["total"] for pedido in pedidos_completados_datos)
    
    return {
        "total_clientes": total_clientes,
        "total_productos": total_productos,
        "total_pedidos": total_pedidos,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_en_proceso": pedidos_en_proceso,
        "pedidos_completados": pedidos_completados,
        "ingresos_totales": ingresos_totales
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()