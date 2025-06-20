import pandas as pd
import re
from dateutil.parser import parse
import io
import numpy as np
from datetime import datetime
from leitura_arquivo_drive import *

# Caminho para a credencial da conta de serviço
CREDENTIALS_PATH = 'credentials/people-analytics-pipoca-agil-google-drive.json'

# Transformação de dados
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
    
    def normalizar_perguntas(self, pergunta):
        fase1 = pergunta.split('.')[1].lstrip()
        fase2 = re.sub(r'[^\w\s]', '', fase1)
        fase3 = self.retirar_acento(fase2)
        fase4 = re.sub(' ', '_', fase3)
        return fase4
    
    def padronizar_datastring(self, dataStamp): 
        try:
            parsed_date = parse(str(dataStamp))
            return parsed_date.strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError):
            return dataStamp #"Invalid Date"
    
    def renomear_colunas_autoavaliacao(self):
        colunas = ['timestamp', 'emailRespondente', 'nomeRespondente', 'funcaoDesempenha', 'equipeParticipante']
        self.df_raw.columns = colunas + [f'pergunta_{i}' for i in range(len(self.df_raw.columns) - len(colunas))]
    
    def transformar_simnao_zeroum(self):
       df_copy=self.df_raw
       df_copy['pergunta_8'].map({'sim': 1, 'nao': 0, 'não':0})
       self.df_raw=df_copy

    def validar_email(self):
        padrao_email = r'^[\w-.]+@[\w-]+.[a-zA-Z]{2,}$'
        self.df_raw['emailRespondente'] = self.df_raw['emailRespondente'].where(
         self.df_raw['emailRespondente'].str.fullmatch(padrao_email))
    
    def clean_empty_rows(self):
        df_copy = self.df_raw
        df_copy = df_copy.drop_duplicates()
        self.df_raw = df_copy
    
    def transformar_dados(self):
        self.renomear_colunas_autoavaliacao()
        self.validar_email()
        self.df_raw['timestamp'] = self.df_raw['timestamp'].apply(self.padronizar_datastring)
        self.transformar_simnao_zeroum()
        self.clean_empty_rows()
        return self.df_raw

# Para transformar o arquivo autoavaliacao da pasta trusted no formato modelo_fato_respostas
class TransformerFatoRespostas:
    def __init__(self, df_trusted, file_name):
        self.df_trusted = df_trusted
        self.file_name = file_name

    def transformar_trusted_fato_respostas(self):
        df_copy = pd.DataFrame(self.df_trusted)
        tipo_perguntas = ['Quantitativa de 0 a 10'] * 8 + ['sim/nao'] + ['Quantitativa de 0 a 10'] * 7 + ['Descritiva, texto de opinião']
        # coluna com o tipo de dados das respostas
        tipo_repostas = ['int'] * 16 +['str']
        perguntas = df_copy.columns.tolist()[5:22]
        all_df = []
        for i_entrevistado in range(df_copy.shape[0]):
            row = df_copy.iloc[i_entrevistado]
            respostas = [int(x) if pd.notna(x) and isinstance(x, (np.float64, float)) else x for x in row.iloc[5:22].tolist()]
            fato_resposta = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'dsEmailRespondente': row.iloc[1],
                'dsNomeRespondente': row.iloc[2],
                'dsQualFuncaoDesempenha': row.iloc[3],
                'dsEquipeParticipante': row.iloc[4],
                'nmCadernoPergunta': 'Avaliação do projeto (respostas)',
                'dsTituloPergunta': perguntas,
                'dsTipoPergunta': tipo_perguntas,
                'dsResposta': respostas,
                'dsDataType': tipo_repostas
            }
            # Garantir que todas as listas tenham o mesmo comprimento
            max_length = max(len(fato_resposta[key]) for key in fato_resposta if isinstance(fato_resposta[key], list))
            for key in fato_resposta:
                if isinstance(fato_resposta[key], list):
                    fato_resposta[key] += [None] * (max_length - len(fato_resposta[key]))
            df_fato_resposta = pd.DataFrame(fato_resposta)
            all_df.append(df_fato_resposta)
        return pd.concat(all_df, ignore_index=True)

# Processo principal de transformação do raw para o trusted
def processar_arquivo(drive_manager, relatorio_raw, relatorio):
    folder_id = drive_manager.Id_camada['raw']
    file_id = drive_manager.get_file_id(relatorio_raw, folder_id)
    if not file_id:
        raise ValueError(f"Arquivo {relatorio_raw} não encontrado na camada 'raw'.")
    drive_manager.download_existing_file(file_id, relatorio_raw)
    df_raw = pd.read_excel(relatorio_raw)
    transformer = DataTransformer(df_raw, relatorio_raw)
    df_transformado = transformer.transformar_dados()
    for camada in ['trusted']:
        drive_manager.save_data_to_layer(df_transformado, camada, relatorio)
    file_to_save = f"{relatorio}_processado.xlsx"
    df_transformado.to_excel(file_to_save)
    return file_to_save

# Processo para transformar trusted em refined, no modelo da fato_respostas
def processar_fato_respostas(drive_manager, transformer, relatorio):
    data = transformer.transformar_trusted_fato_respostas()
    for camada in ['refined']:
        drive_manager.save_data_to_layer(data.copy(), camada, relatorio)

# Executar o processamento
if __name__ == "__main__":
    setup_logging()
    relatorio_raw = "avaliacao_projeto.xlsx"
    file_name = "avaliacao_projeto.xlsx"
    relatorio = "avaliacao_projeto"
    relatorio_final = 'fato_respostas'
    auth = GoogleAuthenticator()
    drive_service = auth.drive_service
    drive_manager = GoogleDriveManager(drive_service)
    file_to_save = processar_arquivo(drive_manager, file_name, relatorio_raw)
    df_trusted = pd.read_excel(file_to_save)
    transformer = TransformerFatoRespostas(df_trusted, file_name)
    processar_fato_respostas(drive_manager, transformer, relatorio_final)



