from sasoi.conversation import Conversation


def test_messages_keep_turns_in_order():
    conversation = Conversation()

    conversation.add_user_message("what time is it?")
    conversation.add_assistant_message([{"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}])
    conversation.add_tool_results([{"type": "tool_result", "tool_use_id": "toolu_1", "content": "09:00"}])

    assert conversation.messages == [
        {"role": "user", "content": "what time is it?"},
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "09:00"}],
        },
    ]


def test_messages_cannot_modify_history():
    conversation = Conversation()

    conversation.messages.append({"role": "user", "content": "sneaky"})

    assert conversation.messages == []
