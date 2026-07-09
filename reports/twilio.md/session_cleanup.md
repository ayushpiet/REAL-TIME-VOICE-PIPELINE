# Session Cleanup

## Post-Call Diagnostics
**Status:** BLOCKED BY EXTERNAL DEPENDENCY

Because a real call was never placed, a real call could never be concluded. Thus, we cannot capture real memory teardown, EventBus pruning, or lingering WebSocket tracking via real performance testing. We rely on the established CI coverage from `tests/test_conversation_state_machine.py`.
