from pipeline1 import pipeline1, load_config
from pipeline2 import pipeline2, load_paths
from backend.pipeline3 import create_chain_of_thought_with_memory, generate_bd_solution_with_interactive_conversation
import streamlit as st

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'processed_transcript' not in st.session_state:
        st.session_state.processed_transcript = False
    if 'chains' not in st.session_state:
        st.session_state.chains = None
    if 'initial_response' not in st.session_state:
        st.session_state.initial_response = None
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""

def clear_input():
    """Callback to clear input after submission"""
    st.session_state.user_input = ""

def process_transcript(transcript_input, config, paths):
    """Process the transcript and generate initial response"""
    transcript, transcript_report, client_background = pipeline1(transcript_input, config)
    top_cases = pipeline2(transcript_report, config, paths)
    
    # Initialize conversation chains
    chains = create_chain_of_thought_with_memory(config)
    st.session_state.chains = chains
    
    # Generate initial response
    initial_response = generate_bd_solution_with_interactive_conversation(
        client_background, transcript, top_cases, config
    )
    
    return initial_response

def display_initial_response(initial_response):
    """Display the initial analysis results"""
    st.header("Initial Solution Generated")
    st.write(f"**Problem Understanding:** {initial_response['problem_understanding']}")
    st.write(f"**Market Positioning:** {initial_response['market_positioning']}")
    st.write(f"**Past Solutions:** {initial_response['past_solutions']}")
    st.write(f"**Tailored Solution:** {initial_response['tailored_solution']}")
    st.write(f"**Outcomes:** {initial_response['outcomes']}")

def display_chat_history():
    """Display the chat history"""
    st.write("### Conversation History")
    for role, message in st.session_state.chat_history:
        st.write(f"**{role}:** {message}")

def handle_user_input():
    """Process user input and generate response"""
    if st.session_state.user_input.strip():
        # Generate response using the conversation chain
        assistant_response = st.session_state.chains["conversation_chain"].run(
            input=st.session_state.user_input
        )
        # Add to chat history
        st.session_state.chat_history.append(("You", st.session_state.user_input))
        st.session_state.chat_history.append(("Assistant", assistant_response))
        # Clear the input
        clear_input()

def talk_back_interaction_streamlit():
    st.title("Business Development Assistant")
    
    # Initialize session state
    initialize_session_state()
    
    # Load configurations and paths (only once)
    config = load_config()
    paths = load_paths()

    # Only show transcript input if we haven't processed a transcript yet
    if not st.session_state.processed_transcript:
        st.header("Step 1: Provide Client Call Transcript")
        transcript_input = st.text_area(
            "Paste the client call transcript below:",
            placeholder="Paste transcript here...",
            height=200,
            key="transcript_input"
        )

        if st.button("Process Transcript", key="process_button"):
            if transcript_input.strip():
                with st.spinner("Processing transcript..."):
                    # Process transcript and store results
                    st.session_state.initial_response = process_transcript(transcript_input, config, paths)
                    st.session_state.processed_transcript = True
                st.success("Transcript processed successfully!")
                st.rerun()
            else:
                st.error("Please paste a transcript before processing.")
                
    else:
        # Display the initial response
        if st.session_state.initial_response:
            display_initial_response(st.session_state.initial_response)
            
            st.divider()
            
            # Interactive chat interface
            st.subheader("Interactive Talk-Back Session")
            
            # Display existing chat history
            display_chat_history()
            
            # Chat input with callback
            st.text_input(
                "Type your message:",
                key="user_input",
                on_change=handle_user_input,
                value=st.session_state.user_input
            )
            
            # Reset button
            if st.button("Start New Session", key="reset_button"):
                # Reset all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    talk_back_interaction_streamlit()