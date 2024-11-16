
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
import json
import os

# Set up your OpenAI API key by loading from the config file
def load_config():
    # Get the directory of the current script (pipeline1.py)
    current_directory = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_directory, 'config.json')

    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
            return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {config_file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {config_file_path}")


# Define the function to analyze the transcript
def analyze_transcript(transcript: str, config) -> str:
    """
    Analyzes the given transcript and returns structured insights in JSON format.
    
    Args:
        transcript (str): The transcript to analyze.
    
    Returns:
        str: JSON formatted response with structured insights.
    """
    # Define the prompt template
    openai_api_key = config["OPENAI_API_KEY"]
    prompt_template = """
    Analyze the following transcript and extract structured insights:
    1. Company Profile: Get company name and summarize the company's key attributes (e.g., industry, scale, market segment, key technologies).
    2. Pain Points: Highlight the challenges or issues the company is facing. Include explicit and inferred points seperately.
    3. Relevant Domains: Specify the functional areas or domains these challenges belong to.
    4. Broad Solutions: Suggest how such problems are typically addressed in the industry.
    6. Specific Solutions: Suggest how clients specific problem could be solved.

    Transcript: {transcript}

    Respond in JSON format with keys: "Company Profile", "Pain Points", "Relevant Domains", "Broad Solutions", Specific Solutions".
    The response should only be json format that I can directly convert to json file from string.
    """

    # Create the LangChain PromptTemplate
    prompt = PromptTemplate(
        input_variables=["transcript"],
        template=prompt_template
    )

    # Create the LangChain LLMChain with the prompt and LLM
    llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini")
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    # Run the chain and return the response
    response = llm_chain.run(transcript=transcript)
    return response


def client_info_fun(client_name):

    return 'Test Client Info'

def pipeline1(transcript, config):
    """
    Processes a list of transcripts and collects responses from the analyze_transcript function.
    
    Args:
        transcripts (list): A list of transcript strings to analyze.
    
    Returns:
        list: A list of JSON formatted responses for each transcript.
    """
    
    transcript_report = analyze_transcript(transcript, config)

    client_data = json.loads(transcript_report[7:-3])
    client_name = client_data['Company Profile']['Company Name'] #get based on transcript response

    client_background = client_info_fun(client_name)

    return transcript, transcript_report, client_background



