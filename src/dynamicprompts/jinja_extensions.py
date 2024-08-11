from __future__ import annotations

import logging
import random
from itertools import permutations
from typing import Any, Callable, Iterable, cast

from jinja2 import Environment, pass_environment
from jinja2.ext import Extension
from jinja2.nodes import CallBlock
from jinja2.parser import Parser

logger = logging.getLogger(__name__)


def choice(*items) -> Any:
    return random.choice(items)


def weighted_choice(*items) -> Any:
    population, weights = zip(*items)
    return random.choices(population, weights=weights)[0]


def flip_coin(first_result = True, second_result = False) -> bool:
    return random.choice([first_result, second_result])


def pick_multiple(items: Iterable[Any], returnLength: int | True = True) -> list[Any]:
    if returnLength is True:
        returnLength = random.randint(1, len(items))
    if returnLength == 0:
        return []
    if returnLength > len(items):
        return list(items)
    return random.sample(list(items), returnLength)


def permutation(
    items: Iterable[Any],
    low: int,
    high: int | None = None,
) -> list[Any]:
    vars: list[Any] = []
    if high is None:
        high = low

    for i in range(low, high + 1):
        vars.extend(permutations(items, i))

    return vars


@pass_environment
def wildcard(environment: Environment, wildcard_name: str) -> list[str]:
    from dynamicprompts.generators import CombinatorialPromptGenerator
    from dynamicprompts.wildcards import WildcardManager

    wm = cast(WildcardManager, environment.globals["wildcard_manager"])
    generator = cast(
        CombinatorialPromptGenerator,
        environment.globals["generators"]["combinatorial"],  # type: ignore
    )

    return [str(r) for r in generator.generate(wm.to_wildcard(wildcard_name))]


@pass_environment
def random_sample(environment: Environment, prompt: str) -> str:
    generator = environment.globals["generators"]["random"]  # type: ignore

    ps = generator.generate(prompt)
    return str(next(iter(ps)))


@pass_environment
def combinatorial_sample(environment: Environment, prompt: str) -> list[str]:
    generator = environment.globals["generators"]["combinatorial"]  # type: ignore

    return [str(p) for p in generator.generate(prompt)]


class PromptExtension(Extension):
    tags = {"prompt"}

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.extend(prompt_blocks=[])

    def parse(self, parser: Parser) -> CallBlock:
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(
            ("name:endprompt",),
            drop_needle=True,
        )
        node = CallBlock(
            self.call_method("_prompt", []),
            [],
            [],
            body,
        )
        node.set_lineno(lineno)
        return node

    def _prompt(self, caller: Callable) -> Any:
        value = caller()
        prompt_blocks = cast(list, self.environment.globals["prompt_blocks"])
        prompt_blocks.append(value)
        return value


DYNAMICPROMPTS_FUNCTIONS: dict[str, Any] = {
    "choice": choice,
    "weighted_choice": weighted_choice,
    "flip_coin": flip_coin,
    "pick_multiple": pick_multiple,
    "random": random.random,
    "randint": random.randint,
    "permutations": permutation,
    "wildcard": wildcard,
    "random_sample": random_sample,
    "all_combinations": combinatorial_sample,
}
