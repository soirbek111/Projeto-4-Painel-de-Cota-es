from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.shortcuts import render
from rest_framework import generics

from .models import RegistroCotacao
from .serializers import RegistroCotacaoSerializer


def consultar_cotacao(request):
    contexto = {}
    try:
        # timeout evita que a página fique esperando para sempre
        resposta = requests.get(settings.COTACAO_URL, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        valor = Decimal(dados['USDBRL']['bid'])
        registro = RegistroCotacao.objects.create(valor=valor)
        contexto = {'sucesso': True, 'registro': registro}
    except requests.exceptions.RequestException:
        contexto = {'erro': 'Não foi possível consultar a cotação agora. Tente novamente em instantes.'}
    except (ValueError, KeyError, TypeError, InvalidOperation):
        # A API respondeu, mas em formato inesperado.
        contexto = {'erro': 'A API externa respondeu em um formato inesperado.'}
    return render(request, 'painel/consultar.html', contexto)


class HistoricoCotacaoView(generics.ListAPIView):
    """Somente leitura: histórico do mais recente para o mais antigo."""
    serializer_class = RegistroCotacaoSerializer

    def get_queryset(self):
        return RegistroCotacao.objects.order_by('-data_hora_consulta', '-id')