from attr import dataclass
import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_teddynote import logging
from langchain_teddynote.messages import random_uuid
from modules.agent import create_agent_executor
from dotenv import load_dotenv
from modules.handler import stream_handler

# API KEY 정보로드
load_dotenv()

# 프로젝트 이름
logging.langsmith("jmango-yp")

st.title("영농계획서 💬")
st.markdown(
    "영농계획서 작성을 도와드립니다"
)

# 대화기록을 저장하기 위한 용도로 생성
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ReAct Agent 초기화
if "react_agent" not in st.session_state:
    st.session_state["react_agent"] = None

# 사이드바 생성
with st.sidebar:
    # 초기화 버튼 생성
    clear_btn = st.button("대화 초기화")
    
    st.markdown("made by jmango(jmhanmu@gmail.com)")

    # 모델 선택 메뉴
    selected_model = st.selectbox("LLM 선택", ["gpt-4o", "gpt-4o-mini"], index=0)

    # 설정 버튼
    apply_btn = st.button("설정 완료", type="primary")

@dataclass
class ChatMessageWithType:
    chat_message: ChatMessage
    msg_type: str
    tool_name: str

# 이전 대화를 출력
def print_messages():
    for message in st.session_state["messages"]:
        if message.msg_type == "text":
            st.chat_message(message.chat_message.role).write(
                message.chat_message.content
            )
        elif message.msg_type == "tool_result":
            with st.expander(f"✅ {message.tool_name}"):
                st.markdown(message.chat_message.content)

# 새로운 메시지를 추가
def add_message(role, message, msg_type="text", tool_name=""):
    if msg_type == "text":
        st.session_state["messages"].append(
            ChatMessageWithType(
                chat_message=ChatMessage(role=role, content=message),
                msg_type="text",
                tool_name=tool_name,
            )
        )
    elif msg_type == "tool_result":
        st.session_state["messages"].append(
            ChatMessageWithType(
                chat_message=ChatMessage(
                    role="assistant", content=message
                ),
                msg_type="tool_result",
                tool_name=tool_name,
            )
        )

# 초기화 버튼이 눌리면...
if clear_btn:
    st.session_state["messages"] = []
    st.session_state["thread_id"] = random_uuid()

# 이전 대화 기록 출력
print_messages()

# 사용자의 입력
user_input = st.chat_input("단계별로 질문해주세요!")

# 경고 메시지를 띄우기 위한 빈 영역
warning_msg = st.empty()

# 설정 버튼이 눌리면...
if apply_btn:
    st.session_state["react_agent"] = create_agent_executor(
        model_name=selected_model,
        tools=[],  # 웹 검색 도구 제거
    )
    st.session_state["thread_id"] = random_uuid()

# 만약에 사용자 입력이 들어오면...
if user_input:
    agent = st.session_state["react_agent"]

    if agent is not None:
        config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
        # 사용자의 입력
        st.chat_message("user").write(user_input)

        with st.chat_message("assistant"):
            # 빈 공간(컨테이너)을 만들어서, 여기에 토큰을 스트리밍 출력한다.
            container = st.empty()

            ai_answer = ""
            container_messages, tool_args, agent_answer = stream_handler(
                container,
                agent,
                {
                    "messages": [
                        ("human", user_input),
                    ]
                },
                config,
            )

            # 대화기록을 저장한다.
            add_message("user", user_input)
            add_message("assistant", agent_answer)
    else:
        warning_msg.warning("사이드바에서 설정을 완료해주세요.")