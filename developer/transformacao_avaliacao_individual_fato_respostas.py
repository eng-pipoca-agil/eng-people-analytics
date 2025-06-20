import pandas as pd
import re
from dateutil.parser import parse
import numpy as np
from datetime import datetime
from leitura_arquivo_drive import *

credentials_path = 'credentials/people-analytics-pipoca-agil-google-drive.json'

class DataTransformer:
    def __init__(self, df_raw, file_name):
        self.df_raw = df_raw
        self.file_name = file_name
    
    def retirar_acento(self, frase):
        nova = frase.lower()
        nova = re.sub(r'[àáâãäå]', 'a', nova)
        nova = re.sub(r'[èéêë]', 'e', nova)
        nova = re.sub(r'[ìíîï]', 'i', nova)
        nova = re.sub(r'[òóôõö]', 'o', nova)
        nova = re.sub(r'[ùúûü]', 'u', nova)
        nova = re.sub(r'ç', 'c', nova)
        return nova
    
    
    def padronizar_datastring(self, dataStamp): 
        try:
            parsed_date = parse(str(dataStamp))
            return parsed_date.strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError):
            return dataStamp 
    
    def renomear_colunas_autoavaliacao(self):
        colunas_fixas = ['timestamp', 'emailRespondente', 'nomeRespondente', 'funcaoDesempenha', 'equipeParticipante']
        colunas_variaveis = [f'pergunta_{i+1}' for i in range(len(self.df_raw.columns) - len(colunas_fixas))]
        self.df_raw.columns = colunas_fixas + colunas_variaveis
    
    def validar_email(self):
        padrao_email = r'^[\w-.]+@[\w-]+.[a-zA-Z]{2,}$'
        self.df_raw['emailRespondente'] = self.df_raw['emailRespondente'].where(
         self.df_raw['emailRespondente'].str.fullmatch(padrao_email))
    
    def clean_empty_rows(self):
        self.df_raw.drop_duplicates(inplace=True)
    
    def transformar_dados(self):
        self.renomear_colunas_autoavaliacao()
        self.validar_email()
        self.df_raw['timestamp'] = self.df_raw['timestamp'].apply(self.padronizar_datastring)
        self.clean_empty_rows()
        return self.df_raw

class TransformerFatoRespostas:
    def __init__(self, df_trusted, file_name):
        self.df_trusted = pd.DataFrame(df_trusted)
        self.file_name = file_name

    def transformar_trusted_fato_respostas(self):
        df_copy = self.df_trusted.copy()
        perguntas = df_copy.columns.tolist()[5:]  # Agora pega todas as colunas de perguntas
        num_perguntas = len(perguntas)
        
        tipo_perguntas = ['Quantitativa de 0 a 10'] * (num_perguntas - 1) + ['Descritiva, texto de opinião']
        tipo_repostas = ['int'] * (num_perguntas - 1) + ['str']
        
        all_df = []
        for i_entrevistado in range(df_copy.shape[0]):
            row = df_copy.iloc[i_entrevistado]
            respostas = [int(x) if pd.notna(x) and isinstance(x, (np.float64, float)) else x for x in row.iloc[5:].tolist()]
            
            fato_resposta = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'dsEmailRespondente': row.iloc[1],
                'dsNomeRespondente': row.iloc[2],
                'dsQualFuncaoDesempenha': row.iloc[3],
                'dsEquipeParticipante': row.iloc[4],
                'nmCadernoPergunta': 'Avaliação individual do time (respostas)',
                'dsTituloPergunta': perguntas,
                'dsTipoPergunta': tipo_perguntas,
                'dsResposta': respostas,
                'dsDataType': tipo_repostas
            }
            df_fato_resposta = pd.DataFrame(fato_resposta)
            all_df.append(df_fato_resposta)
        
        return pd.concat(all_df, ignore_index=True)

def processar_fato_respostas(drive_manager, transformer, relatorio_final):
    df_fato_respostas = transformer.transformar_trusted_fato_respostas()
    drive_manager.save_data_to_layer(df_fato_respostas, 'refined', relatorio_final)

if __name__ == "__main__":
    setup_logging()
    relatorio_raw = "avaliacao_individual.xlsx"
    relatorio = "avaliacao_individual"
    relatorio_final = 'fato_respostas'
    auth = GoogleAuthenticator()
    drive_service = auth.drive_service
    drive_manager = GoogleDriveManager(drive_service)
    
    file_id = drive_manager.get_file_id(relatorio_raw, drive_manager.Id_camada['raw'])
    if not file_id:
        raise ValueError(f"Arquivo {relatorio_raw} não encontrado na camada 'raw'.")
    
    drive_manager.download_existing_file(file_id, relatorio_raw)
    df_raw = pd.read_excel(relatorio_raw)
    transformer = DataTransformer(df_raw, relatorio_raw)
    df_transformado = transformer.transformar_dados()
    
    if df_transformado.empty:
        raise ValueError("Nenhum dado válido após a transformação!")
    
    drive_manager.save_data_to_layer(df_transformado, 'trusted', relatorio)
    df_transformado.to_excel(f"{relatorio}_processado.xlsx")
    
    df_trusted = pd.read_excel(f"{relatorio}_processado.xlsx")
    transformer_fato = TransformerFatoRespostas(df_trusted, relatorio_raw)
    df_fato_respostas = transformer_fato.transformar_trusted_fato_respostas()
    
    drive_manager.save_data_to_layer(df_fato_respostas, 'refined', relatorio_final)

