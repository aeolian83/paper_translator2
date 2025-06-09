import os
import time
from dotenv import load_dotenv
from typing import List
from autogen import UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager

from utils import (
    fetch_arxiv_papers,
    parse_arxiv_response,
)
from prompt_template_term import (
    paper_writer_instruction,
    translator_instruction,
    evaluator_instruction,
)

load_dotenv(dotenv_path="/mnt/t7/dnn/llm_practicing/.env")



class AITranslator:
    def __init__(self):
        self.gpt4omini_config_list = [
            {
                "model": "gpt-4o-mini",
                "api_key": os.environ["OPENAI_API_KEY"],
                # "cache_seed": 42,
                "temperature": 0,
                "top_p": 0.8,
                "timeout": 120,
            },
        ]
        self.gpt4omini_high_temp_config_list = [
            {
                "model": "gpt-4o-mini",
                "api_key": os.environ["OPENAI_API_KEY"],
                # "cache_seed": 42,
                "temperature": 1.0,
                "top_p": 0.8,
                "timeout": 120,
            },
        ]
        self.gpt4_config_list = [
            {
                "model": "gpt-4.1",
                "api_key": os.environ["OPENAI_API_KEY"],
                # "cache_seed": 42,
                "temperature": 0.1,
                "top_p": 0.8,
                "timeout": 120,
            },
        ]
        self.gpt4o_config_list = [
            {
                "model": "gpt-4o",
                "api_key": os.environ["OPENAI_API_KEY"],
                # "cache_seed": 42,
                "temperature": 0.1,
                "top_p": 0.8,
                "timeout": 120,
            },
        ]
        self.gpt4o_high_temp_config_list = [
            {
                "model": "gpt-4o",
                "api_key": os.environ["OPENAI_API_KEY"],
                # "cache_seed": 42,
                "temperature": 0.5,
                "top_p": 0.9,
                "timeout": 120,
            },
        ]

    def gen_translate_sentences(self, terms: str, arxiv_summary):
        # def generate_and_translate_ai_sentences(self, terms: List[str]):
        # response_text = fetch_arxiv_papers(", ".join(terms))

        time.sleep(10)
        initializer = UserProxyAgent(
            name="Init",
            code_execution_config=False,
            # code_execution_config={
            #     "work_dir": "workspace",
            #     "use_docker": False,
            #     "last_n_messages": 3,
            # },
        )

        writer = AssistantAgent(
            "Writer",
            # llm_config={"config_list": self.gpt4omini_high_temp_config_list},
            llm_config={"config_list": self.gpt4o_high_temp_config_list},
            system_message=paper_writer_instruction(terms, arxiv_summary),
        )

        translator = AssistantAgent(
            "Translator",
            # llm_config={"config_list": self.gpt4_config_list},
            llm_config={"config_list": self.gpt4o_config_list},
            system_message=translator_instruction(terms),
        )

        evaluator = AssistantAgent(
            "Evaluator",
            # llm_config={"config_list": self.gpt4omini_config_list},
            llm_config={"config_list": self.gpt4o_config_list},
            system_message=evaluator_instruction(terms),
        )

        executor = AssistantAgent(
            "Executor",
            # llm_config={"config_list": self.gpt4omini_config_list},
            llm_config={"config_list": self.gpt4o_config_list},
            system_message="""If the score is less than 8: Response "translator". If the score is 9 or greater: Response "final output".""",
        )

        def state_transition(last_speaker, groupchat):
            messages = groupchat.messages

            if last_speaker is initializer:
                # init -> writer
                return writer
            elif last_speaker is writer:
                # writer: writer -> translator
                return translator
            elif last_speaker is translator:
                # translator: translator -> evaluator
                return evaluator
            elif last_speaker is evaluator:
                # evaluator: evaluator -> executor
                return executor
            elif last_speaker is executor:
                # evaluator --(low score)--> translator
                if messages[-1]["content"] == "translator":
                    return translator
            elif last_speaker == "final_output":
                # evaluator --(hight score)--> final output
                return None

        groupchat = GroupChat(
            agents=[initializer, writer, translator, evaluator, executor],
            messages=[],
            max_round=10,
            speaker_selection_method=state_transition,
        )
        manager = GroupChatManager(
            groupchat=groupchat, llm_config={"config_list": self.gpt4_config_list}
        )

        sentences = initializer.initiate_chat(
            manager,
            message="Topic: Generating professional English sentences.",
            clear_history=True,
        )

        return arxiv_summary, sentences
