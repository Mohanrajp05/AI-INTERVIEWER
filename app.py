import streamlit as st
from openai import OpenAI, APIConnectionError
import time
import os
from streamlit_js_eval import streamlit_js_eval

# Setting up the Streamlit page configuration
st.set_page_config(page_title="StreamlitChatMessageHistory", page_icon="💬")
st.title("AI INTERVIEWER")

MAX_USER_MESSAGES = 9
CHAT_CONTEXT_TURNS = 6

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback_result" not in st.session_state:
    st.session_state.feedback_result = None
if "feedback_error" not in st.session_state:
    st.session_state.feedback_error = None
if "monitoring" not in st.session_state:
    st.session_state.monitoring = {
        "total_requests": 0,
        "chat_requests": 0,
        "feedback_requests": 0,
        "successes": 0,
        "failures": 0,
        "total_latency_ms": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }


def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True
    st.session_state.feedback_result = None
    st.session_state.feedback_error = None

    st.subheader('Personal information', divider='rainbow')


def build_chat_messages(max_turns: int = CHAT_CONTEXT_TURNS):
    messages = st.session_state.messages
    if len(messages) <= 1:
        return messages

    system_message = messages[0]
    recent_messages = messages[-(max_turns * 2):]
    return [system_message, *recent_messages]


def get_api_key():
    return st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")


def update_monitoring(request_type: str, success: bool, latency_ms: float, usage=None):
    metrics = st.session_state.monitoring
    metrics["total_requests"] += 1
    metrics["total_latency_ms"] += latency_ms

    if request_type == "chat":
        metrics["chat_requests"] += 1
    elif request_type == "feedback":
        metrics["feedback_requests"] += 1

    if success:
        metrics["successes"] += 1
    else:
        metrics["failures"] += 1

    if usage:
        metrics["prompt_tokens"] += int(getattr(usage, "prompt_tokens", 0) or 0)
        metrics["completion_tokens"] += int(getattr(usage, "completion_tokens", 0) or 0)
        metrics["total_tokens"] += int(getattr(usage, "total_tokens", 0) or 0)


def render_monitoring_panel():
    metrics = st.session_state.monitoring
    total_requests = metrics["total_requests"]
    avg_latency_ms = (metrics["total_latency_ms"] / total_requests) if total_requests else 0.0
    success_rate = (metrics["successes"] / total_requests * 100) if total_requests else 0.0

    st.sidebar.subheader("Monitoring")
    st.sidebar.metric("Requests", total_requests)
    st.sidebar.metric("Success Rate", f"{success_rate:.1f}%")
    st.sidebar.metric("Avg Latency", f"{avg_latency_ms:.0f} ms")
    st.sidebar.metric("Failures", metrics["failures"])
    st.sidebar.metric("Total Tokens", metrics["total_tokens"])
    st.sidebar.caption(
        f"Prompt: {metrics['prompt_tokens']} | Completion: {metrics['completion_tokens']}"
    )


render_monitoring_panel()


# Setup stage for collecting user details
if not st.session_state.setup_complete:
    st.subheader('Personal Information', divider='rainbow')

    # Initialize session state for personal information
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

   
    # Get personal information input
    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40)
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=200)
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=200)

    
    # Company and Position Section
    st.subheader('Company and Position', divider='rainbow')

    # Initialize session state for company and position information and setting default values 
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst", "Full Stack Developer", "Product Manager"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst", "Full Stack Developer", "Product Manager").index(st.session_state["position"])
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"])
    )



    # Button to complete setup
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

# Interview phase
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
    """
    Start by introducing yourself
    """,
    icon="👋",
    )

    api_key = get_api_key()
    if not api_key:
        st.error("Missing OPENAI_API_KEY. Add it in Streamlit secrets or environment variables.")
        st.stop()

    client = OpenAI(
        api_key=api_key,
        timeout=30,  # seconds
        max_retries=2,
    )

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"

    # Initializing the system prompt for the chatbot
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system",
            "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                        f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                        f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                        f"at the company {st.session_state['company']}")
        }]

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle user input and OpenAI response
    # Put a max_chars limit
    if st.session_state.user_message_count < MAX_USER_MESSAGES:
        if prompt := st.chat_input("Your response", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                max_attempts = 3
                delay = 1  # initial delay in seconds
                response = ""
                request_started = time.perf_counter()
                for attempt in range(1, max_attempts + 1):
                    try:
                        request_messages = build_chat_messages()
                        with st.spinner("Thinking..."):
                            completion = client.chat.completions.create(
                                model=st.session_state["openai_model"],
                                messages=[
                                    {"role": m["role"], "content": m["content"]}
                                    for m in request_messages
                                ],
                            )
                            response = completion.choices[0].message.content or ""
                            st.markdown(response)
                        latency_ms = (time.perf_counter() - request_started) * 1000
                        update_monitoring(
                            request_type="chat",
                            success=True,
                            latency_ms=latency_ms,
                            usage=completion.usage,
                        )
                        break
                    except APIConnectionError:
                        if attempt == max_attempts:
                            st.error(
                                "Connection error when contacting OpenAI. "
                                "Check your network, proxy, and OPENAI_API_KEY in Streamlit secrets."
                            )
                            latency_ms = (time.perf_counter() - request_started) * 1000
                            update_monitoring(
                                request_type="chat",
                                success=False,
                                latency_ms=latency_ms,
                            )
                            response = ""
                        else:
                            time.sleep(delay)
                            delay *= 2
                    except Exception as e:
                        st.error(f"OpenAI request failed: {e}")
                        latency_ms = (time.perf_counter() - request_started) * 1000
                        update_monitoring(
                            request_type="chat",
                            success=False,
                            latency_ms=latency_ms,
                        )
                        response = ""
                        break

            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Increment the user message count
            st.session_state.user_message_count += 1

    # End interview after configured number of user responses
    if st.session_state.user_message_count >= MAX_USER_MESSAGES:
        st.session_state.chat_complete = True

# Show "Get Feedback" 
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback", divider='rainbow')

    if st.session_state.feedback_result is None and st.session_state.feedback_error is None:
        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

        api_key = get_api_key()
        if not api_key:
            st.error("Missing OPENAI_API_KEY. Add it in Streamlit secrets or environment variables.")
            st.stop()

        feedback_client = OpenAI(
            api_key=api_key,
            timeout=30,  # seconds
            max_retries=2,
        )

        try:
            request_started = time.perf_counter()
            with st.spinner("Generating feedback..."):
                feedback_completion = feedback_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
                                                 Before the feedback, give a score from 1 to 10.
                         Follow this format:
                                                 Overall Score: //Your score
                                                 Feedback: //Here you put your feedback
                                                 Give only the feedback. Do not ask any additional questions.
                          """},
                                                {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool, and you should not engage in any conversation: {conversation_history}"}
                    ]
                )
            latency_ms = (time.perf_counter() - request_started) * 1000
            update_monitoring(
                request_type="feedback",
                success=True,
                latency_ms=latency_ms,
                usage=feedback_completion.usage,
            )
            st.session_state.feedback_result = feedback_completion.choices[0].message.content
        except Exception as e:
            latency_ms = (time.perf_counter() - request_started) * 1000
            update_monitoring(
                request_type="feedback",
                success=False,
                latency_ms=latency_ms,
            )
            st.session_state.feedback_error = f"Feedback generation failed: {e}"

    if st.session_state.feedback_error:
        st.error(st.session_state.feedback_error)
    elif st.session_state.feedback_result:
        st.write(st.session_state.feedback_result)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")
