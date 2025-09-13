#!/usr/bin/env python3

import streamlit as st
import logging
import sys
from datetime import datetime

# Configure logging to CLI only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import campaign assistant components
from core.optimization_suggestion_engine.optimization_suggestion_engine import OptimizationSuggestionEngine
from core.conversation_manager.conversation_manager import ConversationManager
from core.migration_module.migration_module import MigrationModule
from core.data_processor.data_processor import DataProcessor
from core.generator.response_generator import ResponseGenerator
from external.api_clients import (
    TaboolaHistoricalDataClient,
    FacebookApiClient,
    TaboolaApiClient
)

# Page config
st.set_page_config(
    page_title="Taboola Campaign Assistant",
    page_icon="🎯",
    layout="wide"
)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'conversation_manager' not in st.session_state:
        st.session_state.conversation_manager = None
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'is_initialized' not in st.session_state:
        st.session_state.is_initialized = False
    
    if 'current_task' not in st.session_state:
        st.session_state.current_task = 'optimization'


def initialize_components(task='optimization'):
    """Initialize campaign assistant components."""
    try:
        with st.spinner('🚀 Initializing Campaign Assistant...'):
            logging.info(f"Initializing components for task: {task}")
            
            # Initialize API clients and core modules
            historical_data_client = TaboolaHistoricalDataClient()
            taboola_client = TaboolaApiClient()
            facebook_client = FacebookApiClient()
            source_clients = {'facebook': facebook_client}
            suggestion_engine = OptimizationSuggestionEngine(historical_data_client=historical_data_client)
            migration_module = MigrationModule(taboola_client=taboola_client, source_clients=source_clients)
            data_processor = DataProcessor(historical_data_client=historical_data_client)
            response_generator = ResponseGenerator()
            
            # Create conversation manager
            conversation_manager = ConversationManager(
                suggestion_engine=suggestion_engine,
                migration_module=migration_module,
                data_processor=data_processor,
                response_generator=response_generator,
                task=task
            )
            
            st.session_state.conversation_manager = conversation_manager
            st.session_state.is_initialized = True
            st.session_state.current_task = task
            
            # Start initial conversation
            ai_response = conversation_manager.handle_message("Hello")
            st.session_state.messages = [
                {"role": "assistant", "content": ai_response}
            ]
            
            logging.info("Campaign Assistant initialized successfully")
            st.success("✅ Campaign Assistant initialized successfully!")
            
    except Exception as e:
        error_msg = f"Failed to initialize: {str(e)}"
        logging.error(error_msg)
        st.error(error_msg)
        st.session_state.is_initialized = False


def clean_message_content(message):
    """Clean message content to prevent font/rendering issues."""
    if not message:
        return ""
    
    # Strip whitespace and normalize spaces
    cleaned = message.strip()
    cleaned = ' '.join(cleaned.split())
    
    # Remove any potential problematic characters
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\t')
    
    return cleaned


def handle_user_message(user_input):
    """Handle user input and get AI response."""
    if not user_input.strip():
        return
    
    if not st.session_state.conversation_manager:
        st.error("System not initialized. Please restart the application.")
        return
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        logging.info(f"Processing user message: {user_input}")
        ai_response = st.session_state.conversation_manager.handle_message(user_input)
        # Clean the AI response before storing
        clean_response = clean_message_content(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": clean_response})
        logging.info("AI response generated successfully")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logging.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.title("🎯 Taboola Campaign Assistant")
    st.markdown("*AI-powered campaign optimization and migration assistant*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Task selection
        task_options = {
            'optimization': '📈 Campaign Optimization',
            'migration': '🔄 Campaign Migration'
        }
        
        selected_task = st.selectbox(
            "Select Task:",
            options=list(task_options.keys()),
            format_func=lambda x: task_options[x],
            index=0 if st.session_state.current_task == 'optimization' else 1
        )
        
        # Initialize or reinitialize if task changed
        if not st.session_state.is_initialized or selected_task != st.session_state.current_task:
            if st.button("🚀 Initialize Assistant", type="primary", use_container_width=True):
                st.session_state.messages = []  # Clear messages
                initialize_components(selected_task)
                st.rerun()
        
        st.divider()
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        with col2:
            if st.button("🔄 Restart", use_container_width=True):
                if st.session_state.is_initialized:
                    st.session_state.messages = []
                    initialize_components(st.session_state.current_task)
                    st.rerun()
        
        st.divider()
        
        # Status
        st.subheader("📊 Status")
        if st.session_state.is_initialized:
            st.success("✅ System Ready")
            st.info(f"📋 Current Task: {task_options[st.session_state.current_task]}")
            st.metric("💬 Messages", len(st.session_state.messages))
        else:
            st.warning("⚠️ Not Initialized")
        
        st.divider()
        
        # Instructions
        st.subheader("💡 Quick Start")
        if selected_task == 'optimization':
            st.markdown("""
            **Steps:**
            1. Say "create campaign"
            2. Provide campaign URL
            3. Enter daily budget
            4. Set target CPA
            5. Choose platform
            """)
        else:
            st.markdown("""
            **Steps:**
            1. Say "migrate campaign"
            2. Specify source platform
            3. Provide campaign ID
            """)
        
        # Tips
        st.success("⚡ **Just press Enter to send** - No buttons needed!")
    
    # Main chat area
    if st.session_state.is_initialized:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.text(message["content"])
        
        # Chat input with Enter key support (no Send button needed!)
        if prompt := st.chat_input(
            "💬 Type your message and press Enter...",
            disabled=not st.session_state.is_initialized
        ):
            # Display user message immediately
            with st.chat_message("user"):
                st.text(prompt)
            
            # Process the message
            handle_user_message(prompt)
            
            # Display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if st.session_state.messages:
                        latest_message = st.session_state.messages[-1]
                        if latest_message["role"] == "assistant":
                            st.text(latest_message["content"])
            
            st.rerun()
    
    else:
        # Not initialized - show welcome message
        st.info("👈 **Welcome!** Please select a task and click 'Initialize Assistant' to get started.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📈 Campaign Optimization
            
            Get AI-powered recommendations for:
            - **URL Analysis** - Validate campaign URLs
            - **Budget Optimization** - Smart budget suggestions  
            - **CPA Targeting** - Cost-per-acquisition guidance
            - **Platform Selection** - Desktop, Mobile, or Both
            """)
        
        with col2:
            st.markdown("""
            ### 🔄 Campaign Migration
            
            Seamlessly transfer campaigns:
            - **Cross-Platform** - Facebook to Taboola
            - **Data Mapping** - Automatic schema conversion
            - **Validation** - Ensure migration accuracy
            - **Reporting** - Detailed migration results
            """)
        
        # Demo section
        with st.expander("🎬 See it in action"):
            st.markdown("""
            **Example conversation:**
            
            👤 **You:** "create campaign"
            
            🤖 **AI:** "Great! Let's create your campaign. What's your campaign URL?"
            
            👤 **You:** "https://example.com"
            
            🤖 **AI:** "Perfect! Now, what's your daily budget?"
            
            *...and so on*
            """)


if __name__ == "__main__":
    main()