import re
from typing import Optional
from pydantic import Field, BaseModel, model_validator, ValidationInfo
from openai import OpenAI
import instructor

client = instructor.from_openai(OpenAI())


class Expert:
    pass


class Fact(BaseModel):
    fact: str = Field(...)
    substring_quote: list[str] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self, info: ValidationInfo) -> "Fact":
        text_chunks = info.context.get("text_chunk", None)
        spans = list(self.get_spans(text_chunks))
        self.substring_quote = [text_chunks[span[0] : span[1]] for span in spans]
        return self

    def get_spans(self, context):
        for quote in self.substring_quote:
            yield from self._get_span(quote, context)

    def _get_span(self, quote, context):
        for match in re.finditer(re.escape(quote), context):
            yield match.span()


class QuestionAnswerWithSources(BaseModel):
    question: str = Field(...)
    answer: list[Fact] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self) -> "QuestionAnswer":
        self.answer = [fact for fact in self.answer if len(fact.substring_quote) > 0]
        return self


class QuestionAnswer(BaseModel):
    answer: str = Field(...)


def ask_expert(
    question: str,
    expert: Expert,
    history: Optional[str] = None,
    context: Optional[str] = None,
):
    messages = [{"role": "system", "content": expert.__doc__}]
    if context:
        messages.append({"role": "user", "content": context})
    if history:
        messages.append({"role": "user", "content": history})
    messages.append({"role": "user", "content": question})
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        response_model=QuestionAnswer,
        validation_context={"text_chunk": context},
    )


def ask_expert_with_sources(
    question: str,
    expert: Expert,
    history: Optional[str] = None,
    context: Optional[str] = None,
):
    messages = [{"role": "system", "content": expert.__doc__}]
    if context:
        messages.append({"role": "user", "content": context})
    if history:
        messages.append({"role": "user", "content": history})
    messages.append({"role": "user", "content": question})
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_model=QuestionAnswerWithSources,
        validation_context={"text_chunk": context},
    )


__all__ = ["Expert", "Fact", "QuestionAnswer", "ask_expert"]
