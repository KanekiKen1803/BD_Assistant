# from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI


def get_llm_response(config, query):
    
    # llm= AzureChatOpenAI(azure_deployment = config["AZURE_DEPLOYMENT"],
    #                 openai_api_type = config['OPENAI_API_TYPE'],
    #                 openai_api_key = config['OPENAI_API_KEY'],
    #                 azure_endpoint = config['AZURE_ENDPOINT'],
    #                 openai_api_version = config['OPENAI_API_VERSION'],
    #                 temperature = 0
    #                 )
    openai_key=config["OPENAI_API_KEY"]

    llm = ChatOpenAI(api_key=openai_key,model="gpt-4o-mini")
    
    response = llm.invoke(query)
    return response.content
    
    