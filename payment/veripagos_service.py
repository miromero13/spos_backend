import os
import requests
import json
import base64
from django.conf import settings
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class VeripagosService:
    def __init__(self):
        # self.username = os.getenv('VERIPAGOS_USERNAME')
        self.username = "Sauterdev"
        # self.password = os.getenv('VERIPAGOS_PASSWORD')
        self.password = "ec%Nb1Xaox"
        # self.secret_key = os.getenv('VERIPAGOS_SECRET_KEY')
        self.secret_key = "2a4420b4-407f-41ce-85c0-b02da6fb5a2d"
        self.base_url = "https://veripagos.com/api/bcp"
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        if not all([self.username, self.password, self.secret_key]):
            raise ValueError("Veripagos credentials not configured properly")

    def generate_qr(self, amount, extra_information=None, validity="1/00:00", single_use=True, detail=None):
        """
        Genera un código QR para pago
        
        Args:
            amount (float): Monto a cobrar en Bs
            extra_information (dict): Información adicional (opcional)
            validity (str): Vigencia del QR en formato "día/hora:minuto"
            single_use (bool): Si el QR es para un único pago
            detail (str): Detalle personalizado del pago
        
        Returns:
            dict: Respuesta con el QR generado o error
        """
        if extra_information is None:
            extra_information = {}
            
        data = {
            "secret_key": self.secret_key,
            "monto": float(amount),
            "data": extra_information,
            "vigencia": validity,
            "uso_unico": single_use
        }
        
        if detail:
            data["detalle"] = detail
            
        return self._send_request('POST', '/generar-qr', data)

    def verify_qr_status(self, movement_id):
        """
        Verifica el estado de un QR de pago
        
        Args:
            movement_id (int): ID del movimiento generado al crear el QR
            
        Returns:
            dict: Estado del pago
        """
        data = {
            "secret_key": self.secret_key,
            "movimiento_id": str(movement_id)
        }
        
        return self._send_request('POST', '/verificar-estado-qr', data)

    def _send_request(self, method, path, data=None):
        """
        Envía petición HTTP a la API de Veripagos
        
        Args:
            method (str): Método HTTP (GET, POST, etc.)
            path (str): Ruta del endpoint
            data (dict): Datos a enviar
            
        Returns:
            dict: Respuesta formateada
        """
        url = f"{self.base_url}{path}"
        
        try:
            auth = (self.username, self.password)
            
            if method.upper() == 'POST':
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    auth=auth,
                    timeout=30
                )
            else:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=data,
                    auth=auth,
                    timeout=30
                )
            
            logger.debug(f"Veripagos response: {response.text}")
            
            return self._handle_response(response)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a Veripagos: {str(e)}")
            return {
                'status': 500,
                'message': f'Error de conexión: {str(e)}',
                'data': None
            }

    def _handle_response(self, response):
        """
        Maneja la respuesta de la API de Veripagos
        
        Args:
            response: Respuesta HTTP
            
        Returns:
            dict: Respuesta formateada
        """
        if response.status_code != 200:
            return {
                'status': response.status_code,
                'message': 'Error en la petición a Veripagos',
                'data': None
            }
        
        try:
            json_response = response.json()
            
            if json_response.get('Codigo') == 1:
                return {
                    'status': 400,
                    'message': json_response.get('Mensaje', 'Error desconocido'),
                    'data': None
                }
            else:
                return {
                    'status': 200,
                    'message': json_response.get('Mensaje', 'Éxito'),
                    'data': json_response.get('Data')
                }
                
        except json.JSONDecodeError:
            return {
                'status': 500,
                'message': 'Respuesta inválida de Veripagos',
                'data': None
            }

    @staticmethod
    def format_qr_image(qr_base64):
        """
        Formatea la imagen QR para mostrar en frontend
        
        Args:
            qr_base64 (str): QR en base64
            
        Returns:
            str: QR formateado para mostrar
        """
        if qr_base64:
            return f"data:image/png;base64,{qr_base64}"
        return None
