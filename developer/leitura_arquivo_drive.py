import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import pandas as pd
import logging
import os

class GoogleAuthenticator:
    """Gerencia a autenticação do Google Sheets e Google Drive."""

    def __init__(self):
        """Inicializa a autenticação com as credenciais fornecidas."""
        self.sheets_client = None
        self.drive_service = None
        self.authenticate()

    def authenticate(self):
        """Autentica na API do Google Sheets e Google Drive."""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials_path = 'credentials/people-analytics-pipoca-agil-google-drive.json'
            credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)

            # Cliente para Google Sheets
            self.sheets_client = gspread.authorize(credentials)

            # Cliente para Google Drive
            self.drive_service = build('drive', 'v3', credentials=credentials)

            logging.info("Autenticação bem-sucedida no Google Sheets e Google Drive.")
        except Exception as e:
            logging.error(f"Erro na autenticação: {e}")
            raise

class GoogleSheetsManager:
    """Gerencia operações com o Google Sheets."""

    def __init__(self, client):
        """Inicializa o gerenciador do Google Sheets."""
        self.client = client
        self.sheet_ids = {
            'autoavaliacao': '1NmhI61q2bZJBWr3Vb3C_Y6siGUOC1rk66FOXu3gUN00',
            'avaliacao_individual': '1CNhr4wFnrqLuHfU0LUm2SQV4RtF8EAECaRgSQhTvxyY',
            'avaliacao_coletiva': '1tOuJ95zjUiyHQCwY5gMF9uSVnbAr5Fwy-OMWTe_WTpo',
            'avaliacao_projeto': '1FpDuXzn7HIeDh5ZCHxUVtiQGBY3XiQ_v196z56MuHag'
        }

    def get_sheet(self, relatorio):
        """Obtém a planilha pelo ID correspondente ao relatório."""
        if relatorio not in self.sheet_ids:
            logging.error(f"Erro ao acessar a planilha: Relatório '{relatorio}' inválido.")
            raise ValueError(f"Relatório '{relatorio}' não encontrado.")

        sheet_id = self.sheet_ids[relatorio]

        try:
            sheet = self.client.open_by_key(sheet_id).sheet1
            logging.info(f"Conectado à planilha ID: {sheet_id}")
            return sheet
        except Exception as e:
            logging.error(f"Erro ao acessar a planilha: {e}")
            raise

    def get_data(self, sheet):
        """Obtém todos os dados da planilha e retorna como lista de listas."""
        try:
            data = sheet.get_all_values()
            logging.info("Dados obtidos com sucesso da planilha.")
            return data
        except Exception as e:
            logging.error(f"Erro ao obter dados da planilha: {e}")
            raise

class GoogleDriveManager:
    """Gerencia operações de upload de arquivos no Google Drive."""

    def __init__(self, drive_service, camada):
        """Inicializa o gerenciador do Google Drive."""
        self.drive_service = drive_service
        self.Id_camada = {
            'raw': '1E6AEUGqRp3IJsWV4qAwMRJK_tMD7wDYT',
            'refined': '1tc3HQnG507HfyLvHqtZasb-La8GD98P0',
            'trusted': '1WJlq1C_uLq9J3Ta-lVAkQVv7AzblftsD'
        }

    def get_file_id(self, file_name, folder_id):
        """Busca o arquivo no Google Drive e retorna seu ID, se existir."""
        try:
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id)").execute()
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception as e:
            logging.error(f"Erro ao buscar arquivo no Google Drive: {e}")
            return None

    def download_existing_file(self, file_id, file_name):
        """Faz o download do arquivo existente no Google Drive."""
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            with open(file_name, "wb") as f:
                f.write(request.execute())
            logging.info(f"Arquivo {file_name} baixado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao baixar o arquivo: {e}")

    def save_data_to_excel_and_upload(self, data, camada, relatorio):
        """Apende os dados ao arquivo existente ou cria um novo se não existir."""
        try:
            folder_id = self.Id_camada[camada]
            file_name = f"{relatorio}.xlsx"
            file_id = self.get_file_id(file_name, folder_id)

            # Se o arquivo já existir, baixa e apenda os dados
            if file_id:
                self.download_existing_file(file_id, file_name)
                existing_df = pd.read_excel(file_name, header=0)
                new_df = pd.DataFrame(data)
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                logging.info("Dados apensados ao arquivo existente.")
            else:
                updated_df = pd.DataFrame(data)
                logging.info("Criando novo arquivo Excel.")

            # Salva o arquivo atualizado
            updated_df.to_excel(file_name, index=False, header=True)

            # Remove o arquivo antigo do Google Drive (se existir)
            if file_id:
                self.drive_service.files().delete(fileId=file_id).execute()
                logging.info(f"Arquivo antigo {file_name} removido do Google Drive.")

            # Faz upload do novo arquivo
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            uploaded_file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logging.info(f"Arquivo atualizado enviado para o Google Drive. ID: {uploaded_file.get('id')}")

            # Remove o arquivo local após o upload
            os.remove(file_name)

        except Exception as e:
            logging.error(f"Erro ao salvar o arquivo no Google Drive: {e}")
            raise

def setup_logging():
    """Configura o logging para registrar informações e erros."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

if __name__ == "__main__":
    setup_logging()

    auth = GoogleAuthenticator()
    sheets_manager = GoogleSheetsManager(auth.sheets_client)
    drive_manager = GoogleDriveManager(auth.drive_service, camada='trusted')

    relatorio = 'autoavaliacao'  # Defina o relatório desejado
    sheet = sheets_manager.get_sheet(relatorio)  # Obtém a planilha correta

    data = sheets_manager.get_data(sheet)  # Obtém os dados da planilha
    drive_manager.save_data_to_excel_and_upload(data, camada='trusted', relatorio=relatorio)  # Salva e faz upload
