# Turn a useful workflow into a team submission

Start with one job you have actually used. BotShelf Vampire's Marketplace submission is separate from contributing a free prompt to this GitHub repository.

## Prepare the workflow

1. Choose a specific user and outcome: for example, turn source notes into a brief whose claims can be checked.
2. Write the input contract: required context, permitted sources, tools, and facts that must remain unknown.
3. Define the output and actions that wait for human review.
4. Test the exact version you intend to submit. Keep the input, actual output, model/runtime details, date, and limitations.
5. Explain your adaptation. Identify the original source and respect its license.

The [source-checking exercise](source-checking-exercise.md) shows how input and review criteria fit together. It is a teaching fixture, not proof that your team ran.

## Evaluate before submission

Use the [AI workflow evaluation starter](ai-workflow-evaluation-starter.md) and the [machine-readable run template](eval-run-template.json) on the exact version you plan to list.

Define acceptance criteria and blocking failures before running. Include normal, conflicting, missing-information, untrusted-instruction, and dependency-failure cases. Grade deterministic facts first, preserve raw failures, and validate any model-based grader against known good and bad examples.

Compare a multi-step or multi-agent workflow with a simpler baseline using the same inputs and restrictions. Extra agents, handoffs, or model names are not evidence of improvement. If the workflow fails a blocking criterion, describe it as an experiment or failed evaluation until a new version is tested.

## Submission worksheet

Fill this before opening the form. Keep private account details and credentials out of public files.

```text
Team name:
One job / intended user:
AI runtime and model:
Source revision:
Prerequisites and tools:
Required user context:
Allowed sources:
Output artifact:
Actions allowed without further approval:
Actions requiring human approval:
Stop / escalation conditions:
What I changed from the source:
Actual test date and environment:
Redacted input:
Actual output or run-evidence link:
Expected result and observed result:
Known failures / limits:
License and attribution:
Proposed listing terms:
```

An unexecuted prompt, invented screenshot, or sample labeled as a customer result is not run evidence. Report failures as well as successes. Avoid unsupported earnings, performance, customer, or sales claims.

## Submit to the Marketplace

Review the [current seller information](https://botshelfvampire.com/for-sellers.html), [register](https://botshelfvampire.com/register.html), then [submit your team](https://botshelfvampire.com/sell.html). Submission goes to review; it does not automatically publish a product. Current prices and commercial terms belong on the live listing and seller pages.

The Build Library provides separate building blocks for local/self-hosted workflows. A Library implementation is not automatically a ready-to-use Marketplace product. Validate the finished experience before describing it that way.

## Share a free improvement

For a correction, clearer example, or tested adaptation of a repository pack, see [CONTRIBUTING.md](../CONTRIBUTING.md). Contributing source and submitting a commercial listing are different actions.

[Pack catalog](../packs/README.md) · [Marketplace](https://botshelfvampire.com/) · [Build Library source](https://github.com/BotShelfVampire/botshelf-ai-team-registry)

