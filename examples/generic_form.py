"""Fill and read back a generic multi-field form."""
from pydantic import BaseModel

from navpy import Agent


class Confirmation(BaseModel):
    reference: str
    status: str


def main() -> None:
    agent = Agent(model="claude-3-5-sonnet", max_steps=12, max_cost_usd=0.40)
    result: Confirmation = agent.run(
        url="https://httpbin.org/forms/post",
        task=(
            "Fill the customer name with 'binniepiss', choose any size, submit "
            "the form, then extract the resulting reference and status."
        ),
        schema=Confirmation,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
