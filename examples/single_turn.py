"""Run with TOKENFLOW_API_KEY and OPENAI_API_KEY set in the environment."""

import os

from orchya_tokenflow import TokenFlowClient


with TokenFlowClient(os.environ["TOKENFLOW_API_KEY"], os.environ["OPENAI_API_KEY"]) as client:
    answer = client.complete("Reply with one short greeting.", model="gpt-4o-mini")
    print(answer.text)
    print("model:", answer.routed_model, "usage:", answer.usage)
