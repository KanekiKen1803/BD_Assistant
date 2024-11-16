import json
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.schema import Document 
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import time

def load_paths():
    # Get the directory of the current script (this file where the function is defined)
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the full path to 'paths.json' in the current directory
    json_file_path = os.path.join(current_directory, 'paths.json')
    
    try:
        # Load the JSON file
        with open(json_file_path, "r") as f:
            paths = json.load(f)
        
        return paths
    except Exception as e:
        print(f"Error loading paths from {json_file_path}: {e}")
        return {}

# Example usage

    
def pdf_data_extracter(pdf_folder_path, output_folder_path):
    # Check if the output folder exists, if not, create it
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    for file in os.listdir(pdf_folder_path):
        if file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_folder_path, file)
            try:
                loader = PyMuPDFLoader(pdf_path)
                documents = loader.load()
                json_data = [
                    {
                        "page": i + 1,
                        "metadata": doc.metadata,
                        "content": doc.page_content
                    }
                    for i, doc in enumerate(documents)
                ]
                output_file_path = os.path.join(output_folder_path, f"{os.path.splitext(file)[0]}.json")
                with open(output_file_path, 'w', encoding='utf-8') as output_file:
                    json.dump(json_data, output_file, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to convert {file}: {str(e)}")


 # Ensure you have the correct import for Document

def case_summary(document, api_key):
    # Extract metadata from the first page
    metadata = document[0]['metadata']
    
    # Concatenate content from all pages
    concatenated_content = " ".join([page['content'] for page in document])
    
    # Create a new Document instance
    llm_document = Document(
        page_content=concatenated_content,
        metadata=metadata
    )
    # print(llm_document.metadata)
    # print(llm_document.page_content)
    


    prompt_template = """
    Analyze the following case study and extract structured insights for similarity search:
    1. Company Profile: Extract the company's name and summarize key details (e.g., industry, scale, market segment, key technologies used in the project).
    2. Pain Points: Identify and list the challenges or issues the company faced. Include both explicit and inferred points separately.
    3. Relevant Domains: Specify the functional areas or domains that these challenges belong to (e.g., Data Analytics, Operational Efficiency, etc.).
    4. Broad Solutions: Provide broad details on how this specific company’s challenges were addressed in this case.
    5. Specific Solutions: Mention specific details on how the problem was solved for this company.

    Case Study: {case_study}

    Respond in JSON format with keys: "Company Profile", "Pain Points", "Relevant Domains", "Broad Solutions", "Specific Solutions".
    The response should be structured as valid JSON that can be directly used for further analysis or similarity search.
    """

    prompt = PromptTemplate(
        input_variables=["case_study"],
        template=prompt_template
    )

    # Create the LangChain LLMChain with the prompt and LLM
    llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    response = llm_chain.run(case_study=llm_document)
    return response, llm_document





# Function to process documents and build the FAISS vector store
def process_documents_with_rate_limiting(documents, embedding, api_key, vector_store_path, delay=1):
    total_documents = len(documents)  # Total number of documents
    print(f"Total documents to process: {total_documents}")
    
    combined_documents = []  # List to store all processed documents

    for i in range(total_documents):
        doc = documents[i]
        
        try:
            # Generate summary for the document using the case_summary function
            summary, doc = case_summary(doc, api_key)
            
            # Create a new Document object to store both summary and original content
            combined_document = Document(
                page_content=summary,
                metadata=doc.metadata  # Store original document content
            )
            
            # Append to the list of documents
            combined_documents.append(combined_document)
            
            # Print progress update
            print(f"Processed document {i + 1}/{total_documents}")
            print(summary)
        
        except Exception as e:
            print(f"Error processing document {i + 1}: {e}")
        
        # Wait for the specified delay before processing the next document
        time.sleep(delay)
    
    # Create the FAISS vector store using all accumulated documents
    print("Creating and saving the FAISS vector store...")
    db = FAISS.from_documents(combined_documents, embedding)
    db.save_local(vector_store_path)
    print("FAISS vector store saved successfully.")

def read_json_files(folder_path):
    documents = []
    for file in os.listdir(folder_path):
        if file.endswith('.json'):
            file_path = os.path.join(folder_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)  # Load the JSON content
                documents.append(content)  # Append the content to the documents list
    return documents


def fetch_relevant_summaries(prompt, embedding_model, vector_store_path, top_k=5):
    """
    Fetch the most relevant summaries from the FAISS vector store based on the input prompt.
    
    Args:
        prompt (str): The user's input query.
        embedding_model: The embedding model used to generate vector representations.
        vector_store_path (str): Path to the saved FAISS vector store.
        top_k (int): Number of relevant summaries to retrieve.
    
    Returns:
        List[dict]: A list of the most relevant summaries and their metadata.
    """
    try:
        # Load the FAISS vector store
        db = FAISS.load_local(vector_store_path, embedding_model, allow_dangerous_deserialization = True)
        
        # Generate embedding for the prompt
        prompt_embedding = embedding_model.embed_query(prompt)
        
        # Search for the top-k most similar summaries
        results = db.similarity_search_by_vector(prompt_embedding, k=top_k)
        print(f"Number of vectors in the store: {db.index.ntotal}")

        # Format the results
        formatted_results = [
            {"summary": doc.page_content, "metadata": doc.metadata} for doc in results
        ]
        
        return formatted_results
    
    except Exception as e:
        print(f"Error fetching summaries: {e}")
        return []


def data_extraction_pipeline(config, paths):
    """
    Processes a list of transcripts and collects responses from the analyze_transcript function.
    
    Args:
        transcripts (list): A list of transcript strings to analyze.
    
    Returns:
        list: A list of JSON formatted responses for each transcript.
    """
    

    pdf_data_extracter(paths["pdf_folder_path"], paths["output_folder_path"])
    documents = read_json_files(paths["json_folder_path"])

    embedding = OpenAIEmbeddings(api_key=config["OPENAI_API_KEY"])
    process_documents_with_rate_limiting(documents, embedding, api_key=config["OPENAI_API_KEY"])
   

def case_search(prompt, vector_store_path,config,top_n = 5):

    embedding = OpenAIEmbeddings(api_key=config["OPENAI_API_KEY"])
    relevant_summaries = fetch_relevant_summaries(prompt, embedding, vector_store_path, top_k=top_n)
    path_top_cases = [summary["metadata"]['source'] for summary in relevant_summaries]
    top_cases = []

    for path in path_top_cases:
        loader = PyMuPDFLoader(path)
        documents = loader.load()
        meta_data = documents[0].metadata
        content = " ".join([doc.page_content for doc in documents])
        llm_document = Document(page_content=content, metadata=meta_data)
        top_cases.append(llm_document)


    return top_cases


def pipeline2(transcript_report, config, paths, top_n = 5, data_extraction = False):

    if data_extraction:
        data_extraction_pipeline(config, paths)
        
    top_cases = case_search(transcript_report, paths["vector_store_path"], config, top_n=top_n)
    return top_cases





