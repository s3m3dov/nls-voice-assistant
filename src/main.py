"""Voice assistant main entry point."""
from src.dialogue.chat import build_system_prompt, chat_stream


def main():
    """Main conversation loop."""
    print("Voice Assistant Ready! (Type 'quit' to exit)\n")

    messages = [{"role": "system", "content": build_system_prompt()}]

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            print("Assistant: ", end="", flush=True)
            for chunk in chat_stream(user_input, messages):
                print(chunk, end="", flush=True)
            print("\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
