# Detecção de fraude com Kafka

Projeto de estudo em Python. O produtor gera transações aleatórias e publica
no Kafka; o consumidor recebe as mensagens, salva todas em SQLite e mostra
detalhes e alertas de possível fraude no console.

## Executar a primeira etapa

Abra um terminal nesta pasta e execute:

```powershell
python transacoes.py
```

Uma nova transação aparece a cada 3 segundos. Use Ctrl+C para encerrar.
Esta etapa usa apenas a biblioteca padrão do Python.

## Formato provisório

O enunciado menciona um padrão, mas não fornece seus campos. Até receber esse
modelo, usamos:

| Campo | Significado |
| --- | --- |
| id | Identificador único da transação |
| cliente_id | Um dos cinco clientes simulados |
| amount | Valor em reais, entre 1,00 e 15.000,00 |
| cidade | Uma das quatro cidades simuladas |
| data_hora | Data e hora em UTC, no formato ISO 8601 |

Há poucos clientes para permitir repetições durante a demonstração.
As cidades e os valores também são aleatórios; uma execução curta não garante
que todas as regras de fraude sejam acionadas.

## Preparar o Kafka

Instale e inicie o Docker Desktop com suporte a contêineres Linux.
Depois, nesta pasta, execute:

```powershell
docker compose up -d
```

O Kafka estará disponível em localhost:9092. A imagem segue a configuração
simples de desenvolvimento do guia oficial do Apache Kafka.
O envio e o recebimento foram verificados manualmente no computador.

Para preparar a biblioteca usada pelo produtor e pelo consumidor:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Entrega

O consumidor atualizado foi verificado conectado ao Kafka: as transações
foram salvas e os três tipos de alerta apareceram na consulta ao banco.
Ainda é necessário confirmar o formato exigido pelo professor e publicar
o repositório no GitHub.

Faça commits conforme concluir etapas reais do projeto. A entrega exige
pelo menos quatro commits no GitHub.

## Executar produtor e consumidor

Com o Kafka iniciado e a biblioteca instalada, abra dois terminais nesta pasta.
No primeiro execute:

```powershell
& .\.venv\Scripts\python.exe consumidor.py
```

No segundo execute:

```powershell
& .\.venv\Scripts\python.exe produtor.py
```

O produtor mostra ENVIADA e o consumidor mostra RECEBIDA, com o mesmo id.
Use Ctrl+C em cada janela para encerrar. O tópico transacoes é criado pelos
programas se ainda não existir. O consumidor usa um grupo fixo e retoma do
último ponto confirmado; na primeira execução lê desde o início do tópico.
As mensagens são confirmadas no Kafka depois da gravação no banco. Uma
reentrega com o mesmo id não duplica a transação. Os valores são guardados em
centavos inteiros e o histórico permanece disponível após reiniciar o consumidor.

Esta versão usa um novo grupo, detector-fraude-com-banco, para ler e salvar
também as mensagens do primeiro teste que ainda estiverem retidas no Kafka.
Nas próximas execuções retoma do último ponto confirmado. Mantenha o arquivo
transacoes.db junto ao projeto: os pontos de leitura do Kafka dependem desse
histórico. Apagar o banco não faz o Kafka reenviar automaticamente as mensagens.

Para um teste curto, use --limite 3 em ambos os programas.

## Regras e interpretações

| Alerta | Condição |
| --- | --- |
| ALTO_VALOR | amount maior ou igual a 10000 |
| TEMPO_60s | Pelo menos quatro transações do mesmo cliente em menos de 60 segundos, incluindo a atual |
| GEO_10m | Uma transação anterior do mesmo cliente em outra cidade, há no máximo 600 segundos |

As regras usam a data e hora da transação. Exatamente 60 segundos ficam fora
da regra TEMPO_60s; exatamente 10 minutos ficam dentro de GEO_10m. Mais de
uma regra pode disparar na mesma transação. Alertas indicam suspeita segundo
as regras do exercício, e não comprovação de fraude.

O produtor atual gera horários em ordem e usa um tópico com uma partição.
O consumidor consulta apenas transações anteriores já salvas, sem corrigir
alertas retrospectivamente caso outras fontes enviem mensagens fora de ordem.

## Consultar o banco

Abra um terceiro terminal nesta pasta e execute:

```powershell
& .\.venv\Scripts\python.exe consultar_banco.py
```

O programa mostra os totais e as últimas dez transações. O arquivo
transacoes.db é criado na pasta do projeto, independentemente de onde você
abriu o terminal. Não é necessário instalar outro programa de banco.

## Testar as regras sem Kafka

```powershell
& .\.venv\Scripts\python.exe testes.py
```

Os testes verificam valores no limite, janelas de tempo, cidades distintas,
clientes distintos, alertas combinados, reentregas e persistência do histórico.

## Referências

- https://kafka.apache.org/quickstart/
- https://docs.confluent.io/kafka-clients/python/current/overview.html
