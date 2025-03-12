import base64
import logging
import sys
import time

import streamlit as st
import tomllib
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import openai
from openai.types.beta import Assistant
from openai.types.responses import ResponseTextDeltaEvent
from openai.types.responses.file_search_tool_param import FileSearchToolParam

log = logging.getLogger("ai")

st.set_page_config(
    page_title="OpenAI Assistant Chat",
    page_icon="images/assistant.webp",
    menu_items={
        # "Get Help": "https://www.example.com/",
        # "Report a bug": "https://www.example.com/",
        "About": f"Logged in as *{st.session_state['user']}*"
        if "user" in st.session_state
        else "Not logged in"
    },
)


@st.cache_resource
def load_env() -> dict:
    env = sys.argv[1] if len(sys.argv) >= 2 else "dev"
    with open(".streamlit/env.toml", "rb") as f:
        return tomllib.load(f)[env]


@st.cache_resource
def load_pubkey(filename: str) -> ed25519.Ed25519PublicKey:
    with open(filename, "rb") as f:
        keydata = f.read()
    key = serialization.load_pem_public_key(keydata)
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise TypeError(f"{filename} is not an ed25519 public key")
    return key


def verify_signature(message: bytes, signature: bytes):
    pubkey = load_pubkey(load_env()["pubkey"])
    try:
        pubkey.verify(signature, message)
        return True
    except InvalidSignature:
        log.exception("Invalid signature")
        return False


@st.cache_resource
def create_client() -> openai.OpenAI:
    return openai.OpenAI()

@st.cache_resource
def convert_tools(assistant: Assistant) -> list[FileSearchToolParam] | None:
    if assistant.tool_resources and assistant.tool_resources.file_search and (vector_store_ids := assistant.tool_resources.file_search.vector_store_ids):
        return [{"type": "file_search", "vector_store_ids": vector_store_ids}]
    return None


# Update on every interaction
st.session_state.last_interaction = time.time()

idle = load_env()["idle"]


@st.fragment(run_every=idle["poll"])
def idle_timeout():
    if time.time() - st.session_state.last_interaction > idle["timeout"]:
        st.session_state.timed_out = True
        del st.session_state.user
        st.rerun()


def chatbot():
    idle_timeout()

    st.image("images/logo.png")

    client = create_client()

    if "assistant" not in st.session_state:
        st.session_state.assistant = client.beta.assistants.retrieve(load_env()["assistant_id"])
    if "history" not in st.session_state:
        st.session_state.history = []
    if "previous_response_id" not in st.session_state:
        st.session_state.previous_response_id = None

    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="images/assistant.png"):
            with client.responses.stream(
              model=st.session_state.assistant.model,
              instructions=st.session_state.assistant.instructions,
              input=prompt,
              tools=convert_tools(st.session_state.assistant) or openai.NOT_GIVEN,
              previous_response_id=st.session_state.previous_response_id,
              truncation="auto",
            ) as stream:
                response = st.write_stream(event.delta for event in stream if isinstance(event, ResponseTextDeltaEvent))
            st.session_state.previous_response_id = stream.get_final_response().id

        st.session_state.history.append({"role": "assistant", "content": response})


def login():
    if "user" not in st.session_state:
        if "message" in st.query_params and "signature" in st.query_params:
            message = st.query_params.message
            if verify_signature(
                message.encode(),
                base64.urlsafe_b64decode(st.query_params.signature.encode()),
            ):
                user, timestamp = message.split(":")
                if int(timestamp) > time.time():
                    st.session_state.user = user
                    return
        st.error("Invalid login token.")
        st.stop()


if st.session_state.get("timed_out"):
    st.error("Session timed out.")
    st.stop()

if "user" not in st.session_state:
    login()
    st.rerun()


chatbot()
