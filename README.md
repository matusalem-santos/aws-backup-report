# AWS Backup Report

## Objetivo 

- Gerar relatórios diarios dos backups realidazos e enviar por email 

## Dependências

- Python3

#### Módulos python:

- boto3

## Modo de Usar

- Verificar o email remetente e o destinatario no AWS SES

- Colocar o email remetente na variavel **sender_email**

- Colocar os emails destinatarios na variavel **receiver_emails**

- Cria usuario no IAM com permissão de leitura no serviço AWS Backup 

- Executar o script passando como paramêtro a access key e secret key desse usuario
```bash
    python3 backup.py access_key secret_key
```

- Criar uma cron para essa execução acontecer diariamente