import uuid

import streamlit as st
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)

from backend import (
    stream_chat,
    get_all_threads,
    get_messages,
)

###########################################################################
# Page Config
###########################################################################

st.set_page_config(
    page_title="Agentic Chatbot",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Agentic Chatbot with LangGraph")

###########################################################################
# Session State
###########################################################################

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "loaded_thread" not in st.session_state:
    st.session_state.loaded_thread = None


###########################################################################
# Helper Functions
###########################################################################

def load_thread(thread_id: str):
    """
    Load one conversation from SQLite.
    """

    history = []

    messages = get_messages(thread_id)

    for message in messages:

        if isinstance(message, HumanMessage):

            history.append(
                {
                    "role": "user",
                    "content": message.content,
                }
            )

        elif isinstance(message, AIMessage):

            # Skip AI tool request messages.
            if message.tool_calls:
                continue

            history.append(
                {
                    "role": "assistant",
                    "content": message.content,
                }
            )

    st.session_state.messages = history
    st.session_state.thread_id = thread_id
    st.session_state.loaded_thread = thread_id


def new_chat():

    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.loaded_thread = None


###########################################################################
# Sidebar
###########################################################################

with st.sidebar:

    st.header("💬 Conversations")

    if st.button(
        "➕ New Chat",
        use_container_width=True,
    ):
        new_chat()
        st.rerun()

    st.divider()

    all_threads = get_all_threads()

    if not all_threads:

        st.info("No conversations yet.")

    else:

        for thread in reversed(all_threads):

            label = thread[:8] + "..."

            if st.button(
                label,
                key=thread,
                use_container_width=True,
            ):
                load_thread(thread)
                st.rerun()


###########################################################################
# Display Existing Conversation
###########################################################################

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


###########################################################################
# Chat Input
###########################################################################

user_input = st.chat_input("Ask me anything...")

if user_input:

    # ---------------------------------------------------------
    # Show user message
    # ---------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # ---------------------------------------------------------
    # Assistant
    # ---------------------------------------------------------

    with st.chat_message("assistant"):

        answer_placeholder = st.empty()

        final_answer = ""

        tool_container = st.container()

        #
        # Listen to backend events
        #
        for event in stream_chat(
            user_input,
            st.session_state.thread_id,
        ):

            ####################################################
            # Assistant Started
            ####################################################

            if event["type"] == "assistant_started":

                answer_placeholder.markdown(
                    "_Thinking..._"
                )

            ####################################################
            # Tool Started
            ####################################################

            elif event["type"] == "tool_started":

                with tool_container:

                    st.status(
                        f"🔧 Running `{event['tool_name']}`...",
                        expanded=False,
                    )

            ####################################################
            # Tool Finished
            ####################################################

            elif event["type"] == "tool_finished":

                with tool_container:

                    with st.expander(
                        f"🔧 {event['tool_name']}",
                        expanded=False,
                    ):

                        st.markdown("### Arguments")

                        st.json(
                            event["arguments"]
                        )

                        st.markdown("### Output")

                        output = event["output"]

                        if isinstance(output, str):

                            st.code(output)

                        else:

                            st.json(output)

            ####################################################
            # Final Assistant Message
            ####################################################

            elif event["type"] == "assistant_message":

                final_answer = event["content"]

                answer_placeholder.markdown(
                    final_answer
                )

        #
        # Save assistant message
        #

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": final_answer,
            }
        )


