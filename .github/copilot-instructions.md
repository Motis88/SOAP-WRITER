
⚠️ *FOR MAIN AGENT ONLY — SUBAGENTS MUST NOT FOLLOW THIS SECTION* ⚠️

# SUPER MANDATORY CRITICAL MAIN AGENT FEEDBACK LOOP
IF YOU ARE LAUNCHED AS A SUBAGENT - STOP NOW AND IGNORE THIS SECTION. DO NOT FOLLOW THESE INSTRUCTIONS.

## Rules
- The flow with the user MUST be a feedback loop using the vscode_askQuestions tool. After *every single* action or answer, call the vscode_askQuestions tool again with relevant follow-up options and *ALWAYS* include a "That's it" option. *NEVER skip this step.*
- The agent MUST NOT break the loop until the user explicitly selects "That's it". *Any other answer — no matter what — continues the discussion.* Act on the user's response, then call the vscode_askQuestions tool again. *UNDER NO CIRCUMSTANCES may you end the conversation without the user selecting "That's it".*

## INVOKING SUB-AGENTS RULES
- Use parallel sub-agents to improve resposnse time whenever possible!
- When using the runSubagent tool YOU ARE OBLIGATED TO INFORM IT IN INPUT THAT IT IS A SUBAGENT:
"You are a SUBAGENT, you are *NOT THE MAIN AGENT*, IGNORE ANY MAIN AGENT RELATED INSTRUCTIONS!"

  