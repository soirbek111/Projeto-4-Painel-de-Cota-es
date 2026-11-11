from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from django.urls import reverse

from .models import RegistroCotacao


def resposta_falsa(json_data, status=200):
    r = MagicMock()
    r.json.return_value = json_data
    if status >= 400:
        r.raise_for_status.side_effect = requests.exceptions.HTTPError(f'HTTP {status}')
    return r


class ConsultarCotacaoTest(TestCase):

    @patch('painel.views.requests.get')
    def test_sucesso_salva_registro(self, get):
        get.return_value = resposta_falsa({'USDBRL': {'bid': '5.1234'}})
        r = self.client.get(reverse('consultar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Cotação registrada')
        reg = RegistroCotacao.objects.get()
        self.assertEqual(reg.valor, Decimal('5.1234'))
        self.assertEqual(get.call_args.kwargs['timeout'], 5)

    @patch('painel.views.requests.get', side_effect=requests.exceptions.Timeout())
    def test_timeout_nao_quebra_a_pagina(self, get):
        r = self.client.get(reverse('consultar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Não foi possível consultar')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    @patch('painel.views.requests.get')
    def test_erro_http_500_da_api(self, get):
        get.return_value = resposta_falsa({}, status=500)
        r = self.client.get(reverse('consultar'))
        self.assertContains(r, 'Não foi possível consultar')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    @patch('painel.views.requests.get')
    def test_formato_inesperado(self, get):
        get.return_value = resposta_falsa({'outra': 'coisa'})
        r = self.client.get(reverse('consultar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'formato inesperado')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    def test_template_usa_fetch_e_catch(self):
        with patch('painel.views.requests.get', side_effect=requests.exceptions.ConnectionError()):
            r = self.client.get(reverse('consultar'))
        self.assertContains(r, "fetch('/api/historico/')")
        self.assertContains(r, '.catch(')


class HistoricoAPITest(TestCase):

    def test_ordem_do_mais_recente_ao_mais_antigo(self):
        a = RegistroCotacao.objects.create(valor=Decimal('5.0000'))
        b = RegistroCotacao.objects.create(valor=Decimal('5.1000'))
        c = RegistroCotacao.objects.create(valor=Decimal('5.2000'))
        r = self.client.get(reverse('api-historico'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x['id'] for x in r.json()], [c.id, b.id, a.id])

    def test_somente_leitura(self):
        r = self.client.post(reverse('api-historico'), {'valor': '1'})
        self.assertEqual(r.status_code, 405)

    def test_lista_vazia(self):
        self.assertEqual(self.client.get(reverse('api-historico')).json(), [])