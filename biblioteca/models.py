from django.db import models


class Autor(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'autores'

    def __str__(self):
        return self.nome


class Livro(models.Model):
    titulo = models.CharField(max_length=255)
    autor = models.ForeignKey(
        Autor, on_delete=models.PROTECT, related_name='livros'
    )
    ano_publicacao = models.PositiveIntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    chave_open_library = models.CharField(
        max_length=50, unique=True, null=True, blank=True
    )
    numero_paginas = models.PositiveIntegerField(null=True, blank=True)
    quantidade_exemplares = models.PositiveIntegerField(default=1)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return f'{self.titulo} ({self.autor})'

    @property
    def exemplares_disponiveis(self):
        ativos = self.emprestimos.filter(status=Emprestimo.STATUS_ATIVO).count()
        return self.quantidade_exemplares - ativos


class Emprestimo(models.Model):
    STATUS_ATIVO = 'ATIVO'
    STATUS_DEVOLVIDO = 'DEVOLVIDO'
    STATUS_CHOICES = [
        (STATUS_ATIVO, 'Ativo'),
        (STATUS_DEVOLVIDO, 'Devolvido'),
    ]

    livro = models.ForeignKey(
        Livro, on_delete=models.PROTECT, related_name='emprestimos'
    )
    nome_leitor = models.CharField(max_length=150)
    data_emprestimo = models.DateField(auto_now_add=True)
    data_prevista_devolucao = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_ATIVO
    )

    class Meta:
        ordering = ['-data_emprestimo', '-id']

    def __str__(self):
        return f'{self.livro.titulo} -> {self.nome_leitor} ({self.status})'


class RegistroBusca(models.Model):
    termo = models.CharField(max_length=200)
    quantidade_resultados = models.PositiveIntegerField(default=0)
    data_hora_consulta = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora_consulta', '-id']

    def __str__(self):
        return f'"{self.termo}" -> {self.quantidade_resultados} resultado(s)'