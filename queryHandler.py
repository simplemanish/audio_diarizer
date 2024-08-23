from langchain.chains import ConversationalRetrievalChain 
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.chat_models import AzureChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.prompts import PromptTemplate
import streamlit as st
import os
# from setLogger import setupLogger
# logger = setupLogger()
from dotenv import load_dotenv

load_dotenv()

class UserQueryHandler():
    deployment = os.getenv("EMBEDDINGS_DEPLOYMENT_NAME")
    deployment_model = os.getenv("EMBEDDINGS_DEPLOYMENT_MODEL")
    
    gpt_deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    azure_endpoint= os.getenv("OPENAI_ENDPOINT")

    def __init__(self, index_name, question):
        self.index_name = index_name
        self.question = question

    def load_index_ifexisit(self): #it will load index from azure search
        vector_password = os.getenv("AZURE_SEARCH_API_KEY")
        vector_address = os.getenv("AZURE_SEARCH_ENDPOINT")
        index_name = self.index_name
        print("inside load index function")
        try:
            embeddings = AzureOpenAIEmbeddings(azure_endpoint= self.azure_endpoint,deployment= self.deployment, model=self.deployment_model, chunk_size=1)

            if embeddings:
                print("Successfully created azure openai embeddings.")
                vectorstore = AzureSearch(
                    azure_search_endpoint=vector_address,
                    azure_search_key=vector_password,
                    index_name=index_name,
                    embedding_function=embeddings.embed_query,
                )

                if vectorstore:
                    print("Successfully created vector store.")
                    st.session_state.conversation = self.get_conversation_chain(vectorstore)
                    return True
                
                else:
                    st.error("Error occurred while creating vector store.")
                    print("Error occurred while creating vector store.")
        
        except Exception as e:
            st.error(f"Error occurred while loading index.{e}")
            print(f"Error occurred while loading index.{e}")

    def get_conversation_chain(self,vectorstore):
        
        prompt_template = """Use the following pieces of context to answer the question at the end.  Respond with a concise and informative answer. If answer not found in provided context, please don't try to collect any information outside the provided context. Also use {chat_history} to answer the next question mandatorily.
        {context}
        Question: {question}
        Answer:"""
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context","question","chat_history"]
        )
        chain_type_kwargs = {"prompt": PROMPT}

        memory = ConversationBufferMemory( memory_key="chat_history",input_key="question", output_key="answer", return_messages=True)
  
        llm = AzureChatOpenAI(deployment_name=self.gpt_deployment_name,api_version=self.api_version,azure_endpoint= self.azure_endpoint,temperature=0.4)

        if memory and llm:
            conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever(search_type="similarity_score_threshold", k=3,search_kwargs={"score_threshold": 0.4}),
                chain_type="stuff",
                memory=memory,
                max_tokens_limit=4000,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": PROMPT},
                verbose=True,
            ) 
            print("Successfully created conversation chain.")
            return conversation_chain

        else:
            st.error("Failed to create conversation chain.")
            print("Failed to create conversation chain.")

        

    # def get_conversation_chain_memory(self):
    #     global memory
    #     if st.session_state.conversation:
    #         print("inside if conversation")
    #         extracted_msgs = st.session_state.conversation.memory.chat_memory.messages
    #         chat_memory = ChatMessageHistory(messages=extracted_msgs)
    #         memory = ConversationBufferMemory( memory_key="chat_history",input_key="question", output_key="answer", return_messages=True, chat_memory=chat_memory)
    #     else:
    #         print("inside else conversation")
    #         memory = ConversationBufferMemory( memory_key="chat_history",input_key="question", output_key="answer", return_messages=True)

    #     return memory


def handle_userinput(question,index_name):


    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if index_name:
        print(f"Index Name is : {index_name}.")

        uqh = UserQueryHandler(index_name,question)
        if uqh:
            if uqh.load_index_ifexisit():
                result = st.session_state.conversation({"question": question,"chat_history":st.session_state.chat_history})
                
                # for i in range(len(result["chat_history"])-2,len(result["chat_history"])):
                #    st.session_state.chat_history.append(result["chat_history"][i].content)
                
                # if result["source_documents"]:
                print("result :",result)
                for i in range(len(result["chat_history"])-2,len(result["chat_history"])):
                    st.session_state.chat_history.append(result["chat_history"][i].content)
                # else:
                #     for i in range(len(result["chat_history"])-2,len(result["chat_history"])-1):
                #         st.session_state.chat_history.append(result["chat_history"][i].content)
                #         result = "The information regarding your question is out of provided context. We'll soon get back to you."
                #     st.session_state.chat_history.append(result)

        else:
            print("Failed to call UserQueryHandler.")
        
    else:
        st.error("Missing valid index_name.")
        print("Missing valid index_name.")

    return st.session_state.chat_history