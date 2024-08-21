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


class QuestionAnswer(BaseModel):
    question: str = Field(...)
    answer: list[Fact] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self) -> "QuestionAnswer":
        self.answer = [fact for fact in self.answer if len(fact.substring_quote) > 0]
        return self


def ask_expert(question: str, expert: Expert, context: Optional[str]):
    return client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "system", "content": expert.__doc__}]
    )
