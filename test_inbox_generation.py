import json

from services.simulation_generator import (
    generate_backend_inbox_task,
)


if __name__ == "__main__":
    try:
        inbox_task = generate_backend_inbox_task(
            company_name="CareerGrid Technologies"
        )

        print("INBOX GENERATION SUCCESSFUL:\n")

        print(
            json.dumps(
                inbox_task,
                indent=4,
                ensure_ascii=False,
            )
        )

    except Exception as error:
        print("INBOX GENERATION FAILED:")
        print(type(error).__name__)
        print(error)