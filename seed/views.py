from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from user.models import User

class SeedView(APIView):    

    def get(self, request):
        if User.objects.filter(email='admin@mail.com').exists():
            return Response({
                "status": False,
                "message": "⚠️ El usuario administrador ya existe."
            })

        if User.objects.filter(email='cashier@mail.com').exists():
            return Response({
                "status": False,
                "message": "⚠️ El usuario cajero ya existe."
            })
        
        User.objects.create_superuser(
            ci='0000001',
            email='admin@mail.com',
            name='Admin Inicial',
            phone='11111111',
            password='admin123',
            role='administrator'
        )

        User.objects.create_superuser(
            ci='0000002',
            email='cashier@mail.com',
            name='Cajero Inicial',
            phone='22222222',
            password='cashier123',
            role='cashier'
        )
        return Response({
            "status": True,
            "message": "✅ Seeders ejecutados exitosamente."
        })
