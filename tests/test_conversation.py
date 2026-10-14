from sasoi.conversation import Conversation


def test_messages_keep_turns_in_order():
    conversation = Conversation()

    conversation.add_user_message("hello")
    conversation.add_assistant_message("Hi!")

    assert conversation.messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Hi!"},
    ]


def test_messages_cannot_modify_history():
    conversation = Conversation()

    conversation.messages.append({"role": "user", "content": "sneaky"})

    assert conversation.messages == []
