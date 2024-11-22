import os
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
import streamlit as st

# Function to load config file paths
def load_config():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_directory, 'config.json')

    with open(config_file_path, 'r') as f:
        config = json.load(f)

    return config

# Initialize OpenAI's GPT-4 model
def initialize_gpt(config):
    return ChatOpenAI(api_key=config["OPENAI_API_KEY"], model="gpt-4o-mini")

# --- Define Prompt Templates for Each Part of the Process ---
problem_understanding_template = """
Based on the following client call transcript, extract the main problems and pain points the client is facing. 
Focus on the core issues that need to be addressed, and identify the main objectives or goals the client wants to achieve.

Call Transcript:
{transcript}

Provide:
- Key pain points
- The client's main objectives or goals
"""

market_positioning_template = """
Given the following client background, position them within their industry and market segment. 
Discuss their competitive strengths, challenges, and the market dynamics they face. What differentiates them in the marketplace?

Client Information:
{client_background}

Provide:
- Overview of the client's position in the market
- Key competitive advantages and challenges
"""

past_solutions_template = """
Based on the client's current situation and challenges in the transcript, identify 3 case studies that closely align with these issues. 
For each case study, explain how it was used to solve a similar problem in the past. 

Client Pain Points:
{transcript}

Relevant Case Studies:
{top_cases}

Provide:
- A list of relevant case studies
- For each case study, a detailed explanation of the solution used and its success
"""

tailored_solution_template = """
Given the client’s pain points (from the transcript) and their position in the market (from the background), 
propose a tailored solution based on insights from the past case studies. The solution should leverage relevant tools or methodologies from those case studies, 
while addressing the unique challenges the client faces. 

Client Pain Points:
{transcript}

Client Background:
{client_background}

Relevant Case Studies:
{top_cases}

Provide:
- A step-by-step approach to solving the client’s challenges
- The key methodologies or tools from past cases that will be applied
"""

outcomes_linking_template = """
Based on the proposed solution, link the expected outcomes to the client's strategic focus areas and objectives. 
Consider the impact on efficiency, cost savings, market positioning, or any other relevant metric that aligns with the client’s business goals. 

Proposed Solution:
{solution}

Client Background:
{client_background}

Provide:
- The expected impact of the solution on the client’s business, including measurable benefits
"""

# --- LangChain Setup with Memory for Contextual Interaction ---
def create_chain_of_thought_with_memory(config):
    # Initialize the model
    gpt_model = initialize_gpt(config)

    # Define PromptTemplates
    problem_understanding_prompt = PromptTemplate(template=problem_understanding_template, input_variables=["transcript"])
    market_positioning_prompt = PromptTemplate(template=market_positioning_template, input_variables=["client_background"])
    past_solutions_prompt = PromptTemplate(template=past_solutions_template, input_variables=["transcript", "top_cases"])
    tailored_solution_prompt = PromptTemplate(template=tailored_solution_template, input_variables=["transcript", "client_background", "top_cases"])
    outcomes_linking_prompt = PromptTemplate(template=outcomes_linking_template, input_variables=["solution", "client_background"])

    # Set up memory to maintain conversation context
    memory = ConversationBufferMemory(memory_key="history")

    # Create ConversationChain for dynamic, contextual responses
    conversation_chain = ConversationChain(
        llm=gpt_model, 
        memory=memory,
        verbose=True
    )

    # Return all chains for use
    return {
        "conversation_chain": conversation_chain,
        "problem_understanding_prompt": problem_understanding_prompt,
        "market_positioning_prompt": market_positioning_prompt,
        "past_solutions_prompt": past_solutions_prompt,
        "tailored_solution_prompt": tailored_solution_prompt,
        "outcomes_linking_prompt": outcomes_linking_prompt
    }

# --- Full Business Development Chain of Thought Reasoning with Memory ---
def generate_bd_solution_with_interactive_conversation(client_background, transcript, top_cases, config):
    # Get the chains with memory for talk-back feature
    chains = create_chain_of_thought_with_memory(config)

        # Step 2: Generate market positioning for the client
    market_positioning_response = chains["conversation_chain"].run(input=chains["market_positioning_prompt"].format(client_background=client_background))

    # Step 1: Generate problem understanding from the transcript
    problem_understanding_response = chains["conversation_chain"].run(input=chains["problem_understanding_prompt"].format(transcript=transcript))



    # Step 3: Map past solutions to current challenges
    past_solutions_response = chains["conversation_chain"].run(input=chains["past_solutions_prompt"].format(transcript=transcript, top_cases=top_cases))

    # Step 4: Propose tailored solutions
    tailored_solution_response = chains["conversation_chain"].run(input=chains["tailored_solution_prompt"].format(transcript=transcript, client_background=client_background, top_cases=top_cases))

    # Step 5: Link the proposed solution to strategic outcomes
    outcomes_response = chains["conversation_chain"].run(input=chains["outcomes_linking_prompt"].format(solution=tailored_solution_response, client_background=client_background))

    # Return all generated responses along with the context for further interaction
    return {
        "problem_understanding": problem_understanding_response,
        "market_positioning": market_positioning_response,
        "past_solutions": past_solutions_response,
        "tailored_solution": tailored_solution_response,
        "outcomes": outcomes_response,
        "conversation_memory": chains["conversation_chain"].memory
    }

# --- Interactive Talk-Back Function ---
def talk_back_interaction(config, client_background, transcript, top_cases):
    # Step 1: Get the initial setup for conversation
    chains = create_chain_of_thought_with_memory(config)

    # Step 2: Initialize conversation with the initial context (problem understanding, market positioning, etc.)
    initial_response = generate_bd_solution_with_interactive_conversation(client_background, transcript, top_cases, config)
    
    print("Initial Solution Generated:")
    print(f"Problem Understanding: {initial_response['problem_understanding']}")
    print(f"Market Positioning: {initial_response['market_positioning']}")
    print(f"Past Solutions: {initial_response['past_solutions']}")
    print(f"Tailored Solution: {initial_response['tailored_solution']}")
    print(f"Outcomes: {initial_response['outcomes']}")
    print("\nYou can now interact with the assistant by typing your questions or inputs.")
    
    # Step 3: Start the interactive talk-back session
    while True:
        user_input = input("\nType your message (or 'exit' to quit): ")
        
        # Exit condition
        if user_input.lower() == 'exit':
            print("Ending the conversation.")
            break
        
        # Generate a response considering the new input and memory context
        assistant_response = chains["conversation_chain"].run(input=user_input)
        
        # Display assistant response
        print("\nAssistant Response:")
        print(assistant_response)
        
        # Save the input-output pair to memory
        chains["conversation_chain"].memory.save_context({"input": user_input}, {"output": assistant_response})







