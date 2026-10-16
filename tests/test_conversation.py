from sasoi.conversation import Conversation


class TestConversation:
    def test_messages_keep_turns_in_order(self):
        conversation = Conversation()

        conversation.add_user_message("what time is it?")
        conversation.add_assistant_message([{"type": "tool_use"}])
        conversation.add_tool_results([{"type": "tool_result"}])

        assert conversation.messages == [
            {"role": "user", "content": "what time is it?"},
            {"role": "assistant", "content": [{"type": "tool_use"}]},
            {"role": "user", "content": [{"type": "tool_result"}]},
        ]

    def test_messages_cannot_modify_history(self):
        conversation = Conversation()

        conversation.messages.append({"role": "user", "content": "sneaky"})

        assert conversation.messages == []
