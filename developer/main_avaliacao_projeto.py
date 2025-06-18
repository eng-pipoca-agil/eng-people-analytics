from notificacao_discord import DiscordNotifier
from datetime import datetime
from leitura_arquivo_drive import GoogleAuthenticator, GoogleDriveManager, GoogleSheetsManager, processar_camada_raw, processar_camada_trusted
from transformacao_avaliacao_projeto_fato_respostas import processar_fato_respostas, TransformerFatoRespostas
import pandas as pd

# Definições iniciais
relatorio = 'avaliacao_projeto'  # Opções: autoavaliacao, avaliacao_coletiva, avaliacao_projeto, #avaliacao_individual
camada = 'raw'
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
relatorio_raw = "avaliacao_projeto.xlsx"
file_name = "avaliacao_projeto.xlsx"
relatorio_final = 'fato_respostas'

# Instancia a classe de comunicação com o Discord
notifier = DiscordNotifier()
#notifier.enviar_notificacao(f"{timestamp} - Início do processo de transformação de dados.", processo=relatorio, status="sucesso")

# Autenticar no Google Drive
auth = GoogleAuthenticator()
drive_service = auth.drive_service  # Obter o serviço de drive autenticado
drive_manager = GoogleDriveManager(drive_service)  # Passar o serviço de drive para o construtor
sheets_manager = GoogleSheetsManager(auth.sheets_client)

# TODO: Com a centralização futura em um único main, considerar extrair esse bloco para uma função principal.
try:
    # Transformação do raw para trusted
    processar_camada_raw(sheets_manager, drive_manager, relatorio)
    
    # Carregar os dados transformados
    df_trusted = processar_camada_trusted(sheets_manager, drive_manager, relatorio)
    transformer = TransformerFatoRespostas(df_trusted, file_name)
    
    # Transformação do trusted para refined (modelo fato_respostas)
    processar_fato_respostas(drive_manager, transformer, relatorio_final)
    
    #notifier.enviar_notificacao(f"{timestamp} - Transformação de dados concluída com sucesso.", processo=relatorio, status="sucesso")

except Exception as e:
    #notifier.enviar_notificacao(f"{timestamp} - Erro durante o processo de transformação: {str(e)}", processo=relatorio, status="falha")
    raise e
