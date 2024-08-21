from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores.azuresearch import AzureSearch
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
import re
import os
from dotenv import load_dotenv
load_dotenv()
azure_deployment = os.getenv("EMBEDDINGS_DEPLOYMENT_NAME")
api_version =os.getenv("AZURE_OPENAI_API_VERSION")
azure_endpoint =os.getenv("OPENAI_ENDPOINT")
openai_api_type =os.getenv("OPENAI_API_TYPE")
api_key =os.getenv("OPENAI_API_KEY")
azure_search_endpoint =os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_key =os.getenv("AZURE_SEARCH_API_KEY")
index_name =os.getenv("AZURE_SEARCH_INDEX_NAME")

def get_text_chunks(text,filename):
    try:
        text_splitter = CharacterTextSplitter(     
            separator = "\n",     
            chunk_size = 1000,     
            chunk_overlap = 200,
            length_function = len) 
        print("Successfully performed Character text splitting")
        if text_splitter and text:
            text_list = text_splitter.split_text(text)
            print("Successfully performed text splitter") 
            if text_list:
                doc = [Document(page_content=chunk, metadata = {"file_name":filename})for chunk in text_list]
                print("Successfully created vector document.")
                get_vector_store(doc)
                return doc
            else:
                print("Failed to create vector document.")
        else:
            print("Failed to perform text spliting.")
    except Exception:
        print("Failed to fetch the text chunks")

def get_vector_store(chunk_data):
    try:
        embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
            azure_deployment = azure_deployment,
            api_version = api_version,
            azure_endpoint= azure_endpoint,
            openai_api_type = openai_api_type,
            api_key= api_key
        )
        if embeddings:
            print("Successfully created azure openai embeddings.")

            vector_store: AzureSearch = AzureSearch(
                azure_search_endpoint = azure_search_endpoint,
                azure_search_key= azure_search_key,
                index_name=index_name,
                embedding_function=embeddings.embed_query,
                additional_search_client_options={"retry_total": 4}
            )

            if vector_store:
                print("Successfully created vector in Azure Search")

                if vector_store.add_documents(documents=chunk_data):
                    print("Succesffully added document in vector store")
                    return vector_store
                else:
                    print("Failed to add document in vector store.")
            else:
                print("Failed to create vector in Azure Search")
        else:
            print("Failed to create azure openai embeddings.")
                
    except Exception as e:
        print("Failed to add document in vector store :",e)

# text = "Guest-1 (0.11-1.11): Good morning, Steve. Good morning, Katie. Have you tried the latest real time diarization in Microsoft Speech Service which can tell you who? Said. In real time. Guest-2 (12.39-20.31): Not yet. I have been using the batch transcription with diarization functionality but it produces diarization result until whole audio get processed. Is the new feature can die arise in real time? Guest-1 (24.79-25.51): Absolutely. Guest-2 (26.45-28.61): That's exciting. Let me try it right now."
# filename = "katiesteve.wav"
# chunk_data = get_text_chunks(text,filename)
# # print("Chunk data :",chunk_data)
# get_vector_store(chunk_data)
