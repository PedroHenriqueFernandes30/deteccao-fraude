"""Exemplos conhecidos para conferir as regras sem depender do Kafka."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from banco import abrir_banco, salvar_transacao


class RegrasTest(unittest.TestCase):
    def setUp(self):
        self.banco = abrir_banco(":memory:")
        self.inicio = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def tearDown(self):
        self.banco.close()

    def transacao(self, segundos=0, valor=100, cidade="Recife", cliente="A"):
        return {
            "id": str(uuid4()), "cliente_id": cliente, "amount": valor,
            "cidade": cidade,
            "data_hora": (self.inicio + timedelta(seconds=segundos)).isoformat(),
        }

    def salvar(self, **opcoes):
        return salvar_transacao(self.banco, self.transacao(**opcoes))[0]

    def test_normal_tambem_e_salva(self):
        self.assertEqual(self.salvar(), [])
        self.assertEqual(self.banco.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0], 1)

    def test_valor_abaixo_do_limite(self):
        self.assertNotIn("ALTO_VALOR", self.salvar(valor=9999.99))

    def test_valor_no_limite(self):
        self.assertIn("ALTO_VALOR", self.salvar(valor=10000))

    def test_quarta_transacao(self):
        for segundo in (0, 10, 20):
            self.assertNotIn("TEMPO_60s", self.salvar(segundos=segundo))
        self.assertIn("TEMPO_60s", self.salvar(segundos=59))

    def test_exatamente_60_segundos_nao_conta(self):
        for segundo in (0, 10, 20):
            self.salvar(segundos=segundo)
        self.assertNotIn("TEMPO_60s", self.salvar(segundos=60))

    def test_clientes_distintos_nao_somam(self):
        for segundo in (0, 10, 20):
            self.salvar(segundos=segundo)
        self.assertEqual(self.salvar(segundos=30, cliente="B", cidade="Curitiba"), [])

    def test_geo_dentro_de_dez_minutos(self):
        self.salvar()
        self.assertIn("GEO_10m", self.salvar(segundos=300, cidade="Curitiba"))

    def test_geo_exatamente_dez_minutos(self):
        self.salvar()
        self.assertIn("GEO_10m", self.salvar(segundos=600, cidade="Curitiba"))

    def test_geo_fora_de_dez_minutos(self):
        self.salvar()
        self.assertNotIn("GEO_10m", self.salvar(segundos=601, cidade="Curitiba"))

    def test_mesma_cidade_nao_dispara_geo(self):
        self.salvar()
        self.assertNotIn("GEO_10m", self.salvar(segundos=10))

    def test_multiplos_alertas(self):
        for segundo in (0, 10, 20):
            self.salvar(segundos=segundo)
        self.assertEqual(self.salvar(segundos=30, valor=10000, cidade="Curitiba"),
                         ["ALTO_VALOR", "TEMPO_60s", "GEO_10m"])

    def test_reentrega_nao_duplica_nem_soma_na_contagem(self):
        transacao = self.transacao()
        self.assertTrue(salvar_transacao(self.banco, transacao)[1])
        self.assertFalse(salvar_transacao(self.banco, transacao)[1])
        self.salvar(segundos=10)
        self.assertNotIn("TEMPO_60s", self.salvar(segundos=20))
        self.assertEqual(self.banco.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0], 3)

    def test_historico_persiste_apos_reabrir(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as pasta:
            caminho = Path(pasta) / "teste.db"
            banco = abrir_banco(caminho)
            salvar_transacao(banco, self.transacao())
            banco.close()
            banco = abrir_banco(caminho)
            try:
                alertas, _ = salvar_transacao(banco, self.transacao(segundos=30, cidade="Curitiba"))
                self.assertIn("GEO_10m", alertas)
            finally:
                banco.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
