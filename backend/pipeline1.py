
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
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


def client_info_fun(client_name: str,config, **client_details):
    """
    Function to generate a comprehensive summary of a company's business profile.
    
    Parameters:
    - company_name (str): The name of the company.
    - additional_details (dict): Additional dynamic parameters like key performance indicators or areas of focus.

    Returns:
    - str: The generated company summary with key metrics, strategic focus areas, and more.
    """


 

    # Required following parameters. Update following input parameters. Make sure embedding model and LLM models are deployed within same resource.

    openai_key=config["OPENAI_API_KEY"]
    serper_api_key = config["serper_api_key"]
    

    ## Following is very essential to run crewAI agent. Environment key OPENAI_API_KEY must be set up.
    os.environ['SERPER_API_KEY']= serper_api_key
    os.environ["OPENAI_API_KEY"]= openai_key
    llm_crew = ChatOpenAI(api_key=openai_key,model="gpt-4o-mini")

    # Check if the API keys are set
    if not openai_key or not serper_api_key:
        raise ValueError("API keys are missing. Please set the OPENAI_API_KEY and SERPER_API_KEY environment variables.")


    # Define the Agents
    internet_research_agent = Agent(
    role = "Internet Research Agent",
    goal = "Your goal is to assist in identifying and analyzing strategic business insights from trusted web sources. You will focus on uncovering market trends, key metrics (quantative ), competitive positioning, and innovation opportunities to help the business development team craft tailored solutions and value propositions.",
    backstory = "You are a business-focused research agent with expertise in uncovering actionable business insights. Your role is to assist in the discovery of growth opportunities, competitive advantages, and pain points in the client's industry to support strategic decision-making and client proposals.",
    allow_delegation = False,
    verbose = True,
    llm = ChatOpenAI(api_key=openai_key,model="gpt-4o-mini"))
    
    # Define tools for the tasks
    tools = [SerperDevTool(), ScrapeWebsiteTool()]
    
    # Define Tasks for Agents
    internet_research_task = Task(
    description = f"Analyze the company {client_name}’s profile based on the provided query : {{question}} and generate insights on key business factors including market positioning, competitive advantages, target segments, financial performance, strategic priorities, and technological innovation. Extract information that will aid in identifying areas of opportunity or potential challenges for business development efforts.",
    expected_output = "Provide a comprehensive analysis of the company, including its strategic position, industry trends, financial health, key growth areas, and technologies used. Highlight potential business pain points, opportunities for growth, and areas where competitive differentiation can be achieved. Include references to sources that support your findings.",
    tools = tools,
    agent = internet_research_agent,
    )
    
    agents = [internet_research_agent]
    tasks = [internet_research_task]
    
    crew = Crew(
            agents = agents,
            tasks = tasks,
            process = Process.sequential,
            verbose=True
        )

    # inputs = {"question":"Generate a summary of of client {client_name}, covering it's industry positioning, ownership, target market segment, latest available key metrics, strategic focus areas, and the primary technologies or tools they use."}   
    inputs = {"question":f"Generate a summary of of client {client_name}, covering it's industry positioning, ownership, target market segment, latest available key metrics, strategic focus areas, and the primary technologies or tools they use."}
    response = crew.kickoff(inputs=inputs)
    return response.raw  

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

    client_background = client_info_fun(client_name, config)

    return transcript, transcript_report, client_background



