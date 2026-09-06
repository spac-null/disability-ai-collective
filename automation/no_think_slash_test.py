#!/usr/bin/env python3
"""no_think_slash_test.py -- a prompt beginning with "/" is a command, not a question.

MEASURED, not theorised. Against the real CLI, on the argument and on stdin alike:

    "/no_think say OK"  ->  result 'Unknown command: /no_think'   (26 chars, exit 0)
    "say OK"            ->  result 'OK'

`no_think=True` prepends "/no_think " -- a Qwen directive, harmless over HTTP where the
model just reads an unknown token. Claim extraction passes no_think=True, so from the
Phase 2B transport migration onward EVERY article's extraction received that 26-character
reply, failed to parse, and was reported as a Fact Check failure. The single candidate that
ever reached the stage was recorded as "FACT_CHECK HOLD, blocking contradiction(s): []" --
an editorial-looking rejection of an article nothing had checked.

Two layers: the marker is not sent over this transport at all, and no prompt reaching the
CLI may begin with a slash whatever its origin.

Stdlib only, no network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claude_cli_provider as ccp

FAILURES = []
CHECKS = [0]
HERE = os.path.dirname(os.path.abspath(__file__))


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + detail) if detail else ""))
    if not cond:
        FAILURES.append(label)


print("test_the_no_think_marker_is_not_sent_over_the_subscription")
llm = open(os.path.join(HERE, "orchestrator", "llm.py")).read()
i_content = llm.index('content = ("/no_think " if no_think else "") + user_prompt')
i_route = llm.index("return self._call_claude_subscription(")
check("the marker is still built for the HTTP path", i_content < i_route)
seg = llm[i_route:i_route + 400]
check("the subscription branch forwards the UNPREFIXED prompt",
      "system_prompt, user_prompt, wire_model" in seg, seg[:160])
check("it does not forward the prefixed content", "system_prompt, content," not in seg)
check("the reason is recorded at the call site",
      "Unknown command" in llm and "slash command" in llm.lower())
check("the HTTP path still receives the marker",
      '"model": wire_model' in llm and 'content = ("/no_think "' in llm,
      "local Qwen still needs it")


print("\ntest_no_prompt_reaching_the_CLI_may_begin_with_a_slash")
n = ccp._neutralise_leading_slash
check("a leading slash is neutralised", n("/no_think hello").lstrip()[:1] != "/" or
      n("/no_think hello").startswith("\n"), repr(n("/no_think hello")[:20]))
check("the content is preserved exactly", n("/no_think hello").strip() == "/no_think hello")
check("ordinary text is untouched", n("The sky is blue.") == "The sky is blue.")
check("text merely containing a slash is untouched",
      n("Use the and/or form.") == "Use the and/or form.")
check("a path-like opening is protected too",
      n("/srv/data is the root.").startswith("\n"))
check("a fraction opening is protected too", n("/3 of the total.").startswith("\n"))
check("whitespace before the slash still counts", n("  /help me").startswith("\n"))
check("empty input is safe", n("") == "")
check("None is safe", n(None) == "")

src = open(os.path.join(HERE, "claude_cli_provider.py")).read()
# Scoped to complete(). A whole-file offset comparison reads the order backwards, because
# subprocess.run() first appears in auth_status(), defined above complete() -- the same
# trap that already bit the grounder-repair ordering check.
_body = src[src.index("    def complete("):]
check("complete() applies the guard before spawning",
      "user = _neutralise_leading_slash(user)" in _body
      and _body.index("user = _neutralise_leading_slash(user)")
          < _body.index("subprocess.run("))
check("the guard is documented as measured on both argument and stdin",
      "AND on stdin, both measured" in src)


print("\ntest_the_failure_signature_is_recorded")
check("the exact CLI reply is written down", "Unknown command" in src or
      "Unknown command" in llm)
check("its length is recorded, since that is what the artifact showed",
      "26" in llm, "the artifact said 'no JSON object in provider response (26 chars)'")


print("\n" + "-" * 60)
if FAILURES:
    print("NO_THINK SLASH: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d NO_THINK SLASH TESTS PASSED" % CHECKS[0])
