from leitura_arquivo_drive import *
from transformacao_autoavaliacao_fato_respostas import GoogleDriveManager,GoogleAuthenticator
import pandas as pd


#para transformar o arquivo autoavaliacao da pasta trusted no formato modelo_fato_respostas
class TransformerFatoRespostas:
    def __init__(self,df_trusted):
        self.df_trusted = df_trusted


    def transformar_trusted_fato_respostas(self):
        df_copy = self.df_trusted
        #criaremos colunas de informações que são comuns a todos os relatórios
        #coluna com a descrição do tipo de pergunta
        tipo_perguntas = ['Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10',
                  'Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10,','Quantitativa de 0 a 10',
                  'sim/nao','Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10',
                  'Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10',
                  'Descritiva, texto de opinião']
        #coluna com o tipo de dados das respostas
        tipo_repostas = ['int','int','int','int','int','int','int','int','boolean','int','int','int','int','int','int','int',
                 'str']
        # TODO: Avaliar refatoração para tornar as listas tipo_perguntas e tipo_respostas mais limpas e legíveis:
        # tipo_perguntas = ['Quantitativa de 0 a 10'] * 8 + ['sim/nao'] + ['Quantitativa de 0 a 10'] * 7 + ['Descritiva, texto de opinião']
        # tipo_respostas = ['int'] * 8 + ['boolean'] + ['int'] * 7 + ['str']

        #coluna com as perguntas
        perguntas = df_copy.keys().tolist()[5:22]
        #Cada entrevistado, que representa uma linha, que terá que ser transposta separadamente, transformado em dataframe e depois
#os dataframes serão concatenados verticalmente
        all_df = []
        for i_entrevistado in range(df_copy.shape[0]):
            row = df_copy.iloc[i_entrevistado].T
            row = row.apply(lambda x: int(x) if pd.notna(x) and isinstance(x, (np.float64, float)) else x) #transformar todos os campos float para integer
            fato_resposta = {'timestamp': "Placeholder",
                             'dsEmailRespondente': row.iloc[1], #campo do email
                              'dsNomeRespondente': row.iloc[2], #campo do entrevistado    
                              'dsQualFuncaoDesempenha':row.iloc[3], #campo da função
                              'dsEquipeParticipante':row.iloc[4], #campo da equipe
                              'nmCadernoPergunta': 'Autoavaliação Pipoca Ágil (respostas)', #modificar para cada formulário
                              'dsTituloPergunta': perguntas, #lista com as perguntas
                              'dsTipoPergunta':tipo_perguntas, #lista com o tipo das perguntas
                              'dsResposta':row.iloc[5:22], #lista com as respotas
                              'dsDataType':tipo_repostas} #lista com os tipos das respostas
            df_fato_resposta = pd.DataFrame(fato_resposta).reset_index(drop=True) #criar um dataframe do dicionário fato_reposta
        all_df.append(df_fato_resposta) #unir todos os dataframes en uma lista
        df_new = pd.concat(all_df)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_new['timestamp']=timestamp
        return df_new


def processar_fato_respostas(drive_manager, transformer,relatorio):
    data = transformer.transformar_trusted_fato_respostas()
    for camada in ['trusted']:
        drive_manager.save_data_to_layer(data.copy(),camada,relatorio)

def setup_logging():
    """Configura o logging para registrar informações e erros."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
if __name__ == "__main__":
    setup_logging()
    #devemos dividir em duas partes, ler o 
    auth = GoogleAuthenticator()
    drive_manager = GoogleDriveManager(auth.drive_service)
    transformer = TransformerFatoRespostas(df_trusted)
    relatorio = 'fato_respostas.xlsx'  # Defina o relatório desejado
    processar_fato_respostas(drive_manager,transformer,relatorio)

       
    
    
#essa parte será integrada com transformação  
#auth = GoogleAuthenticator()
#drive_manager = GoogleDriveManager(auth.drive_service)
#folder_id = drive_manager.Id_camada['trusted'] #obter o id da pasta trusted
#relatorio = 'modelo_fato_respostas'  # Defina o relatório desejado
#file_id = drive_manager.get_file_id(relatorio,folder_id) obter o id do arquivo relatorio
#autoavaliacao = drive_manager.get_file_data(file_id) #baixar o arquivo para a memória local
#autoavaliacao = autoavaliacao.drop_duplicates() #para remover o cabeçalho caso ele se repita
#o processo de transformação


