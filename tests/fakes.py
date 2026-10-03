"""Fake stages for runner tests."""

from __future__ import annotations

from collections.abc import Callable

from youkelele.stage import Stage, StageContext


def make_fake_stage(
    name: str,
    requires: tuple[str, ...] = (),
    produces: tuple[str, ...] = (),
    body: Callable[[StageContext], None] | None = None,
    fail: bool = False,
) -> Stage:
    _requires, _produces = tuple(requires), tuple(produces)

    class FakeStage(Stage):
        requires = _requires
        produces = _produces

        def run(self, ctx: StageContext) -> None:
            if fail:
                raise RuntimeError("boom")
            if body is not None:
                body(ctx)
            for key in self.produces:
                ctx.output(key).write_text(key, encoding="utf-8")

    FakeStage.name = name
    return FakeStage()
